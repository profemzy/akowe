# Akowe Mobile API Documentation

This document provides comprehensive documentation for the enhanced Akowe Financial Tracker REST API, which can be used to build mobile applications or integrate with other systems.

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

⚠️ **IMPORTANT**: The "Bearer " prefix is required before the token. Without this prefix, the authentication will fail with a "Authentication required" message.

Incorrect:
```
Authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Correct:
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

## Timesheet Endpoints

### Get All Timesheet Entries

```
GET /api/timesheets
```

**Query Parameters:**
- `status` - Filter by status (pending, billed, paid)
- `client_id` - Filter by client ID
- `project_id` - Filter by project ID
- `from_date` - Filter entries on or after this date (YYYY-MM-DD)
- `to_date` - Filter entries on or before this date (YYYY-MM-DD)

**Response:**
```json
{
  "timesheets": [
    {
      "id": 1,
      "date": "2025-04-15",
      "client_id": 2,
      "client_name": "SearchLabs",
      "project_id": 5,
      "project_name": "Interac Konek",
      "description": "API development",
      "hours": "4.50",
      "hourly_rate": "120.00",
      "amount": "540.00",
      "status": "pending",
      "invoice_id": null,
      "created_at": "2025-04-15T14:30:00",
      "updated_at": "2025-04-15T14:30:00"
    },
    // More timesheet entries...
  ],
  "summary": {
    "total_hours": "35.50",
    "total_amount": "4260.00",
    "unbilled_hours": "12.75",
    "unbilled_amount": "1530.00",
    "count": 8
  }
}
```

### Get Timesheet Entry by ID

```
GET /api/timesheets/{id}
```

**Response:**
```json
{
  "id": 1,
  "date": "2025-04-15",
  "client_id": 2,
  "client_name": "SearchLabs",
  "project_id": 5,
  "project_name": "Interac Konek",
  "description": "API development",
  "hours": "4.50",
  "hourly_rate": "120.00",
  "amount": "540.00",
  "status": "pending",
  "invoice_id": null,
  "created_at": "2025-04-15T14:30:00",
  "updated_at": "2025-04-15T14:30:00"
}
```

### Create Timesheet Entry

```
POST /api/timesheets
```

**Request Body:**
```json
{
  "date": "2025-04-21",
  "client_id": 2,
  "project_id": 5,
  "description": "Mobile app development",
  "hours": "6.25",
  "hourly_rate": "125.00"
}
```

**Response:**
```json
{
  "message": "Timesheet entry created successfully",
  "timesheet": {
    "id": 9,
    "date": "2025-04-21",
    "client_id": 2,
    "client_name": "SearchLabs",
    "project_id": 5,
    "project_name": "Interac Konek",
    "description": "Mobile app development",
    "hours": "6.25",
    "hourly_rate": "125.00",
    "amount": "781.25",
    "status": "pending"
  }
}
```

### Update Timesheet Entry

```
PUT /api/timesheets/{id}
```

**Request Body:**
```json
{
  "date": "2025-04-22",
  "description": "Mobile app development and testing",
  "hours": "7.50",
  "hourly_rate": "125.00"
}
```

**Response:**
```json
{
  "message": "Timesheet entry updated successfully",
  "timesheet": {
    "id": 9,
    "date": "2025-04-22",
    "client_id": 2,
    "client_name": "SearchLabs",
    "project_id": 5,
    "project_name": "Interac Konek",
    "description": "Mobile app development and testing",
    "hours": "7.50",
    "hourly_rate": "125.00",
    "amount": "937.50",
    "status": "pending"
  }
}
```

### Delete Timesheet Entry

```
DELETE /api/timesheets/{id}
```

**Response:**
```json
{
  "message": "Timesheet entry deleted successfully"
}
```

### Get Weekly Timesheet

```
GET /api/timesheets/weekly
```

**Query Parameters:**
- `week_start` - Start date of the week (YYYY-MM-DD, defaults to current week)

**Response:**
```json
{
  "week_start": "2025-04-20",
  "week_end": "2025-04-26",
  "days": [
    {
      "date": "2025-04-20",
      "day_of_week": "Monday",
      "entries": [
        {
          "id": 9,
          "client_id": 2,
          "client_name": "SearchLabs",
          "project_id": 5,
          "project_name": "Interac Konek",
          "description": "Mobile app development",
          "hours": "6.25",
          "hourly_rate": "125.00",
          "amount": "781.25",
          "status": "pending"
        }
      ],
      "total_hours": "6.25"
    },
    // More days...
  ],
  "total_hours": "28.75",
  "prev_week": "2025-04-13",
  "next_week": "2025-04-27",
  "daily_totals": {
    "2025-04-20": "6.25",
    "2025-04-21": "4.50",
    // More days...
  }
}
```

## Client Endpoints

### Get All Clients

```
GET /api/clients
```

**Query Parameters:**
- `name` - Filter by client name (partial match)

**Response:**
```json
{
  "clients": [
    {
      "id": 1,
      "name": "TechCorp",
      "email": "billing@techcorp.com",
      "phone": "555-123-4567",
      "address": "123 Tech St, San Francisco, CA 94107",
      "contact_person": "John Smith",
      "notes": "Enterprise client",
      "created_at": "2025-01-15T10:30:00",
      "updated_at": "2025-03-20T14:15:00",
      "project_count": 3,
      "invoice_count": 5,
      "timesheet_count": 24
    },
    // More clients...
  ],
  "count": 8
}
```

### Get Client by ID

```
GET /api/clients/{id}
```

**Response:**
```json
{
  "id": 1,
  "name": "TechCorp",
  "email": "billing@techcorp.com",
  "phone": "555-123-4567",
  "address": "123 Tech St, San Francisco, CA 94107",
  "contact_person": "John Smith",
  "notes": "Enterprise client",
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-03-20T14:15:00",
  "projects": [
    {
      "id": 1,
      "name": "Website Redesign",
      "status": "active",
      "hourly_rate": "125.00"
    },
    // More projects...
  ],
  "recent_invoices": [
    {
      "id": 12,
      "invoice_number": "INV-202504-0003",
      "issue_date": "2025-04-15",
      "due_date": "2025-05-15",
      "total": "4500.00",
      "status": "sent"
    },
    // More invoices...
  ],
  "recent_timesheet_entries": [
    {
      "id": 45,
      "date": "2025-04-18",
      "project": "Website Redesign",
      "description": "Frontend development",
      "hours": "6.50",
      "amount": "812.50",
      "status": "pending"
    },
    // More timesheet entries...
  ]
}
```

### Create Client

```
POST /api/clients
```

**Request Body:**
```json
{
  "name": "New Client Inc",
  "email": "contact@newclient.com",
  "phone": "555-987-6543",
  "address": "456 New St, Toronto, ON M5V 2H1",
  "contact_person": "Jane Doe",
  "notes": "Referred by TechCorp"
}
```

**Response:**
```json
{
  "message": "Client created successfully",
  "client": {
    "id": 9,
    "name": "New Client Inc",
    "email": "contact@newclient.com",
    "phone": "555-987-6543",
    "address": "456 New St, Toronto, ON M5V 2H1",
    "contact_person": "Jane Doe",
    "notes": "Referred by TechCorp"
  }
}
```

### Update Client

```
PUT /api/clients/{id}
```

**Request Body:**
```json
{
  "name": "New Client Corporation",
  "email": "billing@newclient.com",
  "phone": "555-987-6543",
  "address": "456 New St, Toronto, ON M5V 2H1",
  "contact_person": "Jane Doe",
  "notes": "Referred by TechCorp, major enterprise client"
}
```

**Response:**
```json
{
  "message": "Client updated successfully",
  "client": {
    "id": 9,
    "name": "New Client Corporation",
    "email": "billing@newclient.com",
    "phone": "555-987-6543",
    "address": "456 New St, Toronto, ON M5V 2H1",
    "contact_person": "Jane Doe",
    "notes": "Referred by TechCorp, major enterprise client"
  }
}
```

### Delete Client

```
DELETE /api/clients/{id}
```

**Response:**
```json
{
  "message": "Client deleted successfully"
}
```

### Get Client Projects

```
GET /api/clients/{id}/projects
```

**Response:**
```json
{
  "client_id": 1,
  "client_name": "TechCorp",
  "projects": [
    {
      "id": 1,
      "name": "Website Redesign",
      "description": "Complete redesign of corporate website",
      "status": "active",
      "hourly_rate": "125.00",
      "created_at": "2025-01-20T09:15:00",
      "updated_at": "2025-03-15T11:30:00",
      "timesheet_count": 18
    },
    // More projects...
  ],
  "count": 3
}
```

### Get Client Invoices

```
GET /api/clients/{id}/invoices
```

**Response:**
```json
{
  "client_id": 1,
  "client_name": "TechCorp",
  "invoices": [
    {
      "id": 12,
      "invoice_number": "INV-202504-0003",
      "issue_date": "2025-04-15",
      "due_date": "2025-05-15",
      "subtotal": "4000.00",
      "tax_amount": "500.00",
      "total": "4500.00",
      "status": "sent",
      "sent_date": "2025-04-15T14:30:00",
      "paid_date": null
    },
    // More invoices...
  ],
  "count": 5
}
```

### Get Client Timesheets

```
GET /api/clients/{id}/timesheets
```

**Response:**
```json
{
  "client_id": 1,
  "client_name": "TechCorp",
  "timesheet_entries": [
    {
      "id": 45,
      "date": "2025-04-18",
      "project_id": 1,
      "project_name": "Website Redesign",
      "description": "Frontend development",
      "hours": "6.50",
      "hourly_rate": "125.00",
      "amount": "812.50",
      "status": "pending",
      "invoice_id": null
    },
    // More timesheet entries...
  ],
  "count": 24,
  "summary": {
    "total_hours": "156.25",
    "total_amount": "19531.25",
    "unbilled_hours": "32.50",
    "unbilled_amount": "4062.50"
  }
}
```

## Project Endpoints

### Get All Projects

```
GET /api/projects
```

**Query Parameters:**
- `name` - Filter by project name (partial match)
- `client_id` - Filter by client ID
- `status` - Filter by status (active, completed, archived)

**Response:**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "Website Redesign",
      "description": "Complete redesign of corporate website",
      "status": "active",
      "hourly_rate": "125.00",
      "client_id": 1,
      "client_name": "TechCorp",
      "created_at": "2025-01-20T09:15:00",
      "updated_at": "2025-03-15T11:30:00",
      "timesheet_count": 18
    },
    // More projects...
  ],
  "count": 12
}
```

