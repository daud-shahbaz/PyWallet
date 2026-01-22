# PyWallet - Money Manager

Modern, secure personal finance tracking with machine learning insights.

## Features


### Core Features
- **Transaction Management**: Add, categorize, and track all income and expenses
- **Budget Tracking**: Set budgets by category with real-time monitoring
- **Budget Alerts**: Get warnings at 80% and critical alerts at 100%+
- **Financial Analysis**: Daily, monthly, and category summaries with trends
- **Secure Storage**: Encrypted data with auto-rotating backups

### Smart Budget Features
- **Auto-Budget Generator**: Multiple strategies (50/30/20, Conservative, Custom)
- **Surplus Income Optimizer**: Smart recommendations for extra income
- **Budget vs Actual Comparison**: Visual charts showing spending vs budget
- **Category Utilization Tracking**: Monitor how much of each budget is used

### ML & Intelligence Features
- **Spending Predictions**: Forecast next month's expenses by category
- **Anomaly Detection**: Identify unusual transactions automatically
- **Smart Categorization**: NLP-based automatic category assignment
- **Behavior Clustering**: Analyze and understand spending patterns
- **Financial Advisor**: Personalized recommendations and insights

### Security & Privacy
- Argon2 password hashing
- Fernet encryption for sensitive data
- User authentication with session management
- Auto-rotating encrypted backups
- Local-only storage (no cloud)
- Auto-logout feature

## Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/daud-shahbaz/PyWallet.git
cd pywallet

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app/PyWallet.py
```

### First Run
The app will automatically create a `pywallet/data/` directory to store your financial data locally. Create an account when you first open the app.

### System Requirements
- Python 3.8+
- Windows/Mac/Linux

App opens at: http://localhost:8501

## Project Structure
```
pywallet/           - Backend package (data, analytics, ML)
  ├── config.py     - Central configuration
  ├── modules/      - Data manager, analytics
  ├── ml_models/    - 5 ML algorithms (Predictions, Anomalies, Classifier, Clustering, Coach)
  └── security/     - Encryption, auth

app/                - Frontend (5 Streamlit pages)
  ├── PyWallet.py   - Main entry point with authentication
  └── pages/        
      ├── 01_Dashboard.py      - Overview and key metrics
      ├── 02_Transactions.py   - Income/expenses, budget tracking & alerts
      ├── 03_Analytics.py      - Trends, insights, and analysis
      ├── 04_Forecasts.py      - ML predictions, anomalies, patterns
      └── 05_Settings.py       - Configuration and preferences

components/         - Reusable UI components
  ├── cards.py      - Card components
  ├── charts.py     - Chart components
  └── forms.py      - Form components

tests/              - Unit tests
requirements.txt    - Dependencies
```

## Features Overview

| Feature | Details |
|---------|---------|
| Transaction Management | Add, edit, delete, categorize income/expenses |
| Budget Tracking | Set limits, real-time monitoring, alerts |
| Budget Alerts | Warnings at 80%, critical at 100%+ |
| Analytics & Trends | Monthly, category, month-over-month analysis |
| Forecasting | Predict next month's spending |
| Anomaly Detection | Identify unusual transactions |
| Data Security | Encryption, hashing, backups |
| Import/Export | CSV & JSON support |
| Web Interface | 5-page Streamlit app with authentication |

## Tech Stack
- **Web Interface**: Streamlit 1.32.2
- **Data Handling**: Pandas, NumPy
- **Predictions**: Scikit-learn
- **Security**: Cryptography, Argon2
- **Visualizations**: Plotly, Matplotlib

### Running Locally

#### Terminal
```bash
streamlit run app/PyWallet.py
```

### Streamlit Cloud
1. Push to GitHub
2. Visit https://share.streamlit.io
3. Deploy from GitHub repo

Made by Daud | Thank you for using PyWallet!

