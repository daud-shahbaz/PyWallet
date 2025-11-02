import matplotlib.pyplot as plt
from datetime import datetime

# ------------------------------------------------------------
#               PIE CHART — CATEGORY SPENDING
# ------------------------------------------------------------

def plot_category_pie(data):
    category_stats = {}

    for item in data:
        cat = item["category"]
        amt = item["amount"]
        category_stats[cat] = category_stats.get(cat, 0) + amt

    labels = list(category_stats.keys())
    values = list(category_stats.values())

    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct="%1.1f%%")
    plt.title("Expenses by Category")
    plt.tight_layout()
    plt.savefig('charts/category.png')
    plt.show()

# ------------------------------------------------------------
#               BAR CHART — MONTHLY SPENDING
# ------------------------------------------------------------

def plot_monthly_bar(data):
    monthly_stats = {}

    for item in data:
        date_str = item["date"]
        day = datetime.strptime(date_str, "%Y-%m-%d")
        key = f"{day.year}-{day.month:02d}"

        monthly_stats[key] = monthly_stats.get(key, 0) + item["amount"]

    months = list(monthly_stats.keys())
    amounts = list(monthly_stats.values())

    plt.figure(figsize=(8, 5))
    plt.bar(months, amounts)
    plt.xticks(rotation=45)
    plt.title("Monthly Spending")
    plt.xlabel("Month")
    plt.ylabel("Amount")
    plt.tight_layout()
    plt.savefig('charts/monthly.png')
    plt.show()

# ------------------------------------------------------------
#              LINE CHART FOR DAILY SPENDING
# ------------------------------------------------------------

def plot_daily_line(data):
    daily_stats = {}

    for item in data:
        day = datetime.strptime(item["date"], "%Y-%m-%d")
        date_key = day.strftime("%Y-%m-%d")

        daily_stats[date_key] = daily_stats.get(date_key, 0) + item["amount"]

    dates = list(daily_stats.keys())
    amounts = list(daily_stats.values())

    plt.figure(figsize=(8, 5))
    plt.plot(dates, amounts, marker="o")
    plt.xticks(rotation=45)
    plt.title("Daily Spending")
    plt.xlabel("Date")
    plt.ylabel("Amount")
    plt.tight_layout()
    plt.savefig("charts/daily.png")
    plt.show()
