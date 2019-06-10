from flask import jsonify
from utils import error_message


def my_recordings_put(params, claims, mongo):

    if params is None:
        return error_message("No payload sent!")

    if claims["type"] != "user":
        return error_message("only users can send recordings")

    fields = {"spo2", "oxy_events", "dia_events", "hr", "hr_raw"}

    for field in fields:
        if field not in params:
            return error_message("malformed data packet, " + field + " missing!")

    if "timestamp" not in params:
        return error_message("timestamp is a mandatory parameter!")

    try:
        mongo.db[claims["identity"]].find_one_and_update(
            {
                "_id": params["timestamp"]
            },
            {
                "type": "recording",
                "$push":
                {
                    "spo2": {"$each": params["spo2"]},
                    "oxy_events": {"$each": params["oxy_events"]},
                    "dia_events": {"$each": params["dia_events"]},
                    "hr": {"$each": params["hr"]},
                    "hr_raw": {"$each": params["hr_raw"]}
                }
            },
            upsert=True
        )

        return jsonify(status="ok")

    except Exception as e:
        return error_message(str(e))
