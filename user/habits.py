from datetime import date
from flask import jsonify
from commons.utils import error_message


'''
This method creates or updates a habit object into a user collection. The user is retrieved through the claims in the 
authentication token. The methods also check if all the parameters are in the payload
'''
def habits_post(params, claims, mongo):

    if claims["type"] != "user":
        return error_message("Only users can add habits!")

    fields = ["caffe", "drink", "isSport", "isCena"]
    for field in fields:
        if field not in params:
            return error_message(field+" is a mandatory parameter!")

    try:
        today = date.today().strftime("%d/%m/%Y")
        mongo.db[claims["identity"]].find_one_and_update(
            {
                "_id": today,
                "type": "habit"
            },
            {
                "$set": {
                    "type": "habit",
                    "coffee": {
                        "type": params["caffe"]["tipo"],
                        "qty": params["caffe"]["totale"]
                    },
                    "drink": {
                        "type": params["drink"]["tipo"],
                        "qty": params["drink"]["totale"]
                    },
                    "sport": params["isSport"],
                    "dinner": params["isCena"]
                }
            },
            upsert=True
        )

        return jsonify(status="ok")

    except Exception as e:
        return error_message(str(e))
