from flask import jsonify


def error_message(message):
    return jsonify(status="error", message=message)


def interval_avg(signal, rate, interval):
    pass
