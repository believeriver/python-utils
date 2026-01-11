import requests

url = "http://localhost:8000/api/json-example/"
response = requests.get(url)

print(response.json())