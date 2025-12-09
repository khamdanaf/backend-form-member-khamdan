import os
import json
import logging
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
from hmac import compare_digest
from functools import wraps
from components import custom, write_to_bq

# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:/Backup Working Laptop 2025/Pointstar/MAP Active/Freelance/Clarinerv/butter-baby-playground-96243a8db684.json'

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)



API_KEY = os.environ.get("API_KEY", "VdiQrabt/qVgrKPtvUgWNAaN8XVnTxrQJ6G0X0WApfo=")
PROJECT_ID = os.environ.get("PROJECT_ID", "butter-baby-playground")
DATASET_ID = os.environ.get("DATASET_ID", "bb_digital_sandbox")
TABLE_ID_JOIN_MEMBER = os.environ.get("TABLE_ID_JOIN_MEMBER", "bb_form_member")



app = Flask(__name__)
api = Api(app)
app.config['auth-key'] = API_KEY
app.config['JSON_SORT_KEYS'] = False


def is_valid(api_key, api_key_validator):
    if api_key and compare_digest(api_key, api_key_validator):
        return True

def api_key_required(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        logging.info("Checking API credentials...")
        # Check if API key is available in the headers request
        if request.headers.get("auth-key"):
            logging.info("API key found in the headers request")
            api_key = request.headers.get("auth-key")
        else:
            logging.error("No API key found in the headers request")
            return {"message": "No API key found in request"}, 400
        # Check if API key is correct and valid
        if request.method in ["GET","POST"] and is_valid(api_key, app.config['auth-key']):
            logging.info("API key and method is valid")
            return func(*args, **kwargs)
        else:
            logging.error(f"API key and method is invalid: [API Method - {request.method}, API Key - {api_key}]")
            return {"message": "Invalid authentication credentials"}, 403
    return decorator


# Endpoint for Testing
class apiResourceTestAuth(Resource):
    @api_key_required
    def get(self):
        logging.info("Running GET /v1/auth...")
        identity = {"statusCode": 200, "status": True, "message": "Successfully execute auth..."}
        try:
            request_json_body = request.get_json(silent=True)
            request_parameter_1 = request.args.get('firstParamenter', default=None, type=str)
            request_parameter_2 = request.args.get('secondParamenter', default=None, type=str)
            logging.info(f"JSON Body: {request_json_body}")
            logging.info(f"Parameter value for firstParamenter: {request_parameter_1}")
            logging.info(f"Parameter value for secondParamenter: {request_parameter_2}")

            identity['data'] = {}
            identity['data']['jsonBody'] = request_json_body
            identity['data']['firstParamenter'] = request_parameter_1
            identity['data']['secondParamenter'] = request_parameter_2
            logging.info(f"API Response GET /v1/auth: {identity}")
            return make_response(jsonify(identity), identity['statusCode'])
        except Exception as error:
            identity['statusCode'] = 500
            identity['status'] = False
            identity['message'] = f"Internal error: {error}"
            logging.error(f"API Response GET /v1/auth: {identity}")
            return make_response(jsonify(identity), identity['statusCode'])


class apiResourceSendWhatsAppOTP(Resource):
    @api_key_required
    def get(self):
        "This function will implement whatsapp otp confirmation to the user."
        "Users have to verify the code they received and fill the code to the Form Member UI"

        logging.info("Running GET /v1/whatsapp/otp...")
        identity = {"statusCode": 200, "status": True, "message": "Successfully running GET /v1/whatsapp/otp..."}
        try:
            # CODE TO REPLACE
            pass
        except Exception as error:
            identity['statusCode'] = 500
            identity['status'] = False
            identity['message'] = f"Internal error: {error}"
            logging.error(f"API Response GET /v1/whatsapp/otp: {identity}")
            return make_response(jsonify(identity), identity['statusCode'])


class apiResourceAddMemberToBigQuery(Resource):
    @api_key_required
    def post(self):
        "This function will save the user's data they have filled on the Form Member UI."
        "The user's data will be saved in Google BigQuery, with an additional field, i.e insertedBQAt [DATETIME]"
        
        logging.info("Running POST /v1/member/new...")
        identity = {"statusCode": 200, "status": True, "message": "Successfully running POST /v1/member/new..."}
        try:
            # CODE TO REPLACE
            pass
        except Exception as error:
            identity['statusCode'] = 500
            identity['status'] = False
            identity['message'] = f"Internal error: {error}"
            logging.error(f"API Response POST /v1/member/new: {identity}")
            return make_response(jsonify(identity), identity['statusCode'])



api.add_resource(apiResourceTestAuth, "/v1/auth", methods=['GET'])
api.add_resource(apiResourceAddMemberToBigQuery, "/v1/member/new", methods=['POST'])
api.add_resource(apiResourceSendWhatsAppOTP, "/v1/whatsapp/otp", methods=['GET'])


if __name__ == "__main__":
    app.run("0.0.0.0", debug=True, port=int(os.environ.get("PORT", 8080)))