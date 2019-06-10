from flask import jsonify
from utils import error_message
from datetime import datetime


def my_recordings_put(params, claims, mongo):

    mongo.db["record"].insert_one({
        '_id': datetime.now().timestamp(),
        'pay': params
    })

    if claims["type"] != "user":
        return error_message("only users can send recordings")

    fields = {"spo2", "hr", "raw_hr"}

    for field in fields:
        if field not in params:
            return error_message("malformed data packet, " + field + " missing!")

    if "timestamp" not in params:
        return error_message("timestamp is a mandatory parameter!")

    update = {
                "type": "recording",
                "$push":
                {
                    "spo2": params["spo2"],
                    "hr": params["hr"],
                    "raw_hr": {"$each": params["hr_raw"]}
                }
            }

    if "oxy_events" in params and params["oxy_events"] is not None:
        update["$push"]["oxy_events"] = params["oxy_events"]

    if "dia_events" and params["dia_events"] is not None:
        update["$push"]["dia_events"] = params["dia_events"]

    try:
        mongo.db[claims["identity"]].find_one_and_update(
            {
                "_id": params["timestamp"]
            },
            update,
            upsert=True
        )

        return jsonify(status="ok")

    except Exception as e:
        return error_message(str(e))
