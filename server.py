from commons import get_coordinates, me_get, me_post
from commons.authentication import doctor_register, login, user_register
from commons.facts import facts_get, facts_post
from doctor.my_alerts import my_alerts_delete, my_alerts_get
from doctor.my_patients import my_patients_delete, my_patients_get, my_patients_post
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, decode_token, \
    jwt_refresh_token_required, get_jwt_claims, get_jwt_identity
from flask_pymongo import PyMongo
from user.habits import habits_post
from user.my_doctors import my_doctors_post, my_doctors_get, my_doctors_delete
from user.my_recordings import my_recordings_get, my_recordings_put, processing, send_to_doctor

app = Flask(__name__)
CORS(app)

# Initialise mongo client
with open("/root/oniro-server/mongourl.secret") as url_file:
    app.config["MONGO_URI"] = url_file.read()[:-1]
    mongo = PyMongo(app)

# Initialise JWT secret key
with open("/root/oniro-server/jwt.secret") as key_file:
    app.config["JWT_SECRET_KEY"] = key_file.read()[:-1]
    jwt = JWTManager(app)


'''
Decorator used to add custom claims to access token
'''
@jwt.user_claims_loader
def add_claims_to_access_token(data):
    return {
        "identity": data["username"],
        "type": data["type"]
    }


'''
Login method for both patients and doctors. It expects the type of user (user or doctor) in the path and the login
credentials as query parameters.
On success returns an authorization token, a refresh token and their expiration in a JSON format.
On fail returns an error message in a JSON format.
'''
@app.route('/login/<string:user_type>', methods=['GET'])
def login(user_type):
    if user_type != "user" and user_type != "doctor":
        return make_response("error", 404)

    key = ""
    if user_type == "user":
        key = "cf"
    elif user_type == "doctor":
        key = "id"

    identity = request.args.get(key)
    password = request.args.get("password")

    result, message = login(user_type, identity, password, mongo)

    if not result:
        return message

    access_token = create_access_token({"username": identity, "type": user_type})
    expiration = decode_token(access_token)["exp"]
    r_token = create_refresh_token({"username": identity, "type": user_type})
    refresh_expiration = decode_token(r_token)["exp"]

    return jsonify(status="ok", access_token=access_token, access_token_exp=expiration, refresh_token=r_token,
                   refresh_token_exp=refresh_expiration)


'''
Method for the users registration. It expects the registration data in the payload in a JSON format.
On success returns an authorization token, a refresh token and their expiration in a JSON format.
On fail returns an error message in a JSON format.
'''
@app.route("/register/user", methods=['PUT'])
def register_user():
    json_data = request.get_json(silent=True, cache=False)

    result, message = user_register(json_data, mongo)

    if not result:
        return message

    access_token = create_access_token({"username": json_data["cf"], "type": "user"})
    expiration = decode_token(access_token)["exp"]
    r_token = create_refresh_token({"username": json_data["cf"], "type": "user"})
    refresh_expiration = decode_token(r_token)["exp"]

    return jsonify(status="ok", access_token=access_token, access_token_exp=expiration, refresh_token=r_token,
                   refresh_token_exp=refresh_expiration)


'''
Method for the doctors registration. It expects the registration data in the payload in a JSON format.
On success returns an authorization token, a refresh token and their expiration in a JSON format.
On fail returns an error message in a JSON format.
'''
@app.route("/register/doctor", methods=['PUT'])
def register_doctor():
    json_data = request.get_json(silent=True, cache=False)

    result, message = doctor_register(json_data, mongo)

    if not result:
        return message

    access_token = create_access_token({"username": json_data["id"], "type": "doctor"})
    expiration = decode_token(access_token)["exp"]
    r_token = create_refresh_token({"username": json_data["id"], "type": "doctor"})
    refresh_expiration = decode_token(r_token)["exp"]

    return jsonify(status="ok", access_token=access_token, access_token_exp=expiration, refresh_token=r_token,
                   refresh_token_exp=refresh_expiration)


'''
Method used to refresh the authentication token of a user. It needs a refresh token sent in the request's header.
It returns a valid authentication token and its expiration in a JSON format.
'''
@app.route("/refresh", methods=['GET'])
@jwt_refresh_token_required
def refresh_token():
    claims = get_jwt_identity()
    access_token = create_access_token({"username": claims["username"], "type": claims["type"]})
    expiration = decode_token(access_token)["exp"]

    return jsonify(status="ok", access_token=access_token, access_token_exp=expiration)


'''
This resource represents the information related to a user and can be accessed only with a valid authentication token
In case of a GET request, then the method expects no parameters and returns all the data related to the user in a 
JSON format
In case of a POST request, then  the methods expects the data of the user to change in a form data format.
It returns a success message or an error message in a JSON format.
'''
@app.route("/me", methods=['GET', 'POST'])
@jwt_required
def me():
    claims = get_jwt_claims()

    if request.method == 'GET':
        return me_get(claims, mongo)

    if request.method == 'POST':

        image = None
        if "file" in request.files:
            image = request.files["file"]

        return me_post(request.form, claims, mongo, image)


'''
This resource allow a user to manage the doctors it is associated to or its requests to the doctors.
This method requires a valid authentication token and is available to patients only.
In case of a GET request, the methods expects no parameters and returns a list of doctors, divided in subscription
requests and subscription or an error message, both in a JSON format.
In case of a POST request, the methods expects a doctor id in the payload in a JSON format and allow a patient to send a 
request to a doctor. It returns a success message or an error message in a JSON format.
In case of a DELETE request, the methods allow a patient to delete a subscription request or a subscription. It expects
the id of the doctor as a query parameter. It returns a success message or an error message in a JSON format.
'''
@app.route("/user/my_doctors", methods=['GET', 'DELETE', 'POST'])
@jwt_required
def my_doctors():
    params = request.get_json(silent=True, cache=False)
    claims = get_jwt_claims()

    if request.method == 'GET':
        return my_doctors_get(claims, mongo)

    if request.method == 'POST':
        return my_doctors_post(params, claims, mongo)

    if request.method == 'DELETE':
        return my_doctors_delete(request.args.get("doctor_id"), claims, mongo)