### Get Project by ID

```
GET /api/projects/{id}
```

**Response:**
```json
{
  "id": 1,
  "name": "Website Redesign",
  "description": "Complete redesign of corporate website",
  "status": "active",
  "hourly_rate": "125.00",
  "client_id": 1,
  "client_name": "TechCorp",
  "created_at": "2025-01-20T09:15:00",
  "updated_at": "2025-03-15T11:30:00",
  "recent_timesheet_entries": [
    {
      "id": 45,
      "date": "2025-04-18",
      "description": "Frontend development",
      "hours": "6.50",
      "hourly_rate": "125.00",
      "amount": "812.50",
      "status": "pending",
      "invoice_id": null
    },
    // More timesheet entries...
  ],
  "statistics": {
    "total_hours": "112.50",
    "total_amount": "14062.50",
    "unbilled_hours": "22.75",
    "unbilled_amount": "2843.75",
    "timesheet_count": 18
  }
}
```

### Create Project

```
POST /api/projects
```

**Request Body:**
```json
{
  "name": "Mobile App Development",
  "description": "iOS and Android app development",
  "status": "active",
  "hourly_rate": "135.00",
  "client_id": 9
}
```

**Response:**
```json
{
  "message": "Project created successfully",
  "project": {
    "id": 13,
    "name": "Mobile App Development",
    "description": "iOS and Android app development",
    "status": "active",
    "hourly_rate": "135.00",
    "client_id": 9,
    "client_name": "New Client Corporation"
  }
}
```

