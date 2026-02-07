import requests

url = "http://localhost:8000/api_token_auth/"
data = {
    "username": "test2",
    "password": "test2"
}

response = requests.post(url, data=data)

print(response.json())

# test2ユーザーのトークンが返ってくる
#{'token': 'f8cda641c155c4f0d4ea1a19ffc479719634960e'}