import requests


def get_token(_username: str, _password: str) -> str:
    url = "http://localhost:8000/api_token_auth/"
    data = {
        "username": _username,
        "password": _password
    }

    response = requests.post(url, data=data)
    # print(response.json())
    # test2ユーザーのトークンが返ってくる
    # {'token': 'f8cda641c155c4f0d4ea1a19ffc479719634960e'}
    return response.json().get("token")


def post_with_token(_token: str, _url: str, _data: dict) -> requests.Response:
    headers = {
        "Authorization": f"Token {_token}"
    }
    response = requests.post(_url, headers=headers, data=_data)
    return response.json()


if __name__ == '__main__':
    # print(get_token("test2", "test2"))
    # print(get_token("admin", "admin"))

    token = get_token("test2", "test2")
    data = {
        "name": "Product A",
        "price": 150,
        "user": 3
    }
    url = "http://localhost:8000/api/v2/product/"
    print(post_with_token(token, url, data))