### Update Project

```
PUT /api/projects/{id}
```

**Request Body:**
```json
{
  "name": "Mobile App Development Phase 1",
  "description": "iOS and Android app development - initial phase",
  "status": "active",
  "hourly_rate": "140.00"
}
```

**Response:**
```json
{
  "message": "Project updated successfully",
  "project": {
    "id": 13,
    "name": "Mobile App Development Phase 1",
    "description": "iOS and Android app development - initial phase",
    "status": "active",
    "hourly_rate": "140.00",
    "client_id": 9,
    "client_name": "New Client Corporation"
  }
}
```

### Delete Project

```
DELETE /api/projects/{id}
```

**Response:**
```json
{
  "message": "Project deleted successfully"
}
```

### Get Project Timesheets

```
GET /api/projects/{id}/timesheets
```

**Response:**
```json
{
  "project_id": 1,
  "project_name": "Website Redesign",
  "client_id": 1,
  "client_name": "TechCorp",
  "timesheet_entries": [
    {
      "id": 45,
      "date": "2025-04-18",
      "description": "Frontend development",
      "hours": "6.50",
      "hourly_rate": "125.00",
      "amount": "812.50",
      "status": "pending",
      "invoice_id": null,
      "created_at": "2025-04-18T17:30:00",
      "updated_at": "2025-04-18T17:30:00"
    },
    // More timesheet entries...
  ],
  "count": 18,
  "summary": {
    "total_hours": "112.50",
    "total_amount": "14062.50",
    "unbilled_hours": "22.75",
    "unbilled_amount": "2843.75"
  }
}
```

