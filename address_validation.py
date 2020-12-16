import json
import requests

context = {
    'auth_id': '1bd58da0-f135-09f7-7a34-661e77d8bc1f',
    'auth_token': 'qCvQZJY3rV96sOJnSg1P',
    'address_url': 'https://us-street.api.smartystreets.com/street-address'
}


def validate_address(address, context):
    params = {'auth-id': context.get('auth_id', None), 'auth-token': context.get('auth_token', None)}

    url = context.get('address_url', None)

    if params['auth-id'] is None or params['auth-token'] is None or url is None:
        return 500

    params['match'] = 'strict'

    try:
        params['street'] = address['street']
        state = address.get('state',None)
        if state is not None:
            params['state'] = state

        city = address.get('state', None)
        if city is not None:
            params['city'] = city

        zipcode = address.get('zipcode', None)
        if zipcode is not None:
            params['zipcode'] = zipcode

    except KeyError as ke:
        return 422

    result = requests.get(url, params=params)

    if result.status_code == 200:

        j_data = result.json()

        if len(j_data) != 1:
            rsp = None
        else:
            rsp = j_data[0]['components']
            rsp['delivery_point_barcode'] = j_data[0]['delivery_point_barcode']

    else:
        rsp = None

    return rsp




