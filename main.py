import requests
import datetime as dt
from twilio.rest import Client
import os


STOCK = "TSLA" #any stock you'd like track
COMPANY_NAME = "Tesla Inc"

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

#please register with Alphavantage and Newsapi to obtain your own api keys
STOCK_API_KEY = os.environ.get("STOCK_API_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

#please register with Twilio to obtain your own Twilio US number, account_sid and auth_token
TWILIO_US_NUMBER = os.environ.get("TWILIO_US_NUMBER")
ACCOUNT_SID = os.environ.get("ACCOUNT_SID")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")

YOUR_PHONE_NUMBER = os.environ.get("YOUR_PHONE_NUMBER")  #the phone number specified here will receive all notifications


stock_params = {
    "function": "TIME_SERIES_DAILY",
    "symbol": STOCK,
    "apikey": STOCK_API_KEY,
}

response_stocks = requests.get(url=STOCK_ENDPOINT, params=stock_params)
response_stocks.raise_for_status()
stock_data = response_stocks.json()

print(stock_data)


yesterday = dt.datetime.now() - dt.timedelta(days=1)
day_before_yesterday = dt.datetime.now() - dt.timedelta(days=2)

yesterday_formatted = yesterday.strftime("%Y-%m-%d")
day_before_yesterday_formatted = day_before_yesterday.strftime("%Y-%m-%d")

#stock exchanges do not work on weekends which is why we may not be able to retrieve the data on closing prices of the stock on Saturday and Sunday
try:
    yesterday_price = float(stock_data["Time Series (Daily)"][yesterday_formatted]["4. close"])
    the_day_before_yesterday_price = float(stock_data["Time Series (Daily)"][day_before_yesterday_formatted]["4. close"])

except KeyError:
    if dt.datetime.now().strftime("%A") == "Monday":
        yesterday = dt.datetime.now() - dt.timedelta(days=3)
        day_before_yesterday = dt.datetime.now() - dt.timedelta(days=4)

    elif dt.datetime.now().strftime("%A") == "Tuesday":
        yesterday = dt.datetime.now() - dt.timedelta(days=1)
        day_before_yesterday = dt.datetime.now() - dt.timedelta(days=4)
finally:
    yesterday_formatted = yesterday.strftime("%Y-%m-%d")
    day_before_yesterday_formatted = day_before_yesterday.strftime("%Y-%m-%d")

    yesterday_price = float(stock_data["Time Series (Daily)"][yesterday_formatted]["4. close"])
    the_day_before_yesterday_price = float(stock_data["Time Series (Daily)"][day_before_yesterday_formatted]["4. close"])

    change_in_price_percent = (yesterday_price - the_day_before_yesterday_price) / the_day_before_yesterday_price * 100

parameters_news = {
    "apiKey": NEWS_API_KEY,
    "q": COMPANY_NAME,
    "from": day_before_yesterday_formatted,
    "sortBy": "relevancy",
    "pageSize": 3
    }

response_news = requests.get(url=NEWS_ENDPOINT, params=parameters_news)
response_news.raise_for_status()
news_data = response_news.json()["articles"]


# When STOCK price increase/decreases by 5% between yesterday and the day before yesterday
# we send a message (via Twilio) with the percentage change and each news article's title and description to (our) phone number.

to_be_sent = ""

if change_in_price_percent >= 5 or change_in_price_percent <= -5:
    for _ in range(0, 3):
        if yesterday_price > the_day_before_yesterday_price:
            message_text = f"{STOCK}: 🔺{int(round(change_in_price_percent, 0))}%\nHeadline: {news_data[_]['description']}\nBrief: {news_data[_]['content']}\n"

        elif yesterday_price < the_day_before_yesterday_price:
            message_text = f"{STOCK}: 🔻{int(round(change_in_price_percent, 0))}%\nHeadline: {news_data[_]['description']}\nBrief: {news_data[_]['content']}\n"

        to_be_sent += message_text

    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    message = client.messages \
        .create(
        body=to_be_sent,
        from_=TWILIO_US_NUMBER,
        to=YOUR_PHONE_NUMBER
    )

    print(message.status)