### Get Project Statuses

```
GET /api/projects/statuses
```

**Response:**
```json
{
  "statuses": ["active", "completed", "archived"]
}
```

## Invoice Endpoints

### Get All Invoices

```
GET /api/invoices
```

**Query Parameters:**
- `status` - Filter by status (draft, sent, paid, overdue, cancelled)
- `client_id` - Filter by client ID
- `from_date` - Filter invoices on or after this date (YYYY-MM-DD)
- `to_date` - Filter invoices on or before this date (YYYY-MM-DD)

**Response:**
```json
{
  "invoices": [
    {
      "id": 12,
      "invoice_number": "INV-202504-0003",
      "client_id": 1,
      "client_name": "TechCorp",
      "issue_date": "2025-04-15",
      "due_date": "2025-05-15",
      "subtotal": "4000.00",
      "tax_rate": "12.50",
      "tax_amount": "500.00",
      "total": "4500.00",
      "status": "sent",
      "sent_date": "2025-04-15T14:30:00",
      "paid_date": null,
      "created_at": "2025-04-15T10:20:00",
      "updated_at": "2025-04-15T14:30:00",
      "timesheet_count": 8
    },
    // More invoices...
  ],
  "count": 15,
  "summary": {
    "total_paid": "32500.00",
    "total_outstanding": "12750.00",
    "total_draft": "4200.00",
    "total_all": "49450.00"
  }
}
```

### Get Invoice by ID

```
GET /api/invoices/{id}
```

