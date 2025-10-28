# FRED Economic Data Explorer 📊

An interactive Streamlit dashboard for exploring economic data from the Federal Reserve Economic Data (FRED) database.

## Features

- 📈 Interactive charts with drawing tools and light/dark mode
- 🎨 Advanced line formatting with color, style, and thickness controls
- 📊 Comprehensive summary table with all saved metrics
- 🏷️ Grouping system for organizing metrics
- 📋 Expandable data tables with CSV export
- 💾 Persistent storage of saved metrics and preferences

## Live Demo

🚀 **[Try the app live on Streamlit Community Cloud](your-app-url-here)**

## Local Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Get a free FRED API key from [here](https://research.stlouisfed.org/docs/api/api_key.html)
4. Copy `.env.example` to `.env` and add your API key
5. Run: `streamlit run app.py`

## Common FRED Series IDs

- `GDP` - Gross Domestic Product
- `UNRATE` - Unemployment Rate
- `CPIAUCSL` - Consumer Price Index
- `FEDFUNDS` - Federal Funds Rate
- `DGS10` - 10-Year Treasury Constant Maturity Rate

## Deployment

This app is deployed on Streamlit Community Cloud. The API key is configured through Streamlit's secrets management.

## Technologies Used

- **Streamlit** - Web application framework
- **Plotly** - Interactive charts and visualizations
- **Pandas** - Data manipulation and analysis
- **FRED API** - Economic data from Federal Reserve

## Data Sources

All economic data is sourced from the [Federal Reserve Economic Data (FRED)](https://fred.stlouisfed.org/) database, which provides reliable, up-to-date economic indicators from various government agencies.