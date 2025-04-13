# Receipt Upload for Expenses

Akowe Financial Tracker now supports uploading and managing receipts for expense records using Azure Blob Storage.

## Features

- Upload receipt images (JPEG, PNG, GIF) or PDF files for any expense
- View receipts directly from the expense list or detail view
- Delete receipts when no longer needed
- Secure storage in Azure Blob Storage
- Temporary access URLs using Shared Access Signatures (SAS)

## Setup

Before using receipt upload features, you need to configure Azure Blob Storage:

1. Create an Azure Storage account if you don't have one
2. Create a container named `receipts` in your storage account
3. Set the environment variable `AZURE_STORAGE_CONNECTION_STRING` with your Azure Storage connection string
4. Run database migrations to add the required fields to the expense table:
   ```
   flask db upgrade
   ```
   
   If you're starting with a fresh installation, the migration will be applied automatically during setup.

Example environment variable:

```
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=mykey;EndpointSuffix=core.windows.net
```

You can add this to your `.env` file or set it directly in your environment.

## Using Receipt Upload

### Adding a Receipt to a New Expense

1. Navigate to "Add Expense"
2. Fill in the expense details as usual
3. In the "Receipt Image" field, click "Choose File" and select your receipt file
4. Click "Save Expense" to save the expense with the receipt

### Adding or Updating a Receipt for an Existing Expense

1. Navigate to the expense list and click "Edit" for the desired expense
2. In the "Receipt Image" field, click "Choose File" and select your receipt file
3. Click "Update Expense" to save the changes

### Viewing a Receipt

1. From the expense list, click the receipt icon in the "Receipt" column
2. From the expense edit screen, click "View Receipt"

The receipt will open in a new tab using a temporary secure URL.

### Deleting a Receipt

1. Navigate to the expense edit page
2. Click "Delete Receipt" next to the current receipt information
3. Confirm the deletion

## Technical Details

- Files are stored in Azure Blob Storage with randomized names to ensure security
- File size is limited to 5MB
- Supported file types: JPEG, PNG, GIF, PDF
- When viewing receipts, a temporary SAS token is generated with a 1-hour expiration
- When deleting an expense, any associated receipt is automatically deleted
- Database migration adds `receipt_blob_name` and `receipt_url` columns to the `expense` table