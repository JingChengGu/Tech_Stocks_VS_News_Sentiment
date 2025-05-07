import psycopg2
import csv
import os
from dotenv import load_dotenv


load_dotenv()
hostname = os.getenv('HOST_NAME') 
database = os.getenv('DATABASE') 
username = os.getenv('USERNAME') 
pwd = os.getenv('PASSWORD') 
port_id = os.getenv('PORT_ID') 
conn = None
cur = None


try:
    conn = psycopg2.connect(
                host = hostname,
                dbname = database,
                user = username,
                password = pwd,
                port = port_id)

    cur = conn.cursor()

    stock_file_path = "assets/stock_prices.csv"
    cur.execute('DROP TABLE IF EXISTS stock_prices_data')

    create_script = '''CREATE TABLE IF NOT EXISTS stock_prices_data(
                            stock     varchar(40) NOT NULL,
                            date      DATE,
                            open      float,
                            high      float,
                            low       float,
                            close     float,
                            volume    float,
                            PRIMARY KEY (stock, date))'''
    cur.execute(create_script)
    conn.commit()


    with open(stock_file_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header if needed
        data = [tuple(row) for row in reader]

    insert_script = 'INSERT INTO stock_prices_data (stock, date, open, high, low, close, volume) VALUES(%s, %s, %s, %s, %s, %s, %s)'
    insert_values = data

    for value in insert_values:
        cur.execute(insert_script, value)

    conn.commit()
    print("stock price data successfully imported!")


    news_csv_path = "assets/news_data.csv"

    # Drop and create second table
    cur.execute('DROP TABLE IF EXISTS news_data')
    create_news_table = '''CREATE TABLE IF NOT EXISTS news_data(
                                stock      VARCHAR(50),
                                date        DATE,
                                source      VARCHAR(100),
                                title       TEXT,
                                description TEXT,
                                url         TEXT,
                                content     TEXT,
                                text        TEXT,
                                sentiment   FLOAT
                                )'''
    cur.execute(create_news_table)
    conn.commit()

    # Load and insert CSV for news_data
    with open(news_csv_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        news_data = [tuple(row) for row in reader]

    insert_news = '''INSERT INTO news_data 
        (stock, date, source, title, description, url, content, text, sentiment) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''

    for row in news_data:
        cur.execute(insert_news, row)

    conn.commit()
    print("Second table 'news_data' imported!")

    # sentiment csv push to postgres

    sentiment_csv_path = "assets/news_sentiment.csv"
    cur.execute('DROP TABLE IF EXISTS sentiment_data')

    create_script = '''
        CREATE TABLE IF NOT EXISTS sentiment_data (
            stock          VARCHAR(50),
            date            DATE,
            article_count   INTEGER,
            avg_sentiment   FLOAT
        )
    '''
    cur.execute(create_script)
    conn.commit()

    with open(sentiment_csv_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        data = [tuple(row) for row in reader]

    insert_script = '''
        INSERT INTO sentiment_data (stock, date, article_count, avg_sentiment)
        VALUES (%s, %s, %s, %s)
    '''

    for row in data:
        cur.execute(insert_script, row)
    
    conn.commit()
    print("Third table 'sentiment_data' successfully imported!")


except Exception as error:
    print(error)
finally:
    if cur is not None:
        cur.close()
    if conn is not None:
        conn.close()