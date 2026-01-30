import os
import base64

import requests
from datetime import datetime


def get_access_token():

    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    # Create authorization header by encoding consumer key and secret
    auth_str = (
        f"{os.environ['MPESA_CONSUMER_KEY']}:{os.environ['MPESA_CONSUMER_SECRET']}"
    )
    encoded_auth = base64.b64encode(auth_str.encode()).decode("utf-8")
    print("auth", encoded_auth)
    headers = {"Authorization": f"Basic {encoded_auth}"}
    print(url)

    # Make the request to get access token
    try:
        response = requests.get(url, headers=headers)
        print(response.json())
        response.raise_for_status()  # Raise exception for 4XX/5XX errors

        # Parse response
        data = response.json()

        # Calculate token expiry time (typically 1 hour)
        # The expires_in value from API is in seconds

        return {"access_token": data["access_token"], "expires_at": 3600}

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to get M-Pesa access token: {str(e)}")


def send_payment_request(access_token, amount, phone_number, callback_url):
    # Validate and format phone number
    if not phone_number.startswith("254"):
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        elif phone_number.startswith("+254"):
            phone_number = phone_number[1:]
        elif phone_number.startswith("7") or phone_number.startswith("1"):
            phone_number = "254" + phone_number

    # Validate phone number length
    if len(phone_number) != 12:
        raise ValueError(
            f"Invalid phone number format: {phone_number}. Expected 12 digits starting with 254"
        )

    # Validate amount
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError(f"Invalid amount: {amount}. Must be a positive number")

    # Generate timestamp in YYYYMMDDHHMMSS format
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    password_string = (
        f"{os.environ['MPESA_SHORT_CODE']}{os.environ['MPESA_PASSKEY']}{timestamp}"
    )
    password_base64 = base64.b64encode(password_string.encode()).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "BusinessShortCode": os.environ["MPESA_SHORT_CODE"],
        "Password": password_base64,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),  # Ensure amount is integer
        "PartyA": phone_number,
        "PartyB": os.environ["MPESA_SHORT_CODE"],
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": "Payment",  # More descriptive reference
        "TransactionDesc": "Payment for services",  # More descriptive description
    }

    try:
        response = requests.post(
            url="https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
            headers=headers,
            json=payload,
        )

        print("M-Pesa STK Push Response:", response.text)

        # Check if response is successful before raising for status
        if response.status_code == 400:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("errorMessage", "Bad Request")
            raise Exception(f"M-Pesa API Error (400): {error_msg}")

        response.raise_for_status()  # Raise exception for other 4XX/5XX errors
        return response.json()

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to send M-Pesa payment request: {str(e)}")
    except ValueError as e:
        raise Exception(f"Invalid request data: {str(e)}")
