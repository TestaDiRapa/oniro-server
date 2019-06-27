from flask import jsonify
from passlib.hash import pbkdf2_sha256 as sha256
from commons.utils import error_message
import base64
import requests


'''
Returns a list containing all the doctors' addresses
'''
def coordinates_get(mongo):
    try:
        response = []
        for x in mongo.db.doctors.find({}, {"name": 1, "surname": 1, "address": 1}):
            response.append((
                {
                    "doctor": x  # vuoto
                }
            ))
        if len(response) == 0:
            return error_message("empty list!")
        return jsonify(status='ok', payload=response)

    except Exception as e:
        return error_message(str(e))


'''
This method retrieves the data of a user from the database service basing on the claims from the authentication token.
It returns the user or an error message in a JSON format.
'''
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


'''
This method allow changing the data related to the user. It can modify more than one datum at time. If an image file is
passed, then it's sent to the media server.
It returns a success message or an error message to the media server.
'''
def me_post(params, claims, mongo, file):

    collection = "users"
    fields = ["age", "phone_number"]

    if claims["type"] == "doctor":
        collection = "doctors"
        fields = ["address", "phone_number"]

    update = dict()

    image_path = ""

    if "image" in params and file is not None:
        return error_message("two images provided!")

    if "image" in params:

        formatted_string = params["image"].split(',')[1]

        formatted_string += "=" * (4 - len(formatted_string) % 4)

        image = base64.b64decode(formatted_string)

        files = {"file": ("image.png", image)}

    if file is not None:

        files = {"file": ("image.png", file)}

    if file is not None or "image" in params:

        payload = {"user": claims["identity"]}
        r = requests.post("http://localhost:8082/mediaserver", files=files, data=payload)

        if r.status_code != 200:
            return error_message("error in media server, code: " + str(r.status_code))

        elif r.json()["status"] == "error":
            return error_message("error in media server, message: " + r.json()["message"])

        else:
            update["profile_picture"] = r.json()["path"]
            image_path = r.json()["path"]

    try:
        if "old_password" in params and "new_password" in params:
            document = mongo.db[collection].find_one({'_id': claims["identity"]})

            if document is not None:
                if sha256.verify(params["old_password"], document["password"]):
                    update["password"] = sha256.hash(params["new_password"])
                else:
                    return error_message("password is not correct")

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

            return jsonify(status="ok", message=image_path)

        else:
            return error_message("no data provided!")

    except Exception as e:
        return error_message(str(e))

