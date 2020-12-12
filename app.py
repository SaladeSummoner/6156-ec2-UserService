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
import uuid
from flask import Flask, Response, Request
from flask import request

import pymysql
from datetime import datetime
import data_table_adaptor as dta
import middleware.security as security

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
_key_delimiter = "_"

resource_path_translator = {}
resource_path_translator["Users"] = "user_table"
resource_path_translator["Address"] = "address_table"
_db_name = "userservice"

# print("Environment = ", os.environ)

pw = os.environ['dbpw']
# print("Environment = ", os.environ['dbpw'])

c_info = {
    "host": "database-userservice.ch46gnu5bohw.us-east-2.rds.amazonaws.com",
    "port": 3306,
    "user": "dbuser",
    "password": pw,
    "db": "userservice",
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
        for k, v in args.items():
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

    inputs = {
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
    rsp_data = {"status": "healthy", "location": "EC2", "time": str(datetime.now())}
    rsp_str = json.dumps(rsp_data)
    rsp = Response(rsp_str, status=200, content_type="application/json")
    return rsp


@application.route("/databases/<dbname>", methods=["GET"])
def tbls(dbname):
    """

    :param dbname: The name of a database/sche,a
    :return: List of tables in the database.
    """

    inputs = log_and_extract_input(dbs, None)
    res = dta.get_tables(dbname)
    # print(res)

    i = len(res) - 1
    while i >= 0:
        res[i] = res[i]['TABLE_NAME']
        i -= 1

    rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
    return rsp


@application.route('/<resource_name>', methods=['GET', 'POST'])
def get_resource(resource_name, dbname=_db_name):
    result = None
    resource_name = resource_path_translator[resource_name]
    try:
        context = log_and_extract_input(get_resource, resource_name)

        #
        # SOME CODE GOES HERE
        #
        # -- TO IMPLEMENT --
        if request.method == 'GET':
            #
            # SOME CODE GOES HERE
            #
            # -- TO IMPLEMENT --
            args = request.args
            # print(args)

            offset = args.get('offset') if 'offset' in args else 0
            limit = args.get('limit') if 'limit' in args else None

            fields = context.get("fields", None)

            # temp = context.get("body", None) if context.get("body", None) is not None else {}
            temp = {}
            for i in context['query_params']:
                if i != 'offset' and i != 'limit':
                    temp.update({i: context['query_params'][i]})

            r_table = dta.get_rdb_table(resource_name, dbname, connect_info=c_info)
            res = r_table.find_by_template(template=temp, field_list=fields, offset=offset, limit=limit)
            data = []

            for result in res:
                if resource_name == "user_table":
                    link = [
                        {
                            "rel": "email",
                            "href": "/api/user?emails=" + result["email"],
                            "method": "GET"
                        }
                    ]
                    data.append({"data": result, "links": link})
                elif resource_name == "address_table":
                    link = [
                        {
                            "rel": "user for this address",
                            "href": "/api/user?id=" + str(result["userid"]),
                            "method": "GET"
                        }
                    ]
                    data.append({"data": result, "links": link})
            if limit is None and offset == 0:
                rsp = Response(json.dumps({'data': data}, default=str), status=200, content_type="application/json")
            else:
                total = r_table.get_row_count()
                next_link = request.base_url + '?limit=' + str(limit) + (
                    '&offset=' + str(int(offset) + int(limit)) if int(offset) + int(limit) < int(total)
                    else '&offset=' + str(total))
                prev_link = request.base_url + '?limit=' + str(limit) + (
                    '&offset=' + str(int(offset) - int(limit)) if int(offset) - int(limit) >= 0
                    else '&offset=' + '0')
                rsp = Response(json.dumps({'pagination': {'offset': int(offset), 'limit': int(limit), 'total': total},
                                           'data': data,
                                           'links': {
                                               'next': next_link,
                                               'prev': prev_link
                                           }
                                           }, default=str), status=200, content_type="application/json")

            return rsp

        elif request.method == 'POST':
            #
            # SOME CODE GOES HERE
            #
            # -- TO IMPLEMENT --
            # print((context['query_params']))
            temp = context['body']

            print(temp, "This is temp")
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
    print('resourcebyid')
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
        # print(context)

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
            res = r_table.find_by_primary_key(key, field_list=fields)

            rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
            return rsp

        elif request.method == 'DELETE':
            #
            # SOME CODE GOES HERE
            #
            # -- TO IMPLEMENT --
            r_table = dta.get_rdb_table(resource, dbname, connect_info=c_info)
            key = primary_key.split(_key_delimiter)
            res = r_table.delete_by_key(key)

            rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
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

            rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
            return rsp

    except Exception as e:
        print(e)
        return handle_error(e, result)


@application.route('/api/users', methods=['POST'])
def create_user():
    table = resource_path_translator["Users"]
    context = log_and_extract_input(get_resource, table)
    param = context['body']
    # print(param)
    temp = {
        'id': str(uuid.uuid4()),
        'last_name': param['last_name'],
        'first_name': param['first_name'],
        'email': param['email'],
        'hashed_password': param['password'],
        'created_date': datetime.now()
    }
    # print(temp)
    r_table = dta.get_rdb_table(table, _db_name, connect_info=c_info)
    res = r_table.insert(temp)
    # print(res)
    if res == 1:
        location = {'Location': '/api/users/' + temp['id']}
        rsp = Response(json.dumps("user created success"), status=201, content_type="application/json",
                       headers=location)
    else:
        rsp = Response(json.dumps("user created fail"), status=400, content_type="application/json")
    return rsp


def _register(user_info):
    hashed_pw = security.encode_pw(user_info['password'])
    user_info['hashed_password'] = hashed_pw
    del user_info['password']

    table = resource_path_translator["Users"]
    new_uuid = str(uuid.uuid4())
    print(new_uuid)
    temp = {
        'id': new_uuid,
        'last_name': user_info['last_name'],
        'first_name': user_info['first_name'],
        'email': user_info['email'],
        'hashed_password': user_info['hashed_password'],
        'created_date': datetime.now()
    }
    # print(temp)
    r_table = dta.get_rdb_table(table, _db_name, connect_info=c_info)
    res = r_table.insert(temp)
    tok = security.generate_token(user_info)

    return new_uuid, tok


@application.route('/api/registration', methods=['POST'])
def registration():
    inputs = log_and_extract_input(registration)

    rsp_data = None
    rsp_status = None
    rsp_txt = None

    try:
        if inputs['method'] == 'POST':
            rsp, token = _register(inputs['body'])
            if rsp is not None:
                rsp_status = 201
                rsp_txt = 'CREATED'
                link = rsp
                auth = token
            else:
                rsp_data = None
                rsp_status = 404
                rsp_txt = 'NOT FOUND'
        else:
            rsp_data = None
            rsp_txt = 'NOT IMPLEMENTED'
            rsp_status = 501

        if rsp_txt == 'CREATED':
            headers = {'Location': '/api/users/' + link, 'Authorization:': auth}
            full_rsp = Response(rsp_txt, headers=headers, status=rsp_status, content_type='text/plain')
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type='text/plain')

    except Exception as e:
        logger.error('api/registration: Exception=' + str(e))
        rsp_status = 500
        rsp_txt = 'INTERNAL SERVER ERROR'
        full_rsp = Response(rsp_txt, status=rsp_status, content_type='text/plain')

    return full_rsp


@application.route('/api/login', methods=['POST'])
def user_login():
    inputs = log_and_extract_input(user_login)

    try:
        if inputs['method'] == 'POST':
            body = inputs['body']
            # Get the hashed password from database
            table = resource_path_translator["Users"]
            r_table = dta.get_rdb_table(table, _db_name, connect_info=c_info)
            template = {'email': body['email']}
            field_list = ['hashed_password', 'id', 'last_name', 'first_name', 'email']
            res = r_table.find_by_template(template=template, field_list=field_list)[0]
            pw_check = security.check_password(body['password'], res['hashed_password'])

            if pw_check:
                rsp_status = 201
                rsp_txt = 'CREATED'
                tok = security.generate_token(res)
            else:
                rsp_status = 401
                rsp_txt = 'NOT AUTHORIZED'
        else:
            rsp_txt = 'NOT IMPLEMENTED'
            rsp_status = 501

        if rsp_txt == 'CREATED':
            headers = {'Authorization:': tok}
            full_rsp = Response(rsp_txt, headers=headers, status=rsp_status, content_type='text/plain')
        else:
            full_rsp = Response(rsp_txt, status=rsp_status, content_type='text/plain')

    except Exception as e:
        logger.error('api/login: Exception=' + str(e))
        rsp_status = 500
        rsp_txt = 'INTERNAL SERVER ERROR'
        full_rsp = Response(rsp_txt, status=rsp_status, content_type='text/plain')

    return full_rsp


# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.

    application.debug = True
    application.run(host='0.0.0.0', port=5000)
