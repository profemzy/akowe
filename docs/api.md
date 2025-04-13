# Akowe Mobile API Documentation

This document provides comprehensive documentation for the Akowe Financial Tracker REST API, which can be used to build mobile applications or integrate with other systems.

## Authentication

The API uses JSON Web Tokens (JWT) for authentication.

### Login

```
POST /api/login
```

**Request Body:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "user",
    "email": "user@example.com",
    "first_name": "First",
    "last_name": "Last",
    "is_admin": false
  }
}
```

**Authentication for other endpoints:**

Include the JWT token in the Authorization header for all subsequent requests:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## User Endpoints

### Get Current User

```
GET /api/user
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "user",
    "email": "user@example.com",
    "first_name": "First",
    "last_name": "Last",
    "is_admin": false
  }
}
```

### Change Password

```
PUT /api/user/password
```

**Request Body:**
```json
{
  "current_password": "your_current_password",
  "new_password": "your_new_password"
}
```

**Response:**
```json
{
  "message": "Password changed successfully"
}
```

## Expense Endpoints

### Get All Expenses

```
GET /api/expenses
```

**Query Parameters:**
- `category` - Filter by expense category
- `status` - Filter by expense status
- `start_date` - Filter expenses on or after this date (YYYY-MM-DD)
- `end_date` - Filter expenses on or before this date (YYYY-MM-DD)

**Response:**
```json
{
  "expenses": [
    {
      "id": 1,
      "date": "2025-04-12",
      "title": "WD Red Plus 12TB NAS Hard Disk Drive",
      "amount": "386.37",
      "category": "hardware",
      "payment_method": "credit_card",
      "status": "pending",
      "vendor": "Newegg",
      "has_receipt": true,
      "created_at": "2025-04-12T08:15:30",
      "updated_at": "2025-04-12T08:15:30"
    },
    // More expenses...
  ]
}
```

### Get Expense by ID

```
GET /api/expenses/{id}
```

**Response:**
```json
{
  "id": 1,
  "date": "2025-04-12",
  "title": "WD Red Plus 12TB NAS Hard Disk Drive",
  "amount": "386.37",
  "category": "hardware",
  "payment_method": "credit_card",
  "status": "pending",
  "vendor": "Newegg",
  "has_receipt": true,
  "receipt_url": "https://storage.blob.core.windows.net/receipts/receipt.jpg?token...",
  "created_at": "2025-04-12T08:15:30",
  "updated_at": "2025-04-12T08:15:30"
}
```

### Create Expense

```
POST /api/expenses
```

**Request Body (JSON):**
```json
{
  "date": "2025-04-15",
  "title": "New Expense",
  "amount": "150.00",
  "category": "software",
  "payment_method": "credit_card",
  "status": "paid",
  "vendor": "Vendor Name"
}
```

**Multipart Form for Receipt Upload:**
- All fields above as form data
- Add a file field named `receipt` containing the receipt image or PDF

**Response:**
```json
{
  "message": "Expense created successfully",
  "expense": {
    "id": 3,
    "date": "2025-04-15",
    "title": "New Expense",
    "amount": "150.00",
    "category": "software",
    "payment_method": "credit_card",
    "status": "paid",
    "vendor": "Vendor Name",
    "has_receipt": true
  }
}
```

### Update Expense

```
PUT /api/expenses/{id}
```

**Request Body (JSON):**
```json
{
  "date": "2025-04-15",
  "title": "Updated Expense",
  "amount": "175.00",
  "category": "software",
  "payment_method": "credit_card",
  "status": "paid",
  "vendor": "Vendor Name",
  "delete_receipt": "false"
}
```

**Multipart Form for Receipt Update:**
- Only include fields you want to update
- Add a file field named `receipt` to update the receipt
- Set `delete_receipt` to "true" to delete the current receipt without uploading a new one

**Response:**
```json
{
  "message": "Expense updated successfully",
  "expense": {
    "id": 3,
    "date": "2025-04-15",
    "title": "Updated Expense",
    "amount": "175.00",
    "category": "software",
    "payment_method": "credit_card",
    "status": "paid",
    "vendor": "Vendor Name",
    "has_receipt": true
  }
}
```

### Delete Expense

```
DELETE /api/expenses/{id}
```

**Response:**
```json
{
  "message": "Expense deleted successfully"
}
```

## Income Endpoints

### Get All Incomes

```
GET /api/incomes
```

**Query Parameters:**
- `client` - Filter by client name (partial match)
- `start_date` - Filter incomes on or after this date (YYYY-MM-DD)
- `end_date` - Filter incomes on or before this date (YYYY-MM-DD)

**Response:**
```json
{
  "incomes": [
    {
      "id": 1,
      "date": "2025-03-21",
      "amount": "9040.00",
      "client": "SearchLabs (RAVL)",
      "project": "P2025001 - Interac Konek",
      "invoice": "Invoice #INV-202503-0002 - SearchLabs",
      "created_at": "2025-03-21T09:30:15",
      "updated_at": "2025-03-21T09:30:15"
    },
    // More incomes...
  ]
}
```

### Get Income by ID

```
GET /api/incomes/{id}
```

**Response:**
```json
{
  "id": 1,
  "date": "2025-03-21",
  "amount": "9040.00",
  "client": "SearchLabs (RAVL)",
  "project": "P2025001 - Interac Konek",
  "invoice": "Invoice #INV-202503-0002 - SearchLabs",
  "created_at": "2025-03-21T09:30:15",
  "updated_at": "2025-03-21T09:30:15"
}
```

### Create Income

```
POST /api/incomes
```

**Request Body:**
```json
{
  "date": "2025-04-21",
  "amount": "8500.00",
  "client": "New Client",
  "project": "New Project",
  "invoice": "Invoice #123"
}
```

**Response:**
```json
{
  "message": "Income created successfully",
  "income": {
    "id": 3,
    "date": "2025-04-21",
    "amount": "8500.00",
    "client": "New Client",
    "project": "New Project",
    "invoice": "Invoice #123"
  }
}
```

### Update Income

```
PUT /api/incomes/{id}
```

**Request Body:**
```json
{
  "date": "2025-04-22",
  "amount": "9000.00",
  "client": "Updated Client",
  "project": "Updated Project",
  "invoice": "Invoice #124"
}
```

**Response:**
```json
{
  "message": "Income updated successfully",
  "income": {
    "id": 3,
    "date": "2025-04-22",
    "amount": "9000.00",
    "client": "Updated Client",
    "project": "Updated Project",
    "invoice": "Invoice #124"
  }
}
```

### Delete Income

```
DELETE /api/incomes/{id}
```

**Response:**
```json
{
  "message": "Income deleted successfully"
}
```

## Dashboard Endpoints

### Get Dashboard Data

```
GET /api/dashboard
```

**Query Parameters:**
- `period` - Time period for data (year, quarter, month). Defaults to year.

**Response:**
```json
{
  "period": "year",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "summary": {
    "total_income": "26620.00",
    "total_expense": "3782.37",
    "net_income": "22837.63"
  },
  "expense_breakdown": [
    {
      "category": "hardware",
      "amount": "2578.37",
      "percentage": "68.17"
    },
    {
      "category": "software",
      "amount": "1204.00",
      "percentage": "31.83"
    }
  ],
  "income_breakdown": [
    {
      "client": "SearchLabs (RAVL)",
      "amount": "18080.00",
      "percentage": "67.92"
    },
    {
      "client": "TechCorp",
      "amount": "8540.00",
      "percentage": "32.08"
    }
  ],
  "recent_expenses": [
    {
      "id": 2,
      "date": "2025-04-12",
      "title": "WD Red Plus 12TB NAS Hard Disk Drive",
      "amount": "386.37",
      "category": "hardware"
    }
    // More expenses...
  ],
  "recent_incomes": [
    {
      "id": 1,
      "date": "2025-03-21",
      "amount": "9040.00",
      "client": "SearchLabs (RAVL)"
    }
    // More incomes...
  ]
}
```

## Export Endpoints

### Export Expenses

```
GET /api/export/expenses
```

**Query Parameters:**
- `start_date` - Filter expenses on or after this date (YYYY-MM-DD)
- `end_date` - Filter expenses on or before this date (YYYY-MM-DD)

**Response:**
```json
{
  "csv_data": "date,title,amount,category,payment_method,status,vendor\n2025-04-12,WD Red Plus 12TB NAS Hard Disk Drive,386.37,hardware,credit_card,pending,Newegg\n..."
}
```

### Export Incomes

```
GET /api/export/incomes
```

**Query Parameters:**
- `start_date` - Filter incomes on or after this date (YYYY-MM-DD)
- `end_date` - Filter incomes on or before this date (YYYY-MM-DD)

**Response:**
```json
{
  "csv_data": "date,amount,client,project,invoice\n2025-03-21,9040.00,SearchLabs (RAVL),P2025001 - Interac Konek,Invoice #INV-202503-0002 - SearchLabs\n..."
}
```

## Reference Data Endpoints

### Get Expense Categories

```
GET /api/references/categories
```

**Response:**
```json
{
  "categories": [
    "hardware", 
    "software", 
    "rent", 
    "utilities", 
    "travel", 
    "food", 
    "entertainment", 
    "professional_services", 
    "office_supplies", 
    "marketing", 
    "maintenance", 
    "taxes", 
    "insurance", 
    "other"
  ]
}
```

### Get Payment Methods

```
GET /api/references/payment-methods
```

**Response:**
```json
{
  "payment_methods": [
    "credit_card", 
    "debit_card", 
    "bank_transfer", 
    "cash", 
    "other"
  ]
}
```

### Get Expense Statuses

```
GET /api/references/statuses
```

**Response:**
```json
{
  "statuses": [
    "paid", 
    "pending", 
    "cancelled"
  ]
}
```