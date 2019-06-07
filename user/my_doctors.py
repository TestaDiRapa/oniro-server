from flask import jsonify, make_response
from utils import error_message


def my_doctors_delete(doctor_id, claims, mongo):
    if doctor_id is None:
        return error_message("doctor_id is a mandatory field")

    if claims["type"] != "user":
        return error_message("only users can delete a their subscription to a doctor!")

    try:
        doctor = mongo.db.doctors.find_one({'_id': doctor_id})
        if doctor is None:
            return error_message("doctor does not exists!")

        if claims["identity"] not in doctor["patients"] and claims["identity"] not in doctor["patient_requests"]:
            return error_message("you are not subscribed or asked for subscription to this doctor")

        mongo.db.doctors.update_one(
            {
                '_id': doctor_id
            },
            {
                "$pull": {"patients": claims["identity"]}
            }
        )
        mongo.db.doctors.update_one(
            {
                '_id': doctor_id
            },
            {
                "$pull": {"patient_requests": claims["identity"]}
            }
        )

        return jsonify(status="ok")

    except Exception as e:
        return make_response(str(e), 500)


def my_doctors_get(claims, mongo):
    if claims["type"] != "user":
        return error_message("only users can subscribe to doctors!")

    try:
        results = []
        for document in mongo.db.doctors.find({'patients': claims["identity"]}):
            tmp_dict = {}
            for key in document:
                if key != "password":
                    tmp_dict[key] = document[key]
            results.append({
                "doctor": tmp_dict,
                "type": "subscribed"
            })

        for document in mongo.db.doctors.find({'patient_requests': claims["identity"]}):
            tmp_dict = {}
            for key in document:
                if key != "password":
                    tmp_dict[key] = document[key]
            results.append({
                "doctor": tmp_dict,
                "type": "requested"
            })

        return jsonify(status="ok", message=results)

    except Exception as e:
        return make_response(str(e), 500)


def my_doctors_post(params, claims, mongo):
    if params is None:
        return error_message("mime type not accepted")

    if claims["type"] != "user":
        return error_message("only users can subscribe to doctors!")

    if "doctor_id" not in params:
        return error_message("doctor id is a mandatory parameter")

    try:
        doctor = mongo.db.doctors.find_one({'_id': params["doctor_id"]})

        if doctor is None:
            return error_message("this doctor does not exists!")

        elif claims["identity"] in doctor["patients"]:
            return error_message("already a patient of this doctor")

        elif claims["identity"] in doctor["patient_requests"]:
            return error_message("already sent a message to this doctor")

        mongo.db.doctors.update_one(
            {
                "_id": params["doctor_id"]
            },
            {
                "$push": {"patient_requests": claims["identity"]}
            }
        )

        return jsonify(status="ok")

    except Exception as e:
        return make_response(str(e), 500)