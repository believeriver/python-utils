import requests
import logging
import sys

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger(__name__)

BASE_URL = 'http://127.0.0.1:8080/'


def get_profile(_access_token: str):
    _url = f'{BASE_URL}api/auth/profile/'
    response = requests.get(
        _url,
        headers={'Authorization': f'Bearer {_access_token}'},
    )
    logger.debug({'get_profile status': response.status_code})
    return response.json()


def update_profile(_access_token: str, **kwargs):
    _url = f'{BASE_URL}api/auth/profile/'
    response = requests.patch(
        _url,
        json=kwargs,
        headers={'Authorization': f'Bearer {_access_token}'},
    )
    logger.debug({'update_profile status': response.status_code})
    return response.json()


if __name__ == '__main__':
    email    = 'nono@example.com'
    password = 'newpass5678'

    new_name= 'nono_updated'
    new_email = 'nono_new@example.com'

    # ログイン
    login_res = requests.post(
        f'{BASE_URL}api/auth/login/',
        json={'email': email, 'password': password},
    )
    access_token = login_res.json().get('access')

    # 現在のプロフィール取得
    print('--- 現在のプロフィール ---')
    print(get_profile(access_token))

    # usernameだけ更新
    print('--- username更新 ---')
    print(update_profile(access_token, username=new_name))

    # emailだけ更新
    print('--- email更新 ---')
    print(update_profile(access_token, email=new_email))
