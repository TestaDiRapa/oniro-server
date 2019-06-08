from flask import jsonify
from passlib.hash import pbkdf2_sha256 as sha256
from utils import error_message
import requests


def me_get(claims, mongo):
    collection = "users"
    if claims["type"] == "doctor":
        collection = "doctors"

    try:
        document = mongo.db[collection].find_one({"_id": claims["identity"]})
        ret = {}

        for key in document:
            if key != "password":
                ret[key] = document[key]

        return jsonify(status="ok", message=ret)

    except Exception as e:
        return error_message(str(e), 500)


def me_post(params, claims, mongo, image=None):

    collection = "users"
    fields = ["age", "phone_number"]

    if claims["type"] == "doctor":
        collection = "doctors"
        fields = ["address", "phone"]

    update = dict()

    if image is not None:
        files = {"file": image.read()}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        r = requests.post(url="http://localhost:8082/mediaserver/"+claims["identity"], files=files, headers=headers)

        if r.status_code != 200:
            return error_message("error in media server, code: " + str(r.status_code))

        elif r.json()["status"] == "error":
            return error_message("error in media server, message: " + r.json()["message"])

        else:
            update["profile_picture"] = r.json()["path"]

    try:
        if "old_password" in params and "new_password" in params:
            document = mongo.db[collection].find_one({'_id': claims["identity"]})

            if document is not None and sha256.verify(params["old_password"], document["password"]):
                update["password"] = sha256.hash(params["new_password"])

        for field in fields:
            if field in params:
                update[field] = params[field]

        if update:
            mongo.db[collection].find_one_and_update(
                {
                    "_id": claims["identity"]
                },
                {
                    "$set": update
                }
            )

            return jsonify(status="ok")

        else:
            return error_message("no data provided!")

    except Exception as e:
        return error_message(str(e))

