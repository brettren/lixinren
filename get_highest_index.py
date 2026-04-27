import requests
import csv
import time
from datetime import datetime, timedelta

import config

# Configuration
TOKEN = config.token
API_URL = "https://open.lixinger.com/api/cn/fund/net-value-of-dividend-reinvestment"
INPUT_CSV = "qdIIFunds/all_qdII_funds_largest_drawdown_fs.csv"
OUTPUT_CSV = "qdIIFunds/all_qdII_funds_highest_index_fs.csv"

def get_stock_codes_from_csv(csv_path):
    """Extract stock codes from the first column of the CSV"""
    stock_codes = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0]:
                # Extract stock code (before the comma)
                stock_code = row[0].split(',')[0].strip()
                stock_codes.append(stock_code)
    return stock_codes

def get_highest_net_value(stock_code, token):
    """Call API to get historical net values and return the highest value"""
    # Set date range - get data from 10 years ago to today
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=3650)).strftime("%Y-%m-%d")

    payload = {
        "token": token,
        "stockCode": stock_code,
        "startDate": start_date,
        "endDate": end_date
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()

        if data.get("code") == 1 and data.get("data"):
            net_values = [item["netValue"] for item in data["data"] if item.get("netValue") is not None]
            if net_values:
                return max(net_values)
            else:
                print(f"No net values found for {stock_code}")
                return None
        else:
            print(f"API error for {stock_code}: {data.get('message', 'Unknown error')}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Request failed for {stock_code}: {e}")
        return None
    except Exception as e:
        print(f"Error processing {stock_code}: {e}")
        return None

def main():
    print("Reading stock codes from CSV...")
    stock_codes = get_stock_codes_from_csv(INPUT_CSV)
    print(f"Found {len(stock_codes)} stock codes")

    results = []
    total = len(stock_codes)

    for idx, stock_code in enumerate(stock_codes, 1):
        print(f"Processing {idx}/{total}: {stock_code}...", end=" ")

        highest_index = get_highest_net_value(stock_code, TOKEN)

        if highest_index is not None:
            results.append((stock_code, highest_index))
            print(f"Highest: {highest_index}")
        else:
            results.append((stock_code, "N/A"))
            print("Failed")

        # Add a small delay to avoid overwhelming the API
        if idx < total:
            time.sleep(0.5)

    # Write results to CSV
    print(f"\nWriting results to {OUTPUT_CSV}...")
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['stockcode', 'highest_index'])
        writer.writerows(results)

    print(f"Done! Results saved to {OUTPUT_CSV}")
    print(f"Successfully processed: {sum(1 for _, v in results if v != 'N/A')}/{total}")

if __name__ == "__main__":
    main()
