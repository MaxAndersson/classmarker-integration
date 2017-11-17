import json
import hmac
import hashlib
import base64
import os

import lib.certificate as certificate
import lib.neo4j_accounts as accts 

from lib.encryption import decrypt_value


def get_email_lambda(request, context):
    json_payload = json.loads(request["body"])
    user_id = json_payload["user_id"]
    return {"statusCode": 200, "body": accts.get_email_address(user_id), "headers": {}}

def generate_certificate(request, context):
    print("generate_certificate request: {request}".format(request=request))

    json_payload = json.loads(request["body"])
    result = json_payload["result"]

    expected_hmac = request["headers"].get("X-Classmarker-Hmac-Sha256")
    if not expected_hmac:
        raise Exception("No HMAC provided. Request did not come from Classmarker so not generating certificate")

    cm_secret_phrase = decrypt_value(os.environ['CM_SECRET_PHRASE'])

    dig = hmac.new(cm_secret_phrase, msg=request["body"].encode("utf-8"), digestmod=hashlib.sha256).digest()
    generated_hmac = base64.b64encode(dig).decode()

    if expected_hmac != generated_hmac:
        raise Exception("""\
        Generated HMAC did not match the one provided by Classmarker so not generating certificate.
        Expected: {expected}, Actual: {generated}""".format(expected=expected_hmac, generated=generated_hmac))

    event = {
        "user_id": result["link_result_id"],
        "name": "{first} {last}".format(first=result["first"], last=result["last"]),
        "email": accts.get_email_address(result["link_result_id"]),
        "score_percentage": result["percentage"],
        "score_absolute": result["points_scored"],
        "score_maximum": result["points_available"],
        "date": int(result["time_finished"])
    }

    if not result["passed"]:
        print("Not generating certificate for {event}".format(event = event))
        certificate_path = None
    else:
        print("Generating certificate for {event}".format(event = event))
        certificate_path = certificate.generate(event)
        print("Certificate:", certificate_path)

    return {"statusCode": 200, "body": certificate_path, "headers": {}}
