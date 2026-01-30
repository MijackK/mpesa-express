from flask import Flask, request, abort
import traceback
from mpesa.api import get_access_token, send_payment_request
from dotenv import load_dotenv
import json

load_dotenv()

SAFARICOM_CALLBACK_IPS = [
    "196.201.214.200",
    "196.201.214.206",
    "196.201.213.114",
    "196.201.214.207",
    "196.201.214.208",
    "196.201.213.44",
    "196.201.212.127",
    "196.201.212.138",
    "196.201.212.129",
    "196.201.212.136",
    "196.201.212.74",
    "196.201.212.69",
]


def verify_safaricom_callback():
    """Verify that the callback request is from Safaricom's servers"""
    # Get the real client IP (considering proxies/load balancers)
    client_ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
    if client_ip:
        # Take the first IP if there are multiple (comma-separated)
        client_ip = client_ip.split(",")[0].strip()
    print("client_ip:", client_ip)

    return client_ip in SAFARICOM_CALLBACK_IPS


def create_app():
    # create and configure the app
    app = Flask(__name__)

    @app.route("/")
    def index():
        return "Hello, Mpesa!"

    @app.route("/mpesa_express", methods=["POST"])
    def mpesa_express():
        post_data = request.get_json()
        quote = post_data["quote"]
        phone_number = post_data["phone"]

        amount = 1  # For testing purposes, set a fixed amount

        access_response = get_access_token()

        sdk_response = send_payment_request(
            access_token=access_response["access_token"],
            amount=amount,
            phone_number=phone_number,
            callback_url=f"{request.host_url}mpesa_express_callback/{quote}",
        )

        try:
            if sdk_response["ResponseCode"] == "0":
                request_data = json.dumps(sdk_response)
                print("Request Data:", request_data)

            else:
                request_data = json.dumps(sdk_response)
                print("Request Data:", request_data)
            return ""
        except Exception as e:
            traceback.print_exc()
            print("Error: ", e)
            abort(500, description="Transaction update failed")

        return sdk_response["responseDescription"]

    @app.route("/mpesa_express_callback/<quote_id>", methods=["POST"])
    def mpesa_express_callback(quote_id):
        post_data = request.get_json()
        stk_data = post_data.get("Body", {}).get("stkCallback", {})

        if not stk_data or stk_data.get("ResultCode") != 0:

            abort(400, description="Invalid callback data")
        print("MPESA Callback Data:", post_data)
        print("ID:", quote_id)

        return " "

    return app
