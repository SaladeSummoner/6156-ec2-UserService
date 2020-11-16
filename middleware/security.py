import jwt
import copy


_secret = 'secret'

_whitelist = [
    '/api/registration'
]


def encode_pw(pw):
    res = jwt.encode({'hashed_password': pw}, _secret)
    return res


def decode_pw(tok):
    res = jwt.decode(tok, _secret)
    return res.get('hashed_password')


def generate_token(user_info):
    temp = {}
    for k in ['id', 'last_name', 'first_name', 'email', 'role']:
        temp[k] = user_info.get(k, None)

    res = jwt.encode(temp, _secret)
    return res


def decode_token(tok):
    try:
        res = jwt.decode(tok, _secret)
    except Exception as e:
        print('Exception e =' + str(e))
        raise e

    return res


def check_password(in_password, hashed_pw):
    pass


def check_authentication(request):
    result = (401, 'NOT AUTHORIZED', None)
    try:
        path = copy.copy(request.path)

        if path not in _whitelist:
            header = dict(request.headers)
            tok = header.get('Authorization',None)

            if tok is not None:
                dec = decode_token(tok)
                result = (200, 'OK', dec)
        else:
            result = (200, 'OK', None)
    except Exception as e:
        print('check_authentication Exception =' + str(e))
        raise e
    return result

