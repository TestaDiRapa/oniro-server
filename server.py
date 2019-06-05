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
