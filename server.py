from flask import Flask
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo

app = Flask(__name__)

#Initialize mongo client
with open("mongourl.secret") as url_file:
    app.config["MONGO_URI"] = url_file.read()[:-1]
    mongo = PyMongo(app)

#Initialize JWT
with open("jwt.secret") as key_file:
    app.config["JWT_SECRET_KEY"] = key_file.read()[:-1]
    jwt = JWTManager(app)


if __name__ == "__main__":
    app.run("0.0.0.0", 7777, True)
