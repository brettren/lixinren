import requests

# replace YOUR_API_KEY with your Alpha Vantage API key
url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=DAX&apikey=54IJCJL599FUTAW3"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()['Time Series (Daily)']
    # sort the data by date
    sorted_data = sorted(data.items(), key=lambda x: x[0])
    # get the lowest and highest index
    lowest_index = sorted_data[0][1]['4. close']
    highest_index = sorted_data[-1][1]['4. close']
    print(f"Lowest index: {lowest_index}")
    print(f"Highest index: {highest_index}")
else:
    print("Failed to fetch data")
