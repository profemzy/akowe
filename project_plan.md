# Akowe Financial Tracker App

## Database Schema

### Income Table
- id: Integer (Primary Key)
- date: Date
- amount: Decimal(10,2)
- client: String
- project: String
- invoice: String
- created_at: Timestamp
- updated_at: Timestamp

### Expense Table
- id: Integer (Primary Key)
- date: Date
- title: String
- amount: Decimal(10,2)
- category: String
- payment_method: Enum (credit_card, debit_card, bank_transfer)
- status: Enum (paid, pending)
- vendor: String
- created_at: Timestamp
- updated_at: Timestamp

## Tech Stack
- Backend: Flask/FastAPI (Python)
- Database: SQLite (development), PostgreSQL (production)
- ORM: SQLAlchemy
- Frontend: Streamlit or Flask with templates

## Features
1. CSV Import
   - Import income/expense CSV files
   - Validate data before import
   - Show preview before committing to database

2. Data Entry Forms
   - Add new income records
   - Add new expense records
   - Edit existing records

3. Reporting
   - Monthly/quarterly/annual summaries
   - Category-based expense analysis
   - Project-based income tracking
   - Tax liability calculations

4. Export
   - Generate reports in CSV/PDF format
   - Export specific date ranges
   - Custom filtering options

## Implementation Plan
1. Set up project structure
2. Implement database models
3. Create CSV import functionality
4. Build data entry forms
5. Develop reporting features
6. Add export capabilities
7. Deploy application