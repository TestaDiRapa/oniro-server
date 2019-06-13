from commons.utils import error_message
from flask import jsonify


def facts_post(params, mongo):

    if params is None or "fact" not in params:
        return error_message("no fact provided!")

    try:
        mongo.db.facts.insert_one({
            "text": params["fact"]
        })

        return jsonify(status="ok")

    except Exception as e:
        return error_message(str(e))


def facts_get(mongo):

    try:
        facts = []
        for document in mongo.db.facts.find():
            facts.append(document["text"])

        return jsonify(status="ok", payload=facts)

    except Exception as e:
        return error_message(str(e))
