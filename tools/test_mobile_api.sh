#!/bin/bash

# This script runs the mobile API tests and demonstrates how to use the API

echo "Running mobile API tests..."
python -m pytest tests/test_mobile_api.py -v

echo ""
echo "Mobile API Usage Examples:"
echo "=========================="
echo ""
echo "1. Authentication:"
echo "   curl -X POST http://localhost:5000/api/login \\
     -H \"Content-Type: application/json\" \\
     -d '{\"username\":\"your_username\",\"password\":\"your_password\"}'"
echo ""
echo "2. Get User Info:"
echo "   curl -X GET http://localhost:5000/api/user \\
     -H \"Authorization: Bearer your_token_here\""
echo ""
echo "   IMPORTANT: The 'Bearer ' prefix is required before the token!"
echo "   Incorrect: -H \"Authorization: your_token_here\""
echo "   Correct:   -H \"Authorization: Bearer your_token_here\""
echo ""
echo "3. Get Clients:"
echo "   curl -X GET http://localhost:5000/api/clients \\
     -H \"Authorization: Bearer your_token_here\""
echo ""
echo "4. Create a Timesheet Entry:"
echo "   curl -X POST http://localhost:5000/api/timesheets \\
     -H \"Content-Type: application/json\" \\
     -H \"Authorization: Bearer your_token_here\" \\
     -d '{
       \"date\": \"2025-04-21\",
       \"client_id\": 1,
       \"project_id\": 1,
       \"description\": \"API Development\",
       \"hours\": \"4.5\",
       \"hourly_rate\": \"125.00\"
     }'"
echo ""
echo "5. Get Tax Dashboard:"
echo "   curl -X GET http://localhost:5000/api/tax/dashboard \\
     -H \"Authorization: Bearer your_token_here\""
echo ""
echo "For more API endpoints and details, see docs/mobile_api.md"
