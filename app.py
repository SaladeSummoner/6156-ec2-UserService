
# Import functions and objects the microservice needs.
# - Flask is the top-level application. You implement the application by adding methods to it.
# - Response enables creating well-formed HTTP/REST responses.
# - requests enables accessing the elements of an incoming HTTP/REST request.
#
import json
# Setup and use the simple, common Python logging framework. Send log messages to the console.
# The application should get the log level out of the context. We will change later.
#

import os
import sys

from flask import Flask, Response, Request
from flask import request
import pymysql
from datetime import datetime

import user

print("Environment = ", os.environ)

pw = os.environ['dbpw']

print("Environment = ", os.environ['dbpw'])

c_info = {
        "host": "database-userservice.ch46gnu5bohw.us-east-2.rds.amazonaws.com",
        "user": "dbuser",
        "password": pw,
        "cursorclass": pymysql.cursors.DictCursor,
}


application = Flask(__name__)


# This function performs a basic health check. We will flesh this out.
@application.route("/health", methods=["GET"])
def health_check():

    rsp_data = { "status": "healthy", "location": "EC2", "time": str(datetime.now()) }
    rsp_str = json.dumps(rsp_data)
    rsp = Response(rsp_str, status=200, content_type="application/json")
    return rsp

@application.route("/Users", methods=["GET", "POST"])
def users():
    connection = pymysql.connect(**c_info)
    print("connection established")
    try:
        with connection.cursor() as cur:
            if request.method == "POST":
                details = request.form
                res = user.insertUser(details, cur)
                connection.commit()
                return json.dumps(res, indent=4, default=str)

            if request.method == "GET":
                res = user.getUsers()
                return json.dumps(res, indent=4, default=str)

    except Exception as e:
        print("Exeception occured:{}".format(e))
    finally:
        connection.close()
        print("connect close")





# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.





    application.debug = True
    application.run(host='0.0.0.0', port=5000)