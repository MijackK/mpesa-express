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
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": os.environ["MPESA_SHORT_CODE"],
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": "Test",
        "TransactionDesc": "Technology",
    }

    response = requests.post(
        url="https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        headers=headers,
        json=payload,
    )
    print("mpesa response", response.text)
    response.raise_for_status()  # Raise exception for 4XX/5XX errors
    print(response.text.encode("utf8"))

    return response
