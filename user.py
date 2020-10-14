from flask import Flask, jsonify, request
import datetime

def getUsers(cur):
    query = "select * from USER_TABLE;"
    res = cur.execute(query)
    res = cur.fetchall()
    return res

def insertUser(details, cur):
    if len(details) < 5:
        return jsonify(Error="Missing info")
    else:
        user_id = details['id']
        last_name = details['last_name']
        first_name = details['first_name']
        email = details['email']
        pwd = details['hashed_password']
        status = details['status']

        if user_id and last_name and first_name and email and pwd:
            #to do : check if duplicate exits by calling get ?
            # return fail
            if status:
                cur.execute(
                    "INSERT INTO USER_TABLE (id,last_name,first_name,email,hashed_password,created_date,status) "
                    "VALUES (%d, %s, %s, %s, %s, %s, %s);", user_id, last_name, first_name, email, pwd, 'now', status)
            else:
                cur.execute("INSERT INTO USER_TABLE (id,last_name,first_name,email,hashed_password,created_date) "
                            "VALUES (%d, %s, %s, %s, %s, %s);", user_id, last_name, first_name, email, pwd, 'now')
            if cur.fetchone()[0]:
                return jsonify(Success='Success')
            else:
                return jsonify(Error='Error to insert')
        else:
            return jsonify(Error='Post request failed due to incorrect entries')


