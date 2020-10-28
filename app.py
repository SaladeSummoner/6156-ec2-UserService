
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
import logging

from flask import Flask, Response, Request
from flask import request
import pymysql
from datetime import datetime
import data_table_adaptor as dta

import user
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
_key_delimiter = "_"

resource_path_translator = {}
resource_path_translator["Users"] = "user_table"
resource_path_translator["Address"] = "address_table"
_db_name = "userservice"




print("Environment = ", os.environ)

pw = os.environ['dbpw']
# print("Environment = ", os.environ['dbpw'])

c_info = {
        "host": "database-userservice.ch46gnu5bohw.us-east-2.rds.amazonaws.com",
        "port": 3306,
        "user": "dbuser",
        "password": pw,
        "db" : "userservice",
        "cursorclass": pymysql.cursors.DictCursor,
}
def handle_args(args):
    """

    :param args: The dictionary form of request.args.
    :return: The values removed from lists if they are in a list. This is flask weirdness.
        Sometimes x=y gets represented as {'x': ['y']} and this converts to {'x': 'y'}
    """

    result = {}

    if args is not None:
        for k,v in args.items():
            if type(v) == list:
                v = v[0]
            result[k] = v

    return result

def handle_error(e, result):
    return "Internal error.", 504, {'Content-Type': 'text/plain; charset=utf-8'}

def log_and_extract_input(method, path_params=None):

    path = request.path
    args = dict(request.args)
    data = None
    headers = dict(request.headers)
    method = request.method
    url = request.url
    base_url = request.base_url

    try:
        if request.data is not None:
            data = request.json
        else:
            data = None
    except Exception as e:
        # This would fail the request in a more real solution.
        data = "You sent something but I could not get JSON out of it."

    log_message = str(datetime.now()) + ": Method " + method

    # Get rid of the weird way that Flask sometimes handles query parameters.
    args = handle_args(args)

    inputs =  {
        "path": path,
        "method": method,
        "path_params": path_params,
        "query_params": args,
        "headers": headers,
        "body": data,
        "url": url,
        "base_url": base_url
        }

    # Pull out the fields list as a separate element.
    if args and args.get('fields', None):
        fields = args.get('fields')
        fields = fields.split(",")
        del args['fields']
        inputs['fields'] = fields

    log_message += " received: \n" + json.dumps(inputs, indent=2)
    logger.debug(log_message)

    return inputs


application = Flask(__name__)

# This function performs a basic health check. We will flesh this out.
@application.route("/health", methods=["GET"])
def health_check():

    rsp_data = { "status": "healthy", "location": "EC2", "time": str(datetime.now()) }
    rsp_str = json.dumps(rsp_data)
    rsp = Response(rsp_str, status=200, content_type="application/json")
    return rsp

# @application.route("/Users", methods=["GET", "POST"])
# def users():
#     connection = pymysql.connect(**c_info)
#     print("connection established")
#     try:
#         with connection.cursor() as cur:
#             if request.method == "POST":
#                 details = request.form
#                 res = user.insertUser(details, cur)
#                 connection.commit()
#                 return json.dumps(res, indent=4, default=str)
#
#             if request.method == "GET":
#                 res = user.getUsers()
#                 return json.dumps(res, indent=4, default=str)
#
#     except Exception as e:
#         print("Exeception occured:{}".format(e))
#     finally:
#         connection.close()
#         print("connect close")

@application.route("/databases/<dbname>", methods=["GET"])
def tbls(dbname):
    """

    :param dbname: The name of a database/sche,a
    :return: List of tables in the database.
    """

    inputs = log_and_extract_input(dbs, None)
    res = dta.get_tables(dbname)
    #print(res)

    i = len(res) - 1
    while i >= 0:
        res[i] = res[i]['TABLE_NAME']
        i -= 1

    rsp = Response(json.dumps(res,default=str), status=200, content_type="application/json")
    return rsp

@application.route('/<resource_name>', methods=['GET', 'POST'])
def get_resource(resource_name, dbname=_db_name):

    result = None
    resource_name=resource_path_translator[resource_name]
    try:
        context = log_and_extract_input(get_resource, (resource_name))
        #print(context,"this is context")

        #
        # SOME CODE GOES HERE
        #
        # -- TO IMPLEMENT --


        if request.method == 'GET':
            #
            # SOME CODE GOES HERE
            #
            # -- TO IMPLEMENT --
            fields = context.get("fields", None)
            #print((context['query_params']))
            temp = context.get("body", None)
            for i in context['query_params']:
                if i != 'field' and i not in context["body"]:
                    temp[i] = context['query_params'][i]
            # print(fields)
            r_table = dta.get_rdb_table(resource_name, dbname, connect_info=c_info)
            res = r_table.find_by_template(template=temp, field_list=fields)

            rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
            # rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
            return rsp

        elif request.method == 'POST':
            #
            # SOME CODE GOES HERE
            #
            # -- TO IMPLEMENT --
            # print((context['query_params']))
            temp = context['body']

            print(temp,"This is temp")
            for i in context['query_params']:
                if i != 'field':
                    temp[i] = context['query_params'][i]
            # print(fields)
            r_table = dta.get_rdb_table(resource_name, dbname, connect_info=c_info)
            res = r_table.insert(new_record=temp)

            rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
            return rsp
        else:
            result = "Invalid request."
            return result, 400, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        print("Exception e = ", e)



@application.route('/<resource>/<primary_key>', methods=['GET', 'POST', 'DELETE'])
def resource_by_id(resource, primary_key, dbname=_db_name):
    """

    :param dbname: Schema/database name.
    :param resource: Table name.
    :param primary_key: Primary key in the form "col1_col2_..._coln" with the values of key columns.
    :return: Result of operations.
    """

    result = None
    resource = resource_path_translator[resource]
    try:
        # Parse the incoming request into an application specific format.
        context = log_and_extract_input(resource_by_id, (dbname, resource, primary_key))
        #print(context)

        #
        # SOME CODE GOES HERE
        #
        # -- TO IMPLEMENT --

        if request.method == 'GET':

            #
            # SOME CODE GOES HERE
            #
            # -- TO IMPLEMENT --f
            fields = context.get("fields", None)
            r_table = dta.get_rdb_table(resource, dbname, connect_info=c_info)
            key = primary_key.split(_key_delimiter)
            res = r_table.find_by_primary_key(key,field_list=fields)

            rsp = Response(json.dumps(res,default=str), status=200, content_type="application/json")
            return rsp


        elif request.method == 'DELETE':
            #
            # SOME CODE GOES HERE
            #
            # -- TO IMPLEMENT --
            r_table = dta.get_rdb_table(resource, dbname, connect_info=c_info)
            key = primary_key.split(_key_delimiter)
            res = r_table.delete_by_key(key)

            rsp = Response(json.dumps(res,default=str), status=200, content_type="application/json")
            return rsp

        elif request.method == 'POST':
            #
            # SOME CODE GOES HERE
            #
            # -- TO IMPLEMENT --
            temp = context['body']
            # print(temp,"This is temp")

            r_table = dta.get_rdb_table(resource, dbname, connect_info=c_info)
            key = primary_key.split(_key_delimiter)
            res = r_table.update_by_key(key, new_values=temp)

            rsp = Response(json.dumps(res,default=str), status=200, content_type="application/json")
            return rsp


    except Exception as e:
        print(e)
        return handle_error(e, result)






# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.





    application.debug = True
    application.run(host='0.0.0.0', port=5000)