**Response:**
```json
{
  "id": 12,
  "invoice_number": "INV-202504-0003",
  "client_id": 1,
  "client_name": "TechCorp",
  "company_name": "Akowe",
  "issue_date": "2025-04-15",
  "due_date": "2025-05-15",
  "notes": "Payment due within 30 days",
  "subtotal": "4000.00",
  "tax_rate": "12.50",
  "tax_amount": "500.00",
  "total": "4500.00",
  "status": "sent",
  "sent_date": "2025-04-15T14:30:00",
  "paid_date": null,
  "payment_method": null,
  "payment_reference": null,
  "created_at": "2025-04-15T10:20:00",
  "updated_at": "2025-04-15T14:30:00",
  "timesheet_entries": [
    {
      "id": 45,
      "date": "2025-04-18",
      "client_id": 1,
      "project_id": 1,
      "project_name": "Website Redesign",
      "description": "Frontend development",
      "hours": "6.50",
      "hourly_rate": "125.00",
      "amount": "812.50",
      "status": "billed"
    },
    // More timesheet entries...
  ]
}
```

### Create Invoice

```
POST /api/invoices
```

**Request Body:**
```json
{
  "client_id": 9,
  "issue_date": "2025-04-25",
  "due_date": "2025-05-25",
  "notes": "Payment due within 30 days",
  "tax_rate": "13.00",
  "timesheet_ids": [50, 51, 52]
}
```

**Response:**
```json
{
  "message": "Invoice created successfully",
  "invoice": {
    "id": 16,
    "invoice_number": "INV-202504-0004",
    "client_id": 9,
    "client_name": "New Client Corporation",
    "issue_date": "2025-04-25",
    "due_date": "2025-05-25",
    "subtotal": "2800.00",
    "tax_rate": "13.00",
    "tax_amount": "364.00",
    "total": "3164.00",
    "status": "draft",
    "timesheet_count": 3
  }
}
```

### Update Invoice

```
PUT /api/invoices/{id}
```

**Request Body:**
```json
{
  "client_id": 9,
  "issue_date": "2025-04-26",
  "due_date": "2025-05-26",
  "notes": "Payment due within 30 days, updated terms",
  "tax_rate": "13.00",
  "timesheet_ids": [50, 51, 52, 53]
}
```

**Response:**
```json
{
  "message": "Invoice updated successfully",
  "invoice": {
    "id": 16,
    "invoice_number": "INV-202504-0004",
    "client_id": 9,
    "client_name": "New Client Corporation",
    "issue_date": "2025-04-26",
    "due_date": "2025-05-26",
    "subtotal": "3500.00",
    "tax_rate": "13.00",
    "tax_amount": "455.00",
    "total": "3955.00",
    "status": "draft",
    "timesheet_count": 4
  }
}
```

### Delete Invoice

```
DELETE /api/invoices/{id}
```

**Response:**
```json
{
  "message": "Invoice deleted successfully"
}
```

### Mark Invoice as Sent

```
POST /api/invoices/{id}/mark-sent
```

**Response:**
```json
{
  "message": "Invoice marked as sent"
}
```

### Mark Invoice as Paid

```
POST /api/invoices/{id}/mark-paid
```

**Request Body:**
```json
{
  "payment_method": "bank_transfer",
  "payment_reference": "TRF123456789"
}
```

**Response:**
```json
{
  "message": "Invoice marked as paid",
  "income_created": true
}
```

### Get Unbilled Timesheets

```
GET /api/invoices/unbilled-timesheets
```

**Query Parameters:**
- `client_id` - Filter by client ID

**Response:**
```json
{
  "clients": [
    {
      "client_id": 1,
      "client_name": "TechCorp",
      "entries": [
        {
          "id": 45,
          "date": "2025-04-18",
          "client_id": 1,
          "client_name": "TechCorp",
          "project_id": 1,
          "project_name": "Website Redesign",
          "description": "Frontend development",
          "hours": "6.50",
          "hourly_rate": "125.00",
          "amount": "812.50"
        },
        // More entries...
      ],
      "total_hours": "22.75",
      "total_amount": "2843.75",
      "entry_count": 4
    },
    // More clients...
  ],
  "total_entries": 12,
  "total_hours": "68.25",
  "total_amount": "8531.25"
}
```

### Get Invoice Statuses

```
GET /api/invoices/statuses
```

**Response:**
```json
{
  "statuses": ["draft", "sent", "paid", "overdue", "cancelled"]
}
```

