# Tech_Stocks_VS_News_Sentiment Dashboard

🔗 **[Explore the Dashboard →](https://public.tableau.com/views/stocks_and_news/Dashboard1?:language=en-US&publish=yes&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)**  
*A live Tableau dashboard tracking daily sentiment and stock performance*

## Overview

Lately, it feels like stock prices move more on headlines than fundamentals. I wanted to test that idea—how much influence does daily news really have on market movement? This project pulls stock and news data for major tech companies, runs sentiment analysis using FinBERT, and tracks the results in a Tableau dashboard. The goal: measure the connection between media tone and stock price behavior over time. 

This end-to-end data pipeline tracks financial news and daily stock price movements for ten major tech companies. 
It integrates real-time data ingestion, sentiment analysis using a fine-tuned transformer model, and visualization through Tableau. The project is fully containerized with Docker and automated with Apache Airflow, enabling daily insights into how news sentiments and media may impact stock price movements.

---


- Build historial database with Alpha Vantage API and NewsAPI for 10 popular tech stocks (Using Python to pull from both API and calculate the daily news sentiment with FinBert)
- Create a Docker container for daily Airflow news data and stock price data pulls and PostgreSQL database to store daily pulled data
- Showcase the PostgreSQL data on Tableau and using Tableau public to showcase the dashboard.
