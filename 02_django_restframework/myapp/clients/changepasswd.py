import requests
import logging
import sys

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger(__name__)

BASE_URL = 'http://127.0.0.1:8080/'


def fetch_token(_email: str, _password: str):
    _url = f'{BASE_URL}api/auth/login/'
    response = requests.post(_url, json={
        'email': _email,
        'password': _password,
    })
    logger.debug({'fetch_token status': response.status_code})
    return response.json().get('access')


def change_password(_access_token: str, _current: str, _new: str, _new2: str):
    _url = f'{BASE_URL}api/auth/change-password/'
    response = requests.post(
        _url,
        json={
            'current_password': _current,
            'new_password':     _new,
            'new_password2':    _new2,
        },
        headers={'Authorization': f'Bearer {_access_token}'},
    )
    logger.debug({'change_password status': response.status_code})
    return response.json()


if __name__ == '__main__':
    email = 'nono@example.com'
    password = 'pass1234'
    newpass = 'newpass5678'

    # ログイン
    login_res = requests.post(
        f'{BASE_URL}api/auth/login/',
        json={'email': email, 'password': password},
    )
    access_token = login_res.json().get('access')

    # パスワード変更
    print('--- パスワード変更 ---')
    res = change_password(access_token, 'pass1234', newpass, newpass)
    print(res)

    # 新パスワードで再ログイン確認
    print('--- 新パスワードでログイン ---')
    new_login = requests.post(
        f'{BASE_URL}api/auth/login/',
        json={'email': email, 'password': newpass},
    )
    print({'status': new_login.status_code, 'access': new_login.json().get('access')})