## Tax Dashboard Endpoints

### Get Tax Dashboard Data

```
GET /api/tax/dashboard
```

**Query Parameters:**
- `year` - Year for tax data (defaults to current year)
- `province` - Canadian province for tax calculations (defaults to Ontario)

**Response:**
```json
{
  "selected_year": 2025,
  "available_years": [2023, 2024, 2025],
  "selected_province": "Ontario",
  "provinces": ["Alberta", "British Columbia", "Manitoba", "New Brunswick", "Newfoundland and Labrador", "Northwest Territories", "Nova Scotia", "Nunavut", "Ontario", "Prince Edward Island", "Quebec", "Saskatchewan", "Yukon"],
  "summary": {
    "total_income": "68500.00",
    "total_expenses": "12750.00",
    "net_income": "55750.00"
  },
  "cra_expense_categories": [
    {
      "tax_category": "Capital Cost Allowance (CCA)",
      "amount": "4250.00",
      "categories": ["hardware", "software"],
      "expense_count": 8,
      "percentage": "33.33"
    },
    // More categories...
  ],
  "quarterly_data": {
    "Q1 (Jan-Mar)": {
      "expenses": "3250.00",
      "income": "18500.00",
      "net": "15250.00",
      "start_date": "2025-01-01",
      "end_date": "2025-03-31"
    },
    // More quarters...
  },
  "gst_hst": {
    "rate": "0.13",
    "collected": "8905.00",
    "paid": "1478.76",
    "owing": "7426.24"
  },
  "cca_items": [
    {
      "id": 5,
      "date": "2025-02-15",
      "title": "MacBook Pro 16-inch",
      "amount": "3499.00",
      "category": "hardware",
      "cca_class": "Class 50",
      "cca_rate": "0.55",
      "deduction": "1924.45"
    },
    // More items...
  ],
  "tax_deadlines": [
    {
      "date": "April 30, 2026",
      "description": "Deadline to file and pay 2025 personal income taxes",
      "is_passed": false
    },
    // More deadlines...
  ],
  "tax_prediction": {
    // Tax prediction data if current year
  }
}
```

### Get Tax Prediction

```
GET /api/tax/prediction
```

**Query Parameters:**
- `province` - Canadian province for tax calculations (defaults to Ontario)

**Response:**
```json
{
  "year": 2025,
  "province": "Ontario",
  "provinces": ["Alberta", "British Columbia", "Manitoba", "New Brunswick", "Newfoundland and Labrador", "Northwest Territories", "Nova Scotia", "Nunavut", "Ontario", "Prince Edward Island", "Quebec", "Saskatchewan", "Yukon"],
  "prediction": {
    "year": 2025,
    "province": "Ontario",
    "as_of_date": "2025-04-21",
    "year_progress": 30.4,
    "income_to_date": "22500.00",
    "expenses_to_date": "4250.00",
    "net_income_to_date": "18250.00",
    "projected_income": "74000.00",
    "projected_expenses": "14000.00",
    "projected_net_income": "60000.00",
    "estimated_federal_tax": "10800.00",
    "estimated_provincial_tax": "7200.00",
    "estimated_cpp": "6441.00",
    "estimated_total_tax": "24441.00",
    "estimated_tax_rate": 40.7,
    "gst_hst_collected": "9620.00",
    "gst_hst_paid": "1637.17",
    "gst_hst_owing": "7982.83",
    "tax_brackets": [
      {
        "bracket": "$0 - $53,359.00",
        "rate": "15.0%",
        "amount_in_bracket": "53359.00",
        "tax_in_bracket": "8003.85",
        "is_current": true
      },
      {
        "bracket": "$53,359.01 - $106,717.00",
        "rate": "20.5%",
        "amount_in_bracket": "6641.00",
        "tax_in_bracket": "1361.41",
        "is_current": true
      },
      // More brackets...
    ],
    "months_breakdown": [
      {
        "month": 1,
        "month_name": "January",
        "is_actual": true,
        "income": "7500.00",
        "expenses": "1250.00",
        "net": "6250.00"
      },
      // More months...
    ],
    "tax_planning_suggestions": [
      {
        "type": "tax_bracket_planning",
        "title": "Near Higher Tax Bracket",
        "description": "You're $3,358.00 away from the next tax bracket (20.5% to 26.0%)",
        "benefit": "Consider timing expenses to stay below $106,717.00 threshold",
        "priority": "high"
      },
      // More suggestions...
    ]
  }
}
```

