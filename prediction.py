import xlrd
import pandas as pd
import yfinance as yf
import streamlit as st
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime, timedelta
from newsapi import NewsApiClient
import seaborn as sns


companies = {}
xls = xlrd.open_workbook("cname.xls")
sh = xls.sheet_by_index(0)
for i in range(505):
    cell_value_class = sh.cell(i, 0).value
    cell_value_id = sh.cell(i, 1).value
    companies[cell_value_class] = cell_value_id

def get_current_stock_price(stock_symbol):
    stock = yf.Ticker(stock_symbol)
    current_price = stock.history(period="1d")['Close'].iloc[-1]
    return current_price

def predict_stock_price(stock_symbol, days=1, intraday=False):
    if intraday:
        data = yf.download(stock_symbol, period="1d", interval="1m")
    else:
        data = yf.download(stock_symbol, period=f"{days}d")
    data['Date'] = data.index
    data['Price'] = data['Close']

    model = ARIMA(data['Price'], order=(5,1,0))  # arima
    model_fit = model.fit()

    # Prdict stock price
    next_days = model_fit.forecast(steps=days)

    last_date = data['Date'].iloc[-1]
    future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, days + 1)]

    next_days_prices = list(zip(future_dates, next_days))

    return data, next_days_prices

def get_stock_news(stock_symbol, api_key):
    newsapi = NewsApiClient(api_key)
    from_date = (datetime.today() - timedelta(7)).strftime('%Y-%m-%d')
    to_date = datetime.today().strftime('%Y-%m-%d')
    
    news = newsapi.get_everything(
        q=stock_symbol,
        from_param=from_date,
        to=to_date,
        language='en',
    )
    return news

def data_analysis():
    company = st.sidebar.selectbox("Companies", list(companies.keys()), 0)
    stock_symbol = companies[company]
    data = yf.download(tickers=stock_symbol, period='3650d', interval='1d')

    st.header(f'Data Analysis for {company}')

    st.subheader("Basic Data Statistics:")
    st.write(f"Total Data Points: {data.shape[0]}")
    st.write(f"Minimum Price: ${data['Close'].min():.2f}")
    st.write(f"Maximum Price: ${data['Close'].max():.2f}")
    st.write(f"Average Price: ${data['Close'].mean():.2f}")
    st.write(f"Standard Deviation: ${data['Close'].std():.2f}")

    st.subheader("Price Chart:")
    st.line_chart(data['Close'], use_container_width=True)

    st.subheader("Price Distribution:")
    fig, ax = plt.subplots()
    sns.histplot(data['Close'], bins=20, kde=True)
    st.pyplot(fig)

