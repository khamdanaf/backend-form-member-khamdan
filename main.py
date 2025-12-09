import os
import json
import logging
import random
from datetime import datetime, timezone
from hmac import compare_digest
from functools import wraps

from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource

from components import custom, write_to_bq

# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:/Backup Working Laptop 2025/Pointstar/MAP Active/Freelance/Clarinerv/butter-baby-playground-96243a8db684.json'

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(
    format="%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.INFO,
)

API_KEY = os.environ.get("API_KEY", "VdiQrabt/qVgrKPtvUgWNAaN8XVnTxrQJ6G0X0WApfo=")
PROJECT_ID = os.environ.get("PROJECT_ID", "butter-baby-playground")
DATASET_ID = os.environ.get("DATASET_ID", "bb_digital_sandbox")
TABLE_ID_JOIN_MEMBER = os.environ.get("TABLE_ID_JOIN_MEMBER", "bb_form_member")

app = Flask(__name__)
api = Api(app)
app.config["auth-key"] = API_KEY
app.config["JSON_SORT_KEYS"] = False

# Simple in-memory OTP storage per WhatsApp number
otp_store = {}


def is_valid(api_key, api_key_validator):
    if api_key and compare_digest(api_key, api_key_validator):
        return True


def api_key_required(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        logging.info("Checking API credentials...")
        if request.headers.get("auth-key"):
            logging.info("API key found in the headers request")
            api_key = request.headers.get("auth-key")
        else:
            logging.error("No API key found in the headers request")
            return {"message": "No API key found in request"}, 400

        if request.method in ["GET", "POST"] and is_valid(api_key, app.config["auth-key"]):
            logging.info("API key and method is valid")
            return func(*args, **kwargs)
        else:
            logging.error(
                f"API key and method is invalid: "
                f"[API Method - {request.method}, API Key - {api_key}]"
            )
            return {"message": "Invalid authentication credentials"}, 403

    return decorator


# ---------------------------------------------------------------------------
# /v1/auth  (test endpoint)
# ---------------------------------------------------------------------------
class apiResourceTestAuth(Resource):
    @api_key_required
    def get(self):
        logging.info("Running GET /v1/auth...")
        identity = {"statusCode": 200, "status": True, "message": "Successfully execute auth..."}
        try:
            request_json_body = request.get_json(silent=True)
            request_parameter_1 = request.args.get("firstParamenter", default=None, type=str)
            request_parameter_2 = request.args.get("secondParamenter", default=None, type=str)
            logging.info(f"JSON Body: {request_json_body}")
            logging.info(f"Parameter value for firstParamenter: {request_parameter_1}")
            logging.info(f"Parameter value for secondParamenter: {request_parameter_2}")

            identity["data"] = {
                "jsonBody": request_json_body,
                "firstParamenter": request_parameter_1,
                "secondParamenter": request_parameter_2,
            }
            logging.info(f"API Response GET /v1/auth: {identity}")
            return make_response(jsonify(identity), identity["statusCode"])
        except Exception as error:
            identity["statusCode"] = 500
            identity["status"] = False
            identity["message"] = f"Internal error: {error}"
            logging.error(f"API Response GET /v1/auth: {identity}")
            return make_response(jsonify(identity), identity["statusCode"])


# ---------------------------------------------------------------------------
# /v1/whatsapp/otp  (generate & "send" OTP ke nomor WA)
# ---------------------------------------------------------------------------
class apiResourceSendWhatsAppOTP(Resource):
    @api_key_required
    def get(self):
        """
        This function will implement WhatsApp OTP confirmation to the user.
        Users have to verify the code they received and fill the code to the Form Member UI.
        """
        logging.info("Running GET /v1/whatsapp/otp...")
        identity = {
            "statusCode": 200,
            "status": True,
            "message": "Successfully running GET /v1/whatsapp/otp...",
        }
        try:
            request_json_body = request.get_json(silent=True)
            phone = request.args.get("phone", default=None, type=str)

            logging.info(f"JSON Body (if any): {request_json_body}")
            logging.info(f"Parameter value for phone: {phone}")

            if not phone:
                identity["statusCode"] = 400
                identity["status"] = False
                identity["message"] = "Parameter 'phone' is required"
                logging.error("Missing 'phone' parameter on /v1/whatsapp/otp")
                return make_response(jsonify(identity), identity["statusCode"])

            # Try custom OTP generator if exists
            otp_code = None
            try:
                if hasattr(custom, "generate_otp") and callable(custom.generate_otp):
                    otp_code = str(custom.generate_otp())
                    logging.info(f"OTP generated using custom.generate_otp(): {otp_code}")
            except Exception as e:
                logging.warning(f"Failed to use custom.generate_otp(): {e}")

            # Fallback: random 4-digit OTP
            if not otp_code:
                otp_code = f"{random.randint(1000, 9999)}"
                logging.info(f"OTP generated using fallback random: {otp_code}")

            # Save OTP in memory
            otp_store[phone] = {
                "otp": otp_code,
                "generatedAt": datetime.now(timezone.utc).isoformat(),
            }

            # TODO: in production, replace this with actual WhatsApp provider API call
            logging.info(f"[SIMULATION] Sending WhatsApp OTP {otp_code} to {phone}")

            identity["data"] = {
                "phone": phone,
                "generatedAt": otp_store[phone]["generatedAt"],
                "note": "OTP generated. In dev environment, check backend log to see the code.",
            }

            logging.info(f"API Response GET /v1/whatsapp/otp: {identity}")
            return make_response(jsonify(identity), identity["statusCode"])
        except Exception as error:
            identity["statusCode"] = 500
            identity["status"] = False
            identity["message"] = f"Internal error: {error}"
            logging.error(f"API Response GET /v1/whatsapp/otp: {identity}")
            return make_response(jsonify(identity), identity["statusCode"])


# ---------------------------------------------------------------------------
# /v1/member/new  (insert member ke BigQuery: bb_form_member)
# ---------------------------------------------------------------------------
class apiResourceAddMemberToBigQuery(Resource):
    @api_key_required
    def post(self):
        """
        Save the user's data from Form Member UI into Google BigQuery.
        Target table schema:
          - customer_name       STRING
          - customer_email      STRING
          - customer_birthday   DATE
          - customer_phone_num  STRING
          - signup_location     STRING
          - marketing_channel   REPEATED STRING
          - insertedAtBQ        DATETIME
        """
        logging.info("Running POST /v1/member/new...")
        identity = {
            "statusCode": 200,
            "status": True,
            "message": "Successfully running POST /v1/member/new...",
        }

        try:
            request_json_body = request.get_json(silent=True) or {}
            logging.info(f"JSON Body POST /v1/member/new: {request_json_body}")

            # Optional: OTP verification if FE sends 'otp' + phone
            phone_from_body = (
                request_json_body.get("customer_phone_num")
                or request_json_body.get("phone")
                or request_json_body.get("whatsapp_number")
            )
            otp_from_request = request_json_body.get("otp")

            if otp_from_request and phone_from_body:
                saved = otp_store.get(phone_from_body)
                if not saved:
                    identity["statusCode"] = 400
                    identity["status"] = False
                    identity["message"] = "OTP session not found for this phone"
                    logging.error(f"OTP session not found for phone: {phone_from_body}")
                    return make_response(jsonify(identity), identity["statusCode"])

                if str(saved["otp"]) != str(otp_from_request):
                    identity["statusCode"] = 400
                    identity["status"] = False
                    identity["message"] = "Invalid OTP code"
                    logging.error(
                        f"Invalid OTP: expected {saved['otp']} "
                        f"but got {otp_from_request} for phone {phone_from_body}"
                    )
                    return make_response(jsonify(identity), identity["statusCode"])

                logging.info(f"OTP verification success for phone {phone_from_body}")
                # Optional: clear OTP after success
                otp_store.pop(phone_from_body, None)

            # Transform payload → BigQuery row
            bq_row = custom.transform_member_payload(request_json_body)

            # Minimal validation
            if not bq_row["customer_name"] or not bq_row["customer_phone_num"]:
                identity["statusCode"] = 400
                identity["status"] = False
                identity["message"] = "customer_name and customer_phone_num are required."
                logging.error(f"Validation error /v1/member/new: {identity}")
                return make_response(jsonify(identity), identity["statusCode"])

            # Write to BigQuery
            write_to_bq.insert_member_row(
                PROJECT_ID,
                DATASET_ID,
                TABLE_ID_JOIN_MEMBER,
                bq_row,
            )

            identity["data"] = bq_row
            identity["message"] = (
                "Member data successfully written to BigQuery (bb_form_member)."
            )
            logging.info(f"API Response POST /v1/member/new: {identity}")
            return make_response(jsonify(identity), identity["statusCode"])

        except Exception as error:
            identity["statusCode"] = 500
            identity["status"] = False
            identity["message"] = f"Internal error: {error}"
            logging.error(f"API Response POST /v1/member/new: {identity}")
            return make_response(jsonify(identity), identity["statusCode"])


# ---------------------------------------------------------------------------
# Register resources
# ---------------------------------------------------------------------------
api.add_resource(apiResourceTestAuth, "/v1/auth", methods=["GET"])
api.add_resource(apiResourceAddMemberToBigQuery, "/v1/member/new", methods=["POST"])
api.add_resource(apiResourceSendWhatsAppOTP, "/v1/whatsapp/otp", methods=["GET"])


if __name__ == "__main__":
    app.run("0.0.0.0", debug=True, port=int(os.environ.get("PORT", 8080)))