### Get Tax Category Suggestions

```
POST /api/tax/category-suggestions
```

**Request Body:**
```json
{
  "title": "Adobe Creative Cloud Subscription",
  "vendor": "Adobe"
}
```

**Response:**
```json
{
  "title": "Adobe Creative Cloud Subscription",
  "vendor": "Adobe",
  "suggestions": [
    {
      "category": "software",
      "confidence": 0.95,
      "cra_category": "Capital Cost Allowance (CCA)",
      "deduction_rate": "100%",
      "special_rules": "May be 100% deductible in year of purchase if under $500",
      "documentation_required": true
    },
    {
      "category": "subscription",
      "confidence": 0.75,
      "cra_category": "Office Expenses",
      "deduction_rate": "100%",
      "special_rules": "No special rules",
      "documentation_required": false
    },
    {
      "category": "professional_services",
      "confidence": 0.35,
      "cra_category": "Professional Fees",
      "deduction_rate": "100%",
      "special_rules": "No special rules",
      "documentation_required": true
    }
  ]
}
```

### Analyze Expenses for Tax Optimization

```
GET /api/tax/analyze-expenses
```

**Query Parameters:**
- `year` - Year for analysis (defaults to current year)

**Response:**
```json
{
  "year": 2025,
  "total_amount": "12750.00",
  "count": 24,
  "categories": [
    {
      "category": "hardware",
      "cra_category": "Capital Cost Allowance (CCA)",
      "count": 5,
      "amount": "3750.00"
    },
    // More categories...
  ],
  "recommendations": [
    {
      "type": "documentation",
      "message": "Add receipts for 3 expenses over $100",
      "impact": "high",
      "reason": "CRA requires receipts for expenses over $100"
    },
    // More recommendations...
  ],
  "missing_receipts": [
    {
      "id": 12,
      "title": "Dell UltraSharp 32-inch Monitor",
      "amount": "899.99",
      "date": "2025-03-15"
    },
    // More expenses...
  ],
  "potential_recategorizations": [
    {
      "id": 8,
      "title": "Zoom Pro Subscription",
      "vendor": "Zoom",
      "amount": "199.99",
      "current_category": "subscription",
      "suggested_category": "software",
      "confidence": 0.85,
      "current_tax_category": "Office Expenses",
      "suggested_tax_category": "Capital Cost Allowance (CCA)",
      "reason": "Based on 'Zoom' and 'Zoom Pro Subscription'"
    },
    // More recategorizations...
  ]
}
```

### Get CRA Tax Categories

```
GET /api/tax/cra-categories
```

**Response:**
```json
{
  "cra_categories": [
    {
      "category": "office_supplies",
      "cra_category": "Office Expenses"
    },
    {
      "category": "hardware",
      "cra_category": "Capital Cost Allowance (CCA)"
    },
    // More categories...
  ]
}
```

### Get CCA Classes

```
GET /api/tax/cca-classes
```

**Response:**
```json
{
  "cca_classes": [
    {
      "class": "Class 8",
      "rate": "0.20",
      "description": "Furniture, appliances, tools costing > $500",
      "examples": ["office furniture", "tools", "equipment"]
    },
    {
      "class": "Class 10",
      "rate": "0.30",
      "description": "Automotive equipment, some general-purpose electronic devices",
      "examples": ["vehicles", "general computer hardware"]
    },
    // More classes...
  ]
}
```
