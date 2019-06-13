from flask import jsonify
from commons.utils import error_message, prepare_packet


def send_to_doctor(params, claims, mongo):

    if claims["type"] != "user":
        return error_message("only users can send requests to doctors")

    if "id" not in params:
        return error_message("id is a mandatory field!")

    if "doctor" not in params:
        return error_message("doctor is a mandatory field!")

    try:

        doc = mongo.db.doctors.find_one({"_id": params["doctor"]})

        if doc is None:
            return error_message("doctor does not exists!")

        mongo.db.doctors.find_one_and_update(
            {
                "_id": params["doctor"]
            },
            {
                "$push": {
                    "signals": {
                        "cf": claims["identity"],
                        "id": params["id"]
                    }
                }
            }
        )

        return jsonify(status="ok")

    except Exception as e:
        return error_message(str(e))


def my_recordings_get(identifier, cf, claims, mongo):

    if claims["type"] == "doctor":
        if cf is None:
            return error_message("user is a mandatory parameter!")

        try:
            doc = mongo.db.doctors.find_one({'_id': claims["identity"]})

            if doc is None:
                return error_message("doctor is not registered!")

            if cf not in doc["patients"]:
                return error_message("patient not registered!")

            user = cf

        except Exception as e:
            return error_message(str(e))

    else:
        user = claims["identity"]

    if identifier is None:
        try:
            ret = []

            for document in mongo.db[user].find({"type": "recording"}, {"preview": 1}):

                ret.append(document)

            return jsonify(status="ok", payload=ret)

        except Exception as e:
            return error_message(str(e))

    else:
        try:
            doc = mongo.db[user].find_one({"_id": identifier})

            if doc is None:
                return error_message("recording does not exists!")

            return jsonify(status="ok", payload=doc["aggregate"])

        except Exception as e:
            return error_message(str(e))


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

        aggregate, preview = prepare_packet(record)

        mongo.db[user].find_one_and_update(
            {
                "_id": rec_id,
            },
            {
                "$set": {
                    "aggregate": aggregate,
                    "preview": preview
                }
            }
        )

        return jsonify(status="ok")

    except Exception as e:
        return error_message(str(e))


def my_recordings_put(params, claims, mongo):

    if claims["type"] != "user":
        return error_message("only users can send recordings")

    fields = {"spo2", "hr"}

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
                    },
                    "$push":
                    {
                        "spo2": json["spo2"],
                        "hr": json["hr"],
                        "movements_count": json["movements_count"]
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
