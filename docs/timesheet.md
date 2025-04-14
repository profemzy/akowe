# Timesheet System

The Akowe Financial Tracker includes a comprehensive timesheet system to track your billable hours and generate invoices.

## Features

- Track billable hours by client and project
- Weekly and list views for time entries
- View total hours and billable amounts
- Generate invoices directly from timesheet entries
- Track timesheet status (pending, billed, paid)

## Configuration

Set your default hourly rate in the environment variables:

```
DEFAULT_HOURLY_RATE=120.00
```

This rate will be used as the default when creating new timesheet entries, but can be overridden on a per-entry basis.

## Usage

### Adding Time Entries

1. Navigate to **Timesheets** in the main navigation
2. Click **New Timesheet Entry** or use the **Quick Add** form
3. Enter the following details:
   - Date
   - Client
   - Project
   - Description of work
   - Hours worked
   - Hourly rate (defaults to your configured rate)
4. Click **Save Timesheet Entry**

### Weekly View

The weekly view provides a calendar interface to see your tracked time by day:

1. Navigate to **Timesheets** → **Weekly View**
2. Use the navigation buttons to move between weeks
3. Click the plus icon on any day to add a new entry
4. View daily and weekly totals

### Creating Invoices from Timesheet Entries

1. Navigate to **Invoices** → **New Invoice**
2. Select a client (this will pre-select all unbilled entries for that client)
3. Check the timesheet entries you want to include
4. Enter invoice details (issue date, due date, tax rate, etc.)
5. Click **Create Invoice**

Once entries are added to an invoice, their status changes to "billed" and they can no longer be edited.

### Reporting

The timesheet system integrates with the dashboard to provide insights into your billable hours, including:

- Total hours by client
- Total hours by project
- Unbilled hours
- Average hourly rate

## API Integration

The timesheet system exposes endpoints through the mobile API for integration with time tracking apps.

## Best Practices

1. Enter your time regularly to ensure accurate tracking
2. Use consistent client and project names
3. Add detailed descriptions to make invoicing easier
4. Review unbilled time entries regularly to ensure timely invoicing