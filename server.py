from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient()



if __name__ == "__main__":
    app.run("0.0.0.0", 7777)
