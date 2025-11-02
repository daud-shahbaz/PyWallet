#----------------------------------------------------------------------------
#                          Importing Packages
#----------------------------------------------------------------------------

import json
from datetime import datetime as dt
from visualizations import plot_category_pie, plot_daily_line, plot_monthly_bar

#----------------------------------------------------------------------------
#                          Variable for json file
#----------------------------------------------------------------------------

expenses_path = 'data/expenses.json'

#----------------------------------------------------------------------------
#                        Loading data from json file
#----------------------------------------------------------------------------

def load_data():
    print("Loading expenses...")

    try:
        with open(expenses_path, 'r') as file:
            expenses = json.load(file)
        return expenses
    except FileNotFoundError as e:
        print("File does not exist:", e)
        return []
    except json.JSONDecodeError as e:
        print("JSON Decode Error:", e)
        return []
    
#----------------------------------------------------------------------------
#                            Adding a expense
#----------------------------------------------------------------------------

def add_expense():
    print("Adding expense...")

    loaded = load_data()

    try:
        amount = int(input("Enter the amount:"))
    except ValueError as e:
        print("Enter a valid integer", e)
        return
    
    category = input("Enter category: ")

    try:
        year = int(input("Enter year (YYYY): "))
        month = int(input("Enter month (1-12): "))
        day = int(input("Enter day (1-31): "))
        date = dt(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        print("Invalid dateinput. Please enter valid year, month, and day.")
        return

    note = input("Any notes you would like to add: ")

    expense = {
            "amount": amount,
            "category": category,
            "date":date,
            "note": note
    }
    
    loaded.append(expense)

    with open(expenses_path, 'w') as file:
        json.dump(loaded, file, indent=4)

    print("Expense added successfully")

#----------------------------------------------------------------------------
#                          Viewing all expenses
#----------------------------------------------------------------------------

def view_expense():
    print("Viewing expense...")

    loaded = load_data()

    if not loaded:
        print("No expenses found")
        return

    print(f"{'Sr':<3} | {'Amount':<10} | {'Category':<12} | {'Date':<12} | Note")
    print("-" * 60)

    for i, exp in enumerate(loaded, start=1):
        print(f"{i:<3} | {exp['amount']:<10} | {exp['category']:<12} | {exp['date']:<12} | {exp['note']}")

#----------------------------------------------------------------------------
#                          Showing main statisitcs
#----------------------------------------------------------------------------

def show_stats():
    print("Showing all statisitcs...")

    loaded = load_data()
    
    if not loaded:
        print("No expenses found")
        return
    
    print("==============================================================")
    print("               Overall Statistics of Expenses                ")
    print("==============================================================")
    print("--------------------------------------------------------------")
    print("Total Amount Spent: ", calculate_total(loaded))
    print("--------------------------------------------------------------")
    print("Total Amount Spent by Category:")
    category_data = category_summary(loaded)
    for category, amount in category_data.items():
        print(f"  {category}: {amount}")
    print("--------------------------------------------------------------")
    print("Total Amount Spent per month:")
    monthly_data = monthly_spending(loaded)
    for month, amount in monthly_data.items():
        print(f"  {month}: {amount}")
    print("--------------------------------------------------------------")


#----------------------------------------------------------------------------
#                        Calculating total expenses
#----------------------------------------------------------------------------

def calculate_total(data):
    total_amount = 0
    for i in data:
        total_amount += i['amount']
    return total_amount

#----------------------------------------------------------------------------
#                         Expenses by Category
#----------------------------------------------------------------------------

def category_summary(data):
    category_stats= {}

    for i in data:
        category = i["category"]
        amount = i["amount"]
        category_stats[category] = category_stats.get(category, 0) + amount
    
    return category_stats

#----------------------------------------------------------------------------
#                            Monthly Expenses
#----------------------------------------------------------------------------

def monthly_spending(data):
    monthly_spent = {}

    for i in data:
        ymd = dt.strptime(i["date"], "%Y-%m-%d")

        year = ymd.year
        month = ymd.month

        ym = f"{year}-{month:02d}"

        amount = i["amount"]
        monthly_spent[ym] = monthly_spent.get(ym, 0) + amount

    return monthly_spent

#----------------------------------------------------------------------------
#                             Daily Expenses
#----------------------------------------------------------------------------

def amount_per_day(data):
    daily_spent = {}

    for i in data:
        date = i["date"]
        ymd = dt.strptime(date, "%Y-%m-%d")

        day = ymd.date()

        amount = i["amount"]
        daily_spent[day] = daily_spent.get(day, 0) + amount
    
    sorted_daily = sorted(daily_spent.items())

    dates_list = []
    amounts_list = []

    for day, amount in sorted_daily:
        dates_list.append(day.strftime("%Y-%m-%d"))
        amounts_list.append(amount)

    return dates_list, amounts_list

#----------------------------------------------------------------------------
#                                   MENU
#----------------------------------------------------------------------------

while True:
    print("=========================")
    print("           Menu          ")
    print("=========================")
    print("1. Add Expense")
    print("-------------------------")
    print("2. View Expense")
    print("-------------------------")
    print("3. Show Statistics")
    print("-------------------------")
    print("4. Show and Export charts")
    print("-------------------------")
    print("5. Save and Exit")
    print("-------------------------")
    try:
        choice = int(input("Enter your choice: "))
        match choice:
            case 1:
                add_expense()
            case 2:
                view_expense()
            case 3:
                show_stats()
            case 4:
                data = load_data()
                plot_monthly_bar(data)
                plot_category_pie(data)
                plot_daily_line(data)
            case 5:
                print("Saving and Exiting...")
                break
    except ValueError:
        print("Invalid choice. Enter a number from 1–5")
        continue