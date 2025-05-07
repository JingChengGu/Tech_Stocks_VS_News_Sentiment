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

csv_file_path = "assets/stock_prices.csv"
try:
    conn = psycopg2.connect(
                host = hostname,
                dbname = database,
                user = username,
                password = pwd,
                port = port_id)

    cur = conn.cursor()

    cur.execute('DROP TABLE IF EXISTS stock_prices')

    create_script = '''CREATE TABLE IF NOT EXISTS stock_prices(
                            stock     varchar(40) NOT NULL,
                            date      TIMESTAMP,
                            open      float,
                            high      float,
                            low       float,
                            close     float,
                            volume    float,
                            PRIMARY KEY (stock, date))'''
    cur.execute(create_script)
    conn.commit()


    with open(csv_file_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header if needed
        data = [tuple(row) for row in reader]

    insert_script = 'INSERT INTO stock_prices (stock, date, open, high, low, close, volume) VALUES(%s, %s, %s, %s, %s, %s, %s)'
    insert_values = data

    for value in insert_values:
        cur.execute(insert_script, value)

    conn.commit()
    print("CSV data successfully imported!")

except Exception as error:
    print(error)
finally:
    if cur is not None:
        cur.close()
    if conn is not None:
        conn.close()