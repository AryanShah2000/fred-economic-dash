import json
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Your FRED API key
api_key = os.getenv('FRED_API_KEY')

if not api_key:
    print("Please set your FRED_API_KEY in the .env file")
    exit(1)

# Define all the tickers and their groups
default_tickers = {
    "Automotive": [
        "AUINSA", "TOTALSA", "ALTSALES", "IPG33611S", "CAPUTLG33611S"
    ],
    "Commercial Auto Insurance": [
        "PCU9241269241263"
    ],
    "Construction": [
        "HOUST", "HSN1F", "MORTAGE30US", "IPG321S"
    ],
    "CPG_Food and Paper": [
        "IPG311S", "IPG322S"
    ],
    "Industrial Production": [
        "TRUCKD11", "INDPRO", "IPMAN", "IPG311A2S", "IPG333S", "IPG322S", "IPG3361T3S", "MCUMFN"
    ],
    "Personal Consumption Trends": [
        "DFXARX1Q020SBEA", "A136RC1Q027SBEA"
    ],
    "Retail": [
        "RSAFS"
    ],
    "Retail Inventories": [
        "RETAILIRSA", "RETAILSMSA", "RETAILIMSA"
    ]
}

def get_series_info(series_id):
    """Get series information from FRED API"""
    url = "https://api.stlouisfed.org/fred/series"
    params = {
        'series_id': series_id,
        'api_key': api_key,
        'file_type': 'json'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'seriess' in data and len(data['seriess']) > 0:
            return data['seriess'][0].get('title', series_id)
        else:
            return series_id
    except Exception as e:
        print(f"Error fetching info for {series_id}: {e}")
        return series_id

# Build the data structure
saved_metrics = []
saved_metrics_names = {}
saved_metrics_groups = {}

print("Fetching series information from FRED API...")

for group_name, tickers in default_tickers.items():
    print(f"\nProcessing group: {group_name}")
    
    for ticker in tickers:
        print(f"  Fetching info for {ticker}...")
        
        # Add to saved metrics list
        saved_metrics.append(ticker)
        
        # Get full name from FRED API
        full_name = get_series_info(ticker)
        saved_metrics_names[ticker] = full_name
        
        # Assign group
        saved_metrics_groups[ticker] = group_name
        
        print(f"    {ticker}: {full_name}")

# Create the final data structure
data = {
    'saved_metrics': saved_metrics,
    'saved_metrics_names': saved_metrics_names,
    'saved_metrics_groups': saved_metrics_groups
}

# Save to file
with open('saved_metrics.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"\n✅ Successfully added {len(saved_metrics)} metrics across {len(default_tickers)} groups!")
print(f"📁 Data saved to saved_metrics.json")

# Print summary
print(f"\n📊 Summary:")
for group_name, tickers in default_tickers.items():
    print(f"  {group_name}: {len(tickers)} metrics")