from flask import jsonify
from utils import error_message


def me_get(claims, mongo):
    collection = "users"
    if claims["type"] == "doctor":
        collection = "doctors"

    try:
        document = mongo.db[collection].find_one({"_id": claims["identity"]})
        ret = {}

        for key in document:
            if key != "_id" and key != "password":
                ret[key] = document[key]

        return jsonify(status="ok", payload=ret)

    except Exception as e:
        return error_message(str(e), 500)


def me_post(params, claims, mongo):
    return error_message("NOT IMPLEMENTED", 500)
