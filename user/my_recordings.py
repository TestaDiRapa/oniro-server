from flask import jsonify
from commons.utils import error_message


def processing(rec_id, claims, mongo):

    if claims["type"] != "user":
        return error_message("only users can access their recordings!")

    user = claims["identity"]

    if rec_id is None:
        return error_message("id is a mandatory parameter!")

    try:
        record = mongo.db[user].find_one({"_id": rec_id})

        if record is None:
            return error_message("no records with the specified id!")

        spo2_rate = 4



    except Exception as e:
        return error_message(str(e))


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
                    "$set": {"type": "recording"},
                    "$push":
                    {
                        "spo2": json["spo2"],
                        "hr": json["hr"],
                        "raw_hr": {"$each": json["raw_hr"]}
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
