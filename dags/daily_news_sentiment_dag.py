from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

from datetime import datetime, timedelta
import pandas as pd
import requests
import os
import re
import time
from dotenv import load_dotenv
from alpha_vantage.timeseries import TimeSeries

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

# ========================
# ENVIRONMENT & CONSTANTS
# ========================

load_dotenv()

#NEWS_API_KEY = os.getenv('NEWS_API_KEY')
#ALPHA_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

NEWS_API_KEY="ed97359fd5f145c393ca0e0f2683a396"
ALPHA_API_KEY="7MH8BBDFTW6MDMFJ"


if not ALPHA_API_KEY:
        raise ValueError("API key is missing. Set the Alpha_Vantage_API_KEY environment variable in the .env file.")

POSTGRES_CONN_ID = 'postgres_default'
tickers = ["Apple", "Google", "Microsoft", "Amazon", "Meta", "Nvidia", "Tesla", "Netflix", "AMD", "Palantir"]
ticker_map = {
    "AAPL": "Apple", "GOOG": "Google", "MSFT": "Microsoft", "AMZN": "Amazon",
    "META": "Meta", "NVDA": "Nvidia", "TSLA": "Tesla", "NFLX": "Netflix",
    "AMD": "AMD", "PLTR": "Palantir"
}

# ===========================
# FUNCTION: Fetch Stock Data
# ===========================

def fetch_stock_prices(**context):
    ts = TimeSeries(key=ALPHA_API_KEY, output_format='pandas')
    all_data = []
    target_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')

    for ticker_code, company_name in ticker_map.items():
        try:
            df, _ = ts.get_daily(symbol=ticker_code, outputsize='compact')
            df.reset_index(inplace=True)
            df['date'] = df['date'].astype(str)
            df = df[df['date'] == target_date]
            df['stock'] = company_name  # Renamed column from 'ticker' to 'stock'
            all_data.append(df)
        except Exception as e:
            print(f"Error fetching {ticker_code}: {e}")

    if not all_data:
        raise ValueError("No stock data found for previous day.")

    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df = combined_df[['stock', 'date', '1. open', '2. high', '3. low', '4. close', '5. volume']]
    combined_df.columns = ['stock', 'date', 'open', 'high', 'low', 'close', 'volume']  # Renamed 'ticker' to 'stock'

    context['ti'].xcom_push(key='stock_df', value=combined_df.to_json())

    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    engine = pg_hook.get_sqlalchemy_engine()

    with engine.begin() as conn:
        for stock in combined_df['stock'].unique():  # Changed 'ticker' to 'stock'
            conn.execute(
                "DELETE FROM stock_prices_data WHERE stock = %s AND date = %s",
                (stock, target_date)
            )

    combined_df.to_sql("stock_prices_data", con=engine, if_exists="append", index=False)

# =============================
# FUNCTION: Fetch News & Sentiment
# =============================

def fetch_news_and_sentiments(**context):
    from_date = to_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    base_url = "https://newsapi.org/v2/everything?"
    all_articles = []

    for ticker in tickers:
        params = {
            "q": f'"{ticker}"',
            "searchIn": "title",
            "from": from_date,
            "to": to_date,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": 10,
            "apiKey": NEWS_API_KEY
        }
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            articles = response.json().get("articles", [])
            for article in articles:
                article['stock'] = ticker  
                article['date'] = article.get('publishedAt', '')[:10]
                all_articles.append(article)
            time.sleep(1.1)
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")

    news_df = pd.DataFrame(all_articles)
    if news_df.empty:
        raise ValueError("No news data pulled.")

    fruit_keywords = ['fruit', 'juice', 'pie', 'orchard', 'cider', 'farming', 'produce']
    def is_apple_company(row):
        text = (str(row['title']) + ' ' + str(row['description'])).lower()
        return not any(re.search(rf'\b{kw}\b', text) for kw in fruit_keywords)

    news_df = pd.concat([
        news_df[news_df['stock'] == 'Apple'].loc[news_df[news_df['stock'] == 'Apple'].apply(is_apple_company, axis=1)],
        news_df[news_df['stock'] != 'Apple']
    ], ignore_index=True)

    news_df['source'] = news_df['source'].apply(lambda x: x.get('name') if isinstance(x, dict) else None)
    news_df = news_df[['stock', 'date', 'source', 'title', 'description', 'url', 'content']]  # Changed 'ticker' to 'stock'
    news_df.dropna(subset=['description'], inplace=True)
    news_df['text'] = news_df['title'].fillna('') + ' ' + news_df['description'].fillna('')

    tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")
    model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")
    model.cpu()

    def get_score(text):
        try:
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.cpu() for k, v in inputs.items()}
            with torch.no_grad():
                logits = model(**inputs).logits
                probs = torch.softmax(logits, dim=1).squeeze()
                return probs[0].item() * 1 + probs[1].item() * -1
        except:
            return None

    news_df['sentiment'] = news_df['text'].apply(get_score)

    sentiment_summary = news_df.groupby(['stock', 'date']).agg(  # Changed 'ticker' to 'stock'
        article_count=('sentiment', 'count'),
        avg_sentiment=('sentiment', 'mean')
    ).reset_index()
    sentiment_summary['avg_sentiment'] = sentiment_summary['avg_sentiment'].round(3)

    pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    engine = pg_hook.get_sqlalchemy_engine()

    with engine.begin() as conn:
        for stock in news_df['stock'].unique(): 
            conn.execute(
                "DELETE FROM news_data WHERE stock = %s AND date = %s",
                (stock, from_date)
            )
            conn.execute(
                "DELETE FROM sentiment_data WHERE stock = %s AND date = %s",
                (stock, from_date)
            )

    news_df.to_sql("news_data", con=engine, if_exists="append", index=False)
    sentiment_summary.to_sql("sentiment_data", con=engine, if_exists="append", index=False)
    # Log number of rows inserted into both tables
    print(f"Inserted {len(news_df)} rows into news_data for Apple on {from_date}")
    print(f"Inserted {len(sentiment_summary)} rows into sentiment_data for Apple on {from_date}")

# =====================
# DEFAULT ARGS & DAG
# =====================

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="daily_stock_news_and_sentiment_dag",
    default_args=default_args,
    description="Fetch daily stock prices and news sentiment",
    #schedule=None,
    schedule = '30 0 * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["stocks", "news", "sentiment"],
) as dag:

    fetch_stock_task = PythonOperator(
        task_id="fetch_stock_prices",
        python_callable=fetch_stock_prices,
    )

    fetch_news_task = PythonOperator(
        task_id="fetch_news_and_sentiments",
        python_callable=fetch_news_and_sentiments,
    )

    fetch_stock_task >> fetch_news_task