'''
This method returns all the addresses of all the doctors registered in a JSON format, along with their name and surname 
in a JSON format. 
In case of error it returns an error message in a JSON format.
This method requires a valid access token and it expects no additional parameters.
'''
@app.route("/user/getcoordinates", methods=['GET'])
@jwt_required
def get_coordinates():

    return get_coordinates(mongo)


'''
This method allow a patient to insert or update its habits related to a certain day. It requires a valid authentication 
token and can be only accessed by patients.
It expects the habits in the payload in a JSON format and returns a success message or an error message in a JSON 
format.
'''
@app.route("/user/habits", methods=['PUT'])
@jwt_required
def habits():
    params = request.get_json(silent=True, cache=False)
    claims = get_jwt_claims()

    if request.method == 'PUT':
        return habits_post(params, claims, mongo)


'''
This method allow a doctor to manage its patients. It requires a valid authentication token anc can be only accessed by 
patients. 
In case of a GET request, the methods expects no parameters and returns a list of the patient associated to the doctor, 
divided in subscription requests and subscribed or an error message, both in a JSON format.
In case of a POST request, the methods expects a patient cf in the payload in a JSON format and allow a doctor to accept 
a request from a patient. It returns a success message or an error message in a JSON format.
In case of a DELETE request, the methods allow a doctor to delete a subscription request or a subscription. It expects
the cf of the patient as a query parameter. It returns a success message or an error message in a JSON format.
'''
@app.route("/doctor/my_patients", methods=['GET', 'DELETE', 'POST'])
@jwt_required
def my_patients():
    params = request.get_json(silent=True, cache=False)
    claims = get_jwt_claims()

    if request.method == 'GET':
        return my_patients_get(claims, mongo)

    if request.method == 'POST':
        return my_patients_post(params, claims, mongo)

    if request.method == 'DELETE':
        return my_patients_delete(request.args.get("patient_cf"), claims, mongo)


'''
This method manages the sleep recordings data. It requires a valid authentication token. The PUT method can be accessed 
only by patient, while the GET method can be accessed both by patients and doctors
The patient can use the GET method as such:
    - if the id query parameter is not specified, then the response will contain all the previews of the recordings 
    associated to that user in a JSON format.
    - if the id query parameter is specified, then the response will contain all the elaborated data of the recording
    with the specified id
The doctor can use the GET method in the same way, but can access just the data of its patients and must specify also 
the cf of the patients he wants to see the data of.
In case of a PUT request, the method expects a chunk of the data related to a sleep recording session in the body in a 
JSON format in order to add them to the other data associated to the same session. It will return a success or an error
message in a JSON format.
'''
@app.route("/user/my_recordings", methods=['PUT', 'GET'])
@jwt_required
def my_recordings():
    params = request.get_json(silent=True)
    claims = get_jwt_claims()

    if request.method == 'PUT':
        return my_recordings_put(params, claims, mongo)

    if request.method == 'GET':
        return my_recordings_get(request.args.get("id"), request.args.get("cf"), claims, mongo)


'''
This method triggers the elaboration of the raw data of a recording. It requires a valid authentication token and can be
accessed only by users.
This method accepts only GET requests with two mandatory query parameters:
    - id: the id of the recording to elaborate
    - stop: the timestamp (in ISO format) of the time the recording stopped
'''
@app.route("/user/my_recordings/process", methods=['GET'])
@jwt_required
def process_recording():
    claims = get_jwt_claims()
    rec_id = request.args.get("id")
    stop_time = request.args.get("stop")

    return processing(rec_id, stop_time, claims, mongo)


'''
This method allow a patient to report a sleep recording to a doctor. It requires a valid authentication token and can be 
accessed only by a user. 
The method accepts only POST requests and expects a payload in a JSON format that contains the id of the recording to 
report and the id of the doctor to send the report to.
It returns a success or an error mesasge in a JSON format.
'''
@app.route("/user/my_recordings/send", methods=['POST'])
@jwt_required
def signal_recording():
    claims = get_jwt_claims()
    params = request.get_json(silent=True)

    if request.method == 'POST':
        return send_to_doctor(params, claims, mongo)


'''
This method allow a doctor to manage all its reports. It requires a valid authentication token and can only be accessed 
by a doctor.
In case of a DELETE request, the method expects a patient cf and a recording id as query parameters and delete the 
report related to those parameters. It returns a success or an error message in a JSON format.
In case of a GET request, the method returns all the reports associated to the doctor (whose identity is stored in the
authentication token) in a JSON format or an error message in a JSON format.
'''
@app.route("/doctor/my_alerts", methods=['DELETE', 'GET'])
@jwt_required
def get_my_requests():
    claims = get_jwt_claims()

    if request.method == 'DELETE':
        return my_alerts_delete(request.args.get("id"), request.args.get("cf"), claims, mongo)

    if request.method == 'GET':
        return my_alerts_get(claims, mongo)


@app.route("/facts", methods=['GET', 'POST'])
def add_fact():
    params = request.get_json(silent=True)

    if request.method == 'GET':
        return facts_get(mongo)

    if request.method == 'POST':
        return facts_post(params, mongo)


if __name__ == "__main__":
    app.run('0.0.0.0', 8080)
