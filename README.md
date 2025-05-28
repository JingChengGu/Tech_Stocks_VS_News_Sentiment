# Tech Stocks VS News Sentiment Dashboard

🔗 **[Explore the Dashboard →](https://public.tableau.com/views/stocks_and_news/Dashboard1?:language=en-US&publish=yes&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)**  
*A live Tableau dashboard tracking daily sentiment and stock performance*

## 📊 Overview

Lately, it feels like stock prices move more on headlines than fundamentals. I wanted to test that idea—how much influence does daily news really have on market movement? This project pulls stock and news data for major tech companies, runs sentiment analysis using FinBERT, and tracks the results in a Tableau dashboard. The goal: measure the connection between media tone and stock price behavior over time. 

This end-to-end data pipeline tracks financial news and daily stock price movements for ten major tech companies. 
It integrates real-time data ingestion, sentiment analysis using a fine-tuned transformer model, and visualization through Tableau. The project is fully containerized with Docker and automated with Apache Airflow, enabling daily insights into how news sentiments and media may impact stock price movements.

---

## ⛓️ Architecture & Tech Stack

### Architecture

- **ETL Pipeline** orchestrated via **Apache Airflow** (Dockerized)
- **Two Data APIs**:
  - [Alpha Vantage](https://www.alphavantage.co/) for stock prices
  - [NewsAPI](https://newsapi.org/) for financial news
- **Sentiment Analysis**: FinBERT via HuggingFace Transformers
- **Database**: PostgreSQL (Dockerized)
- **Dashboard**: Tableau connected to live PostgreSQL database

### Tech Stack

| category      | Technologies Used           |
|---------------|-----------------------------|
| Workflow Mgnt | Apache Airflow (Dockerized) |
| Data Storage  | PostgreSQL (Dockerized)     |
| API Data Pull | Alpha Vantage, NewsAPI      |
| NLP Model      | HuggingFace Transformers, FinBERT, PyTorch      |
| Backend Tools  | Python, Pandas, SQLAlchemy, Requests, dotenv    |
| Deployment     | Docker Compose                                  |
| Dashboarding   | Tableau    |

---

## 🧾 Data

### Sources

- **Stock Prices**: Daily OHLCV data from Alpha Vantage
- **News Articles**: Headlines and descriptions from NewsAPI

### Data Tables

- `stock_prices_data`: Stock open, high, low, close, volume
- `news_data`: Title, source, description, date, company ticker
- `sentiment_data`: Aggregated daily sentiment scores by ticker

*Note: Apple-related articles are filtered to remove fruit-related noise using keyword heuristics. This helps to focus on only Apple stock related news.*

---

## 🤖 Model

I initially experimented with TextBlob for sentiment analysis due to its simplicity and ease of integration. However, I quickly realized that its general-purpose sentiment scoring was insufficient for the nuances of financial news. Many articles that were contextually neutral or even optimistic in a financial sense were misclassified due to TextBlob’s lack of domain-specific understanding.

To improve the quality of sentiment scoring, I moved to [FinBERT](https://huggingface.co/yiyanghkust/finbert-tone), a BERT-based model fine-tuned on financial text. FinBERT is better suited for interpreting language patterns found in news headlines an dmarket commentary. This shift allowed the model to more accurately reflect the sentiment tone relevant to market behavior.

**Scoring Function:**

```python
Sentiment Score = P(positive) - P(negative)
```

Each article is scored individually. Sentiment scores are then averaged per company per day to produce a daily sentiment metric.

---

## 📈 Results

The Tableau dashboard offers:

- **Stock vs. Sentiment Time Series**: Compare daily closing prices with sentiment trends
- **Company Filters**: Focus on individual tickers
- **Event Detection**: Spot sentiment spikes tied to price moves

The dashboard connects live to the Dockerized PostgreSQL instance on `localhost:5433`.

---

## 🤔 Limitations

The current version of news article sentiment analysis does not purely focus on financial market related content, as news articles range from many different categories related to the tickers (new releases, CEO news, misaligned content). 

In future work, I plan to narrow down the news content that are injected into sentiment analysis to be more financially focused to better correlate to stock movements.

---

## 🔮 Future Work

- Compare **multiple NLP models** for sentiment analysis
- Develop **trading backtest strategies** using historical sentiment
- Build a **web frontend** with Streamlit or React
- Explore **cloud deployment** and Airflow scalability

## Final Thoughts
