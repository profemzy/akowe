# Akowe Financial Tracker

Akowe is a financial tracking application built to help with business expense and income management for tax preparation.

## Features

- Import income and expense data from CSV files
- Track and categorize business expenses
- Record client income with project tracking
- Generate financial reports and summaries
- Prepare data for tax season

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```
6. Run the application: `flask run` or `python app.py`

## Usage

1. Access the application at http://localhost:5000
2. Import your existing CSV data through the Import buttons
3. Add new income and expense entries through the web interface
4. View financial summaries on the dashboard

## CSV Import Format

### Income CSV Format
```
date,amount,client,project,invoice
2025-03-21,9040.00,SearchLabs (RAVL),P2025001 - Interac Konek,Invoice #INV-202503-0002 - SearchLabs
```

### Expense CSV Format
```
date,title,amount,category,payment_method,status,vendor
2025-04-12,WD Red Plus 12TB NAS Hard Disk Drive,386.37,hardware,credit_card,pending,Newegg
```