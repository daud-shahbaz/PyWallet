# personal-finance-tracker

A simple command-line tool to record and monitor your daily spending.

![MENU](ss/menu.jpg)

## Core Features
- **Add Expense:** Enter the amount, category, date, and an optional note.

![Add Expense](ss/add.jpg)

- **View Expenses:** Display all stored expenses in a clean list.  

![Add Expense](ss/view.jpg)

- **Show Statistics:** View basic spending stats like totals and summaries. 

![Add Expense](ss/stats.jpg) 

- **Exit:** Saves everything to your JSON file before closing.

Expenses are stored in a JSON file using four main fields (`amount`, `category`, `date`, `note`) and handled through the project’s core Python methods.

---

## New Features (Phase 2)
- **Monthly Spending:** Automatically groups and totals expenses by month.

![Monthly Chart](charts/monthly.png)

- **Category Breakdown:** Shows how much you’ve spent in each category.

![Category Chart](charts/category.png)  

- **Expenses Over Time:** Tracks your spending trend across dates for simple time-based analysis.  

![Daily Chart](charts/daily.png)