def main():
    st.title("TradeTalk")
    st.sidebar.subheader("Company Selection")

    choice = st.sidebar.radio("Menu", ["Home", "Prediction", "News", "Data Analysis", "Manage Portfolio"])

    if choice == "Home":
        st.markdown("Welcome to the Stock Analysis and Price Prediction App.")

    elif choice == "Prediction":
        st.subheader("Stock Price Prediction")
        st.write("Enter the stock symbol to predict its future prices or get the current market price.")
        stock_symbol = st.text_input("Stock Symbol (e.g., AAPL for Apple Inc. or RELIANCE.BO for Reliance Industries)")

        days_to_predict = st.number_input("Number of Days to Predict", 1, 30, 10)
        intraday = st.checkbox("Intraday Prediction (1-minute interval)")

        if st.button("Predict"):
            if stock_symbol:
                data, next_days_prices = predict_stock_price(stock_symbol, days_to_predict, intraday)

                st.write(f"Predicted prices for {stock_symbol} for the next {days_to_predict} days:")
                st.dataframe(pd.DataFrame(next_days_prices, columns=["Date", "Predicted Price"]))

                # Plot the historical prices, predicted prices, and current price
                fig, ax = plt.subplots()
                ax.plot(data['Date'], data['Price'], label="Historical Prices")

                for next_day, next_day_price in next_days_prices:
                    ax.axvline(next_day, color='r', linestyle='--', label="Prediction Day")
                    ax.axhline(next_day_price, linestyle='--', label="Predicted Price")

                current_price = get_current_stock_price(stock_symbol)
                st.write(f"Current market price for {stock_symbol}: ${current_price:.2f}")
                ax.axhline(current_price, color='g', linestyle='--', label="Current Price")

                ax.set_xlabel("Date")
                ax.set_ylabel("Price (USD)")
                ax.set_title(f"{stock_symbol} Stock Price Comparison")
                ax.legend()
                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: pd.to_datetime(x).strftime('%Y-%m-%d')))
                st.pyplot(fig)
            else:
                st.warning("Please enter a stock symbol.")

        if st.button("Get Current Price"):
            if stock_symbol:
                current_price = get_current_stock_price(stock_symbol)
                st.write(f"Current market price for {stock_symbol}: ${current_price:.2f}")
            else:
                st.warning("Please enter a stock symbol.")

    elif choice == "News":
        st.subheader("Stock News")
        st.write("Enter the stock symbol to get recent news articles related to the stock.")
        stock_symbol = st.text_input("Stock Symbol (e.g., AAPL for Apple Inc. or RELIANCE.BO for Reliance Industries)")

        if st.button("Get News"):
            if stock_symbol:
                api_key = 'fcf0a214233d4fa3a7a60c5b1b1d68ab'  
                news = get_stock_news(stock_symbol, api_key)
                if 'articles' in news and len(news['articles']) > 0:
                    st.write(f"Recent news articles related to {stock_symbol}:")
                    for article in news['articles']:
                        st.write(article['title'])
                        st.write(article['description'])
                        st.write(article['url'])
                        st.image(article['urlToImage'], use_column_width=True)
                else:
                    st.warning("No recent news available for this stock.")
            else:
                st.warning("Please enter a stock symbol.")

    elif choice == "Data Analysis":
        data_analysis()

    elif choice == "Manage Portfolio":
        st.subheader("Virtual Stock Portfolio")
        st.write("Manage your virtual stock portfolio")

        # Not working properly
        portfolio = {}

        def calculate_portfolio_value(portfolio):
            total_value = 0
            for symbol, data in portfolio.items():
                stock = yf.Ticker(symbol)
                current_price = stock.history(period="1d")['Close'].iloc[-1]
                total_value += current_price * data['Quantity']
            return total_value

        if st.button("Buy Stock"):
            stock_symbol = st.text_input("Stock Symbol (e.g., AAPL for Apple Inc. or RELIANCE.BO for Reliance Industries)")
            quantity = st.number_input("Quantity", 1, 100, 1)
            if stock_symbol:
                if stock_symbol in portfolio:
                    portfolio[stock_symbol]['Quantity'] += quantity
                else:
                    portfolio[stock_symbol] = {'Quantity': quantity}
                st.success(f"Bought {quantity} shares of {stock_symbol}.")

        if st.button("Sell Stock"):
            stock_symbol = st.text_input("Stock Symbol (e.g., AAPL for Apple Inc. or RELIANCE.BO for Reliance Industries)")
            quantity = st.number_input("Quantity", 1, 100, 1)
            if stock_symbol:
                if stock_symbol in portfolio:
                    if portfolio[stock_symbol]['Quantity'] >= quantity:
                        portfolio[stock_symbol]['Quantity'] -= quantity
                        st.success(f"Sold {quantity} shares of {stock_symbol}.")
                    else:
                        st.warning("Not enough shares in the portfolio to sell.")
                else:
                    st.warning(f"You do not own {stock_symbol} in your portfolio.")

        if st.button("View Portfolio"):
            if not portfolio:
                st.warning("Your portfolio is empty.")
            else:
                st.write("Your Virtual Portfolio:")
                st.table(pd.DataFrame.from_dict(portfolio, orient='index').rename(columns={'Quantity': 'Shares'}))

        if st.button("Calculate Portfolio Value"):
            total_value = calculate_portfolio_value(portfolio)
            st.success(f"Total Portfolio Value: ${total_value:.2f}")

        if st.button("Clear Portfolio"):
            portfolio.clear()
            st.success("Cleared your portfolio.")

if __name__ == "__main__":
    main()