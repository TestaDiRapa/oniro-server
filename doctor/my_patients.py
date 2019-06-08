from flask import jsonify, make_response
from utils import error_message


def my_patients_delete(patient_cf, claims, mongo):
    if patient_cf is None:
        return error_message("patient_cf is a mandatory field")

    if claims["type"] != "doctor":
        return error_message("only a doctor can remove a patient!")

    try:
        doctor = mongo.db.doctors.find_one({'_id': claims["identity"]})

        if patient_cf not in doctor["patients"] and patient_cf not in doctor["patient_requests"]:
            return error_message("this patient is not subscribed nor asked for subscription")

        mongo.db.doctors.update_one(
            {
                "_id": claims["identity"]
            },
            {
                "$pull": {
                    "patients": patient_cf,
                    "patient_requests": patient_cf
                }
            }
        )

        return jsonify(status="ok")

    except Exception as e:
        return make_response(str(e), 500)


def my_patients_get(claims, mongo):
    if claims["type"] != "doctor":
        return error_message("only doctors can see their patients!")

    try:
        results = []
        doctor = mongo.db.doctors.find_one({'_id': claims["identity"]})

        for value in doctor["patients"]:
            results.append(
                {
                    "patient": value,
                    "type": "registered"
                }
            )

        for value in doctor["patient_requests"]:
            results.append((
                {
                    "patient": value,
                    "type": "request"
                }
            ))

        return jsonify(status="ok", results=results)

    except Exception as e:
        return make_response(str(e), 500)


def my_patients_post(params, claims, mongo):
    if params is None:
        return error_message("mime type not accepted")

    if claims["type"] != "doctor":
        return error_message("only doctors are allowed to accept patients!")

    if "user_cf" not in params:
        return error_message("user_cf is a mandatory parameter")

    try:
        user = mongo.db.users.find_one({'_id': params["user_cf"]})
        if user is None:
            return error_message("user does not exists")

        doctor = mongo.db.doctors.find_one({'_id': claims["identity"]})

        if doctor is None:
            return error_message("doctor does not exists")

        if params["user_cf"] in doctor["patients"]:
            return error_message("patient already accepted")

        if params["user_cf"] not in doctor["patient_requests"]:
            return error_message("patient did not sent a request")

        mongo.db.doctors.update_one(
            {
                "_id": claims["identity"]
            },
            {
                "$pull": {"patient_requests": params["user_cf"]},
                "$push": {"patients": params["user_cf"]}
            }
        )

        return jsonify(status="ok")

    except Exception as e:
        return make_response(str(e), 500)