from flask import jsonify
from commons.utils import aggregate_apnea_events, error_message, interval_avg, spectral_analysis
from statistics import mean


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

            for document in mongo.db[user].find({"type": "preview"}):
                ret.append(document)

            return jsonify(status="ok", payload=ret)

        except Exception as e:
            return error_message(str(e))

    else:
        try:
            doc = mongo.db[user].find({"_id": identifier})

            if doc is None:
                return error_message("recording does not exists!")

            return jsonify(status="ok", payload=doc)

        except Exception as e:
            return error_message(str(e))


def processing(rec_id, claims, mongo):

    if claims["type"] != "user":
        return error_message("only users can access their recordings!")

    user = claims["identity"]

    if rec_id is None:
        return error_message("id is a mandatory parameter!")

    aggregate = dict()
    preview = dict()

    try:
        record = mongo.db[user].find_one({"_id": rec_id})

        if record is None:
            return error_message("no records with the specified id!")

        aggregate["_id"] = rec_id + "A"
        aggregate["date"] = rec_id
        aggregate["type"] = "aggregate"

        preview["_id"] = rec_id + "P"
        preview["date"] = rec_id
        preview["type"] = "preview"

        aggregate["avg_spo2"] = mean(record["spo2"])
        aggregate["plot_spo2"] = interval_avg(record["spo2"], record["spo2_rate"], 60)

        preview["avg_spo2"] = aggregate["avg_spo2"]

        aggregate["avg_hr"] = mean(record["hr"])
        aggregate["plot_hr"] = interval_avg(record["hr"], record["hr_rate"], 60)

        preview["avg_hr"] = aggregate["avg_hr"]

        aggregate["total_movements"] = sum(record["movements_count"])
        aggregate["plot_movements"] = record["movements_count"]

        f, ps = spectral_analysis(record["spo2"], record["spo2_rate"])

        aggregate["spo2_spectra"] = {
            "frequencies": f,
            "spectral_density": ps
        }

        f, ps = spectral_analysis(record["raw_hr"], record["raw_hr_rate"])

        aggregate["hr_spectra"] = {
            "frequencies": f,
            "spectral_density": ps
        }

        apnea_events = aggregate_apnea_events(record["oxy_events"], record["dia_events"])
        avg = 0
        for event in apnea_events:
            avg += event["duration"]
        avg = avg // len(apnea_events)

        aggregate["apnea_events"] = len(apnea_events)
        aggregate["avg_duration"] = avg
        aggregate["plot_apnea_events"] = apnea_events

        preview["apnea_events"] = len(apnea_events)

        mongo.db[user].insert_one(preview)
        mongo.db[user].insert_one(aggregate)

        return jsonify(status="ok")

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
