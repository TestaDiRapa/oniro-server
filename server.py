from flask import Flask, jsonify, request, make_response
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_claims
from flask_pymongo import PyMongo
from passlib.hash import pbkdf2_sha256 as sha256
from utils import error_message

app = Flask(__name__)

# Initialize mongo client
with open("/root/oniro-server/mongourl.secret") as url_file:
    app.config["MONGO_URI"] = url_file.read()[:-1]
    mongo = PyMongo(app)

# Initialize JWT
with open("/root/oniro-server/jwt.secret") as key_file:
    app.config["JWT_SECRET_KEY"] = key_file.read()[:-1]
    jwt = JWTManager(app)


@jwt.user_claims_loader
def add_claims_to_access_token(data):
    return {
        "identity": data["username"],
        "type": data["type"]
    }


@app.route('/login/<string:user_type>', methods=['GET'])
def login(user_type):
    if user_type != "user" and user_type != "doctor":
        return make_response("error", 404)

    params = request.get_json(silent=True)
    if params is None:
        return error_message("wrong parameters")

    if "cf" not in params or "password" not in params:
        return error_message("username and password are mandatory fields!")

    try:
        user = mongo.db[user_type+"s"].find_one({"_id": params["cf"]})

        if user is None:
            return error_message("user doesn't exists!")

        pwd = user["password"]
        if not sha256.verify(params["password"], pwd):
            return error_message("password is not correct")

        access_token = create_access_token({"username": params["cf"], "type": "user"})
        return jsonify(status="ok", access_token=access_token)

    except:
        return make_response("error", 500)


@app.route("/register/user", methods=['PUT'])
def register_user():
    json_data = request.get_json(silent=True, cache=False)
    if json_data is None:
        return error_message("mime type not accepted")

    fields = ["cf", "name", "surname", "age", "email", "password", "phone_number"]

    for field in fields:
        if field not in json_data:
            return error_message(field + " is a mandatory field")

    try:
        if mongo.db.users.find_one({'_id': json_data["cf"]}) is not None:
            return error_message("a user with this CF already exists!")

        mongo.db.users.insert_one(
            {
                "_id": json_data["cf"],
                "email": json_data["email"],
                "password": sha256.hash(json_data["password"]),
                "name": json_data["name"],
                "surname": json_data["surname"],
                "age": json_data["age"],
                "phone_server": json_data["phone_number"]
            }
        )

        access_token = create_access_token({"username": json_data["cf"], "type": "user"})
        return jsonify(status="ok", access_token=access_token)

    except:
        return make_response("error", 500)


@app.route("/register/doctor", methods=['PUT'])
def register_doctor():
    json_data = request.get_json(silent=True, cache=False)
    if json_data is None:
        return error_message("mime type not accepted")

    fields = ["id", "email", "password", "name", "surname", "address"]

    for field in fields:
        if field not in json_data:
            return error_message(field + " is a mandatory field")

    try:
        if mongo.db.doctors.find_one({'_id': json_data["id"]}) is not None:
            return error_message("a user with this id already exists!")

        mongo.db.users.insert_one(
            {
                "_id": json_data["if"],
                "email": json_data["email"],
                "password": sha256.hash(json_data["password"]),
                "name": json_data["name"],
                "surname": json_data["surname"],
                "address": json_data["address"],
                "patients": [],
                "patient_requests": []
            }
        )

        access_token = create_access_token({"username": json_data["cf"], "type": "doctor"})
        return jsonify(status="ok", access_token=access_token)

    except:
        return make_response("error", 500)


@app.route("/user/subscribe_to_doctor", methods=['POST'])
@jwt_required
def subscribe_to_doctor():
    params = request.get_json(silent=True, cache=False)
    claims = get_jwt_claims()
    if claims["type"] != "user":
        return error_message("only users can subscribe to doctors!")

    if "doctor_id" not in params:
        return error_message("doctor id is a mandatory parameter")

    try:
        result = mongo.db.doctors.find_one({'_id': params["doctor_id"]})

        if result is None:
            return error_message("this doctor doesn't exists!")

        elif claims["username"] in result["patients"]:
            return error_message("already a patient of this doctor")

        elif claims["username"] in result["patient_requests"]:
            return error_message("already sent a message to this doctor")

        mongo.db.doctors.update_one(
            {
                "_id": params["doctor_id"]
            },
            {
                "$push": {"patient_requests": claims["username"]}
            }
        )

        return jsonify(status="ok")

    except:
        return make_response("error", 500)


if __name__ == "__main__":
    app.run('0.0.0.0', 8080)
