## Pesalink_AI_Hackathon_16_2025

This project validates user bank accounts by integrating with the PesaLink Account Validation API. It processes a CSV file containing account numbers and transaction amounts, performs both rule-based and API-based validation, and outputs valid and invalid account files.

# Dependencies
Ensure you have the following Python packages installed:
pip install pandas numpy fastapi requests pydantic python-multipart uvicorn


# 🛠️ How to Run
1. Start the FastAPI Server
The API exposes a /validate-account endpoint that calls the PesaLink validation API.
To start the FastAPI server, run:
uvicorn main:app --reload


File: main.py
Endpoint: POST /validate-account

The FastAPI app receives an account number and transaction amount, validates the account using the PesaLink API, and returns a structured response:
{
  "is_valid": true,
  "is_active": true,
  "can_send_receive": true,
  "reason": "Valid"
}


2. Prepare Input CSV
Create a file named accounts.csv with the following columns:
account_number,transaction_amount
1234567890,1000
9876543210,500
...


3. Run the Bulk Validator
Use the provided script to process the CSV file and call the FastAPI backend in batches:
python validation.py


# Output
After running the bulk validator, the script will return the following JSON output summarizing the process:


{
  "valid": true,
  "invalid": true,
  "processed": true
}


valid: Indicates whether valid accounts were found and written to valid_accounts.csv.


invalid: Indicates whether invalid accounts were found and written to invalid_accounts.csv.


processed: Indicates whether the CSV file was successfully processed.

Each row in the results includes:

is_valid: Whether the account passed validation


is_active: Whether the account had recent activity


can_send_receive: Whether the account is ready for transactions


reason: Explanation for validation result



# Integration with PesaLink

This system integrates with:

PesaLink Account Validation API

Base URL:
https://account-validation-service.dev.pesalink.co.ke/api/key
Authentication:


{
  "apiKey": "your-api-key-here"
}

