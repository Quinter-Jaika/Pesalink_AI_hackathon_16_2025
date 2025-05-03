from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
from pydantic import BaseModel
import pandas as pd
from typing import Dict

app = FastAPI()

# Load your pre-existing dataset (replace with your actual data path)
DATASET_PATH = "Bank_Transaction_Fraud_Detection.csv"
df = pd.read_csv(DATASET_PATH)

# Convert fields to appropriate types
df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"])
df["Customer_ID"] = df["Customer_ID"].astype(str)

# Mock bank codes (replace with Pesalink codes)
VALID_BANK_CODES = ["011", "023", "045"]

class ValidationRequest(BaseModel):
    account_number: str
    transaction_amount: float

class ValidationResponse(BaseModel):
    is_valid: bool
    is_active: bool
    can_send_receive: bool
    reason: str  # e.g., "Insufficient funds", "Invalid bank code"

@app.post("/validate-account")
def validate_account(request: ValidationRequest) -> ValidationResponse:
    """Mock validation based on pre-existing data."""
    # Rule 1: Check if account exists and has valid format
    account_data = df[df["Customer_ID"] == request.account_number]
    if account_data.empty:
        return ValidationResponse(
            is_valid=False,
            is_active=False,
            can_send_receive=False,
            reason="Account not found"
        )

    # Rule 2: Check if account is active (recent transaction)
    last_transaction_date = account_data["Transaction_Date"].max()
    is_active = (datetime.now() - last_transaction_date) <= timedelta(days=30)

    # Rule 3: Check fraud/block status
    is_blocked = account_data["Is_Fraud"].any()

    # Rule 4: Sufficient balance
    account_balance = account_data["Account_Balance"].iloc[-1]  # Latest balance
    has_funds = account_balance >= request.transaction_amount

    # Compile results
    is_valid = is_active and not is_blocked
    can_send_receive = is_valid and has_funds

    reason = (
        "Insufficient funds" if not has_funds else
        "Account blocked" if is_blocked else
        "Inactive account" if not is_active else
        "Valid"
    )

    return ValidationResponse(
        is_valid=is_valid,
        is_active=is_active,
        can_send_receive=can_send_receive,
        reason=reason
    )

# Run with: uvicorn mock_api:app --reload