# Invoice System

The Akowe Financial Tracker includes a powerful invoice system that works with the timesheet feature to create professional invoices for your clients.

## Features

- Generate invoices from timesheet entries
- Customizable company name and details
- Tax calculation with configurable rates
- Invoice status tracking (draft, sent, paid)
- Print-friendly invoice templates
- Payment tracking

## Configuration

Set your company name in the environment variables:

```
COMPANY_NAME=Your Company Name
```

This name will appear on all generated invoices. If not set, "Akowe" will be used as the default.

## Usage

### Creating Invoices

1. Navigate to **Invoices** in the main navigation
2. Click **New Invoice**
3. Select the client for the invoice
4. Check the timesheet entries to include
5. Set the issue date, due date, and tax rate
6. Add any notes or payment instructions
7. Click **Create Invoice**

### Invoice Workflow

Invoices follow a standard workflow:

1. **Draft**: Initially created, can be edited or deleted
2. **Sent**: Marked as sent to client, limited editing
3. **Paid**: Payment recorded, no further changes allowed

### Marking Invoices as Sent

1. View the invoice
2. Click **Mark as Sent**
3. The sent date is recorded automatically

### Recording Payments

1. View the invoice
2. Click **Mark as Paid**
3. Enter payment details:
   - Payment method (bank transfer, credit card, etc.)
   - Payment reference (transaction ID, check number, etc.)
4. Click **Mark as Paid**

The timesheet entries linked to the invoice will also be marked as paid.

### Printing/Exporting Invoices

1. View the invoice
2. Click **Print**
3. Use your browser's print function to print or save as PDF

### Invoice Numbering

Invoices are automatically numbered in the format:

```
INV-YYYYMM-XXXX
```

Where:
- YYYY = Year
- MM = Month
- XXXX = Sequential number (e.g., 0001, 0002)

## Reporting

The invoice system integrates with the dashboard to provide insights into your invoicing, including:

- Total invoiced amount
- Paid vs. outstanding amounts
- Overdue invoices
- Revenue by client

## Best Practices

1. Create invoices regularly to maintain cash flow
2. Include detailed descriptions in timesheet entries
3. Set consistent payment terms
4. Follow up on overdue invoices promptly
5. Record payments as soon as they're received