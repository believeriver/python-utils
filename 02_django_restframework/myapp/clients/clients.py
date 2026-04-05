import requests
import logging
import sys

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger(__name__)

BASE_URL = 'http://127.0.0.1:8000/'


def create_user(_email: str, _password: str, _password2: str):
    _url = f'{BASE_URL}api/auth/register/'
    response = requests.post(_url, json={
        'email': _email,
        'password': _password,
        'password2': _password2,
    })
    logger.debug({'create_user status': response.status_code})
    return response.json()


def fetch_token(_email: str, _password: str):
    _url = f'{BASE_URL}api/auth/login/'
    response = requests.post(_url, json={
        'email': _email,
        'password': _password,
    })
    logger.debug({'fetch_token status': response.status_code})
    return response.json().get('access')


if __name__ == '__main__':
    email = 'nono@example.com'
    password = 'pass1234'
    password2 = 'pass1234'

    create_flg = False

    if create_flg:
        print('create user:')
        res = create_user(email, password, password2)
        print('res:', res)

    print('fetch token')
    token = fetch_token(email, password)
    print({'Authorization JWT': token})
