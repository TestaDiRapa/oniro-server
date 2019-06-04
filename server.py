from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token
from flask_pymongo import PyMongo
from flask_restful import Api, Resource
from passlib.hash import pbkdf2_sha256 as sha256
from utils import error_message

app = Flask(__name__)
api = Api(app)

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


class UserLogin(Resource):

    def get(self):
        pass


class UserRegister(Resource):

    def put(self):
        json_data = request.get_json(silent=True, cache=False)
        if json_data is None:
            return error_message("mime type not accepted")

        fields = ["cf", "email", "password"]

        for field in fields:
            if field not in json_data:
                return error_message(field + " is a mandatory field")

        try:
            if mongo.db.users.find_one({'_id': json_data["cf"]}) is not None:
                return error_message("A user with this CF already exists!")

            mongo.db.users.insert_one(
                {
                    '_id': json_data['cf'],
                    'email': json_data['email'],
                    # MUST BE VERIFIED WITH sha256.verify(password, hash)
                    'password': sha256.hash(json_data["password"])
                }
            )

            access_token = create_access_token({"username": json_data["cf"], "type": "user"})
            return jsonify(status="ok", payload={"access_token": access_token})

        except:
            return error_message("Error in database connection")


class DoctorLogin(Resource):

    def get(self):
        pass


class DoctorRegister(Resource):

    def put(self):
        pass


api.add_resource(UserLogin, "/login/user")
api.add_resource(UserRegister, "/register/user")
api.add_resource(DoctorLogin, "/login/doctor")
api.add_resource(DoctorRegister, "/register/doctor")

if __name__ == "__main__":
    app.run('0.0.0.0', 8080, True)
