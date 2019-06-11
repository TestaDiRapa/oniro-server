from flask import jsonify
from utils import error_message


def my_recordings_put(params, claims, mongo):

    if claims["type"] != "user":
        return error_message("only users can send recordings")

    fields = {"spo2", "hr", "raw_hr"}

    for json in params:
        for field in fields:
            if field not in json:
                return error_message("malformed data packet, " + field + " missing!")

        if "timestamp" not in json:
            return error_message("timestamp is a mandatory parameter!")

        update = {
                    "$set": {
                        "type": "recording",
                        "spo2_rate": json["spo2_rate"],
                        "hr_rate": json["hr_rate"],
                        "raw_hr_rate": json["raw_hr_rate"]
                    },
                    "$push":
                    {
                        "spo2": json["spo2"],
                        "hr": json["hr"],
                        "raw_hr": {"$each": json["raw_hr"]},
                        "movement_count": json["movement_count"]
                    }
                }

        if "oxy_event" in json and json["oxy_event"] is not None:
            update["$push"]["oxy_events"] = json["oxy_event"]

        if "dia_event" in json and json["dia_event"] is not None:
            update["$push"]["dia_events"] = json["dia_event"]

        try:
            mongo.db[claims["identity"]].find_one_and_update(
                {
                    "_id": json["timestamp"]
                },
                update,
                upsert=True
            )

        except Exception as e:
            return error_message(str(e))

    return jsonify(status="ok")
