import pandas as pd
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
from datetime import datetime, timedelta

# Configuration
API_URL = "http://localhost:8000/validate-account"
WORKERS = 10
BATCH_SIZE = 50
DATE_FORMAT = "%d-%m-%Y"

def validate_account_batch(batch: List[Dict]) -> List[Dict]:
    """Process accounts in batches to reduce API calls"""
    try:
        response = requests.post(
            f"{API_URL}/batch",
            json={"accounts": batch},
            timeout=10
        )
        return response.json()["results"]
    except Exception as e:
        return [{
            **account,
            "is_valid": False,
            "reason": f"API Error: {str(e)}",
            "can_send_receive": False
        } for account in batch]

def validate_bulk_accounts(df: pd.DataFrame) -> pd.DataFrame:
    """Process accounts in parallel batches"""
    records = df.to_dict("records")
    batches = [records[i:i + BATCH_SIZE] for i in range(0, len(records), BATCH_SIZE)]
    
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        batch_results = list(executor.map(validate_account_batch, batches))
        
    return pd.DataFrame([account for batch in batch_results for account in batch])

def prevalidate_accounts(df: pd.DataFrame) -> pd.DataFrame:
    """Vectorized prevalidation for better performance"""
    df = df.copy()
    
    # Before validation, standardize dates in your CSV:
    df["Transaction_Date"] = df["Transaction_Date"].replace("/", "-")
    # Convert dates
    df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"], format=DATE_FORMAT, errors="coerce")
    
    # Validate rules
    df["is_active"] = (datetime.now() - df["Transaction_Date"]) <= timedelta(days=360)
    df["is_blocked"] = df["Is_Fraud"] == 1
    df["sufficient_funds"] = df["Transaction_Amount"] <= df["Account_Balance"]
    
    # Combine validations
    df["is_valid"] = df["is_active"] & ~df["is_blocked"] & df["sufficient_funds"]
    
    # Generate reasons
    conditions = [
        (~df["is_active"], "Account inactive"),
        (df["is_blocked"], "Account blocked"),
        (~df["sufficient_funds"], "Insufficient funds")
    ]
    df["reason"] = np.select(
        [cond for cond, _ in conditions],
        [msg for _, msg in conditions],
        default="Prevalidation passed"
    )
    
    df["can_send_receive"] = False
    return df

def validate_accounts(df: pd.DataFrame) -> pd.DataFrame:
    """Optimized validation pipeline"""
    # Vectorized prevalidation
    prevalidated = prevalidate_accounts(df)
    
    # Process only valid accounts through API
    valid_for_api = prevalidated[prevalidated["is_valid"]].copy()
    if not valid_for_api.empty:
        api_validated = validate_bulk_accounts(valid_for_api)
        prevalidated.update(api_validated)
    
    return prevalidated

def save_validation_results(results: pd.DataFrame):
    """Save results with proper type conversion"""
    # Convert datetime for CSV output
    results = results.copy()
    if "Transaction_Date" in results:
        results["Transaction_Date"] = results["Transaction_Date"].dt.strftime(DATE_FORMAT)
    
    # Save files
    valid_accounts = results[results["is_valid"]]
    invalid_accounts = results[~results["is_valid"]]
    
    valid_accounts.to_csv("valid_accounts.csv", index=False)
    invalid_accounts.to_csv("invalid_accounts.csv", index=False)
    
    return valid_accounts, invalid_accounts

if __name__ == "__main__":
    # Load data with optimized reading
    df = pd.read_csv("Bank_Transaction_Fraud_Detection.csv", parse_dates=["Transaction_Date"], dayfirst=True)
    
    
    # Validate accounts
    validation_results = validate_accounts(df)
    
    # Save and report results
    valid, invalid = save_validation_results(validation_results)
    
    print(f"Total accounts processed: {len(validation_results)}")
    print(f"Valid accounts: {len(valid)}")
    print(f"Invalid accounts: {len(invalid)}")
    print("\nTop error reasons for invalid accounts:")
    print(invalid["reason"].value_counts().to_string())