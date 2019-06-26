from commons.utils import error_message
from flask import make_response
from passlib.hash import pbkdf2_sha256 as sha256


'''
This function manages the registration of a doctor
'''
def doctor_register(params, mongo):
    if params is None:
        return False, error_message("mime type not accepted")

    fields = ["id", "email", "password", "name", "surname", "address", "phone_number"]

    for field in fields:
        if field not in params:
            return False, error_message(field + " is a mandatory field")

    try:
        if mongo.db.doctors.find_one({'_id': params["id"]}) is not None:
            return False, error_message("a user with this id already exists!")

        mongo.db.doctors.insert_one(
            {
                "_id": str(params["id"]),
                "email": params["email"],
                "password": sha256.hash(params["password"]),
                "name": params["name"],
                "surname": params["surname"],
                "address": params["address"],
                "phone_number": params["phone_number"],
                "patients": [],
                "patient_requests": [],
                "signals": [],
                "profile_picture": ""
            }
        )

        return True, None

    except Exception as e:
        return False, make_response(str(e), 500)


'''
This function manages the login. It receives the user type, the identity, the password and returns a boolean and an 
error message, that can be None
'''
def login(user_type, identity, password, mongo):
    if identity is None or password is None:
        return False, error_message("Id and password are mandatory fields!")

    try:
        user = mongo.db[user_type+"s"].find_one({"_id": identity})

        if user is None:
            return False, error_message("user does not exists!")

        pwd = user["password"]
        if not sha256.verify(password, pwd):
            return False, error_message("password is not correct")

        return True, None

    except Exception as e:
        return False, make_response(str(e), 500)


'''
This function handles the registration of a user
'''
def user_register(params, mongo):
    if params is None:
        return error_message("mime type not accepted")

    fields = ["cf", "name", "surname", "age", "email", "password", "phone_number"]

    for field in fields:
        if field not in params:
            return False, error_message(field + " is a mandatory field")

    try:
        if mongo.db.users.find_one({'_id': params["cf"]}) is not None:
            return False, error_message("a user with this CF already exists!")

        mongo.db.users.insert_one(
            {
                "_id": params["cf"],
                "email": params["email"],
                "password": sha256.hash(params["password"]),
                "name": params["name"],
                "surname": params["surname"],
                "age": params["age"],
                "phone_number": params["phone_number"],
                "profile_picture": ""
            }
        )

        return True, None

    except Exception as e:
        return False, make_response(str(e), 500)

