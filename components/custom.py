from datetime import datetime
import logging


def transform_member_payload(request_json: dict) -> dict:
    """
    Transform JSON dari form → 1 row siap kirim ke BigQuery.
    Schema:
      - customer_name        STRING
      - customer_email       STRING
      - customer_birthday    DATE (YYYY-MM-DD)
      - customer_phone_num   STRING
      - signup_location      STRING
      - marketing_channel    REPEATED STRING (list)
      - insertedAtBQ         DATETIME (YYYY-MM-DD HH:MM:SS)
    """

    logging.info(f"Raw JSON from request: {request_json}")

    customer_name = (
        request_json.get("customer_name")
        or request_json.get("name")
    )

    customer_email = (
        request_json.get("customer_email")
        or request_json.get("email")
    )

    customer_birthday = (
        request_json.get("customer_birthday")
        or request_json.get("dateOfBirth")
        or request_json.get("dob")
    )

    customer_phone_num = (
        request_json.get("customer_phone_num")
        or request_json.get("phone")
        or request_json.get("whatsapp_number")
    )

    signup_location = request_json.get("signup_location")

    marketing_channel_raw = request_json.get("marketing_channel")

    if isinstance(marketing_channel_raw, list):
        marketing_channel = [str(ch).strip() for ch in marketing_channel_raw if ch]
    elif isinstance(marketing_channel_raw, str):
        marketing_channel = [
            part.strip() for part in marketing_channel_raw.split(",") if part.strip()
        ]
    else:
        marketing_channel = []

    inserted_at_bq = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    row = {
        "customer_name": customer_name,
        "customer_email": customer_email,
        "customer_birthday": customer_birthday,
        "customer_phone_num": customer_phone_num,
        "signup_location": signup_location,
        "marketing_channel": marketing_channel,
        "insertedAtBQ": inserted_at_bq,
    }

    logging.info(f"Transformed row for BigQuery: {row}")
    return row
