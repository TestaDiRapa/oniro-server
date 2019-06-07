from datetime import date
from flask import jsonify
from utils import error_message


def habits_post(params, claims, mongo):

    if claims["type"] != "user":
        return error_message("Only users can add habits!")

    fields = ["caffe", "drink", "isSport", "isCena"]
    for field in fields:
        if field not in params:
            return error_message(field+" is a mandatory parameter!")

    try:
        today = date.today().strftime("%d/%m/%Y")
        cf = claims["identity"]
        mongo.db[cf].insert_one_and_update(
            {
                "_id": today,
                "type": "habit"
            },
            {
                "$set": {
                    "type": "habit",
                    "coffee": params["caffe"],
                    "drink": params["drink"],
                    "isSport": params["isSport"],
                    "isDinner": params["isCena"]
                }
            },
            upsert=True
        )

        return jsonify(status="ok")

    except Exception as e:
        return error_message(str(e))
