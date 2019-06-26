from commons.utils import error_message
from flask import jsonify

'''
This method allow a doctor to see all the reports sent from its patients
'''
def my_alerts_get(claims, mongo):

    if claims["type"] != "doctor":
        return error_message("only doctors can see signals!")

    try:
        doc = mongo.db.doctors.find_one({"_id": claims["identity"]})

        if doc is None:
            return error_message("doctor does not exists!")

        return jsonify(status="ok", signals=doc["signals"])

    except Exception as e:
        return error_message(str(e))


'''
This method allow a doctor to delete a report from a patient, given the patient cf and the recording id
'''
def my_alerts_delete(identity, cf, claims, mongo):

    if claims["type"] != "doctor":
        return error_message("only doctors can delete signals!")

    if "id" is None:
        return error_message("id is a mandatory field!")

    if "cf" is None:
        return error_message("cf is a mandatory field!")

    try:

        doc = mongo.db.doctors.find_one({"_id": claims["identity"]})

        if doc is None:
            return error_message("doctor does not exists!")

        mongo.db.doctors.find_one_and_update(
            {
                "_id": claims["identity"]
            },
            {
                "$pull": {
                    "signals": {
                        "cf": cf,
                        "id": identity
                    }
                }
            }
        )

        return jsonify(status="ok")

    except Exception as e:
        return error_message(str(e))
