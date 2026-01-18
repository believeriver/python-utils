import requests

url = "http://localhost:8000/api/item/"

print("GET Response:")
response = requests.get(url)
print(response.status_code)
print(response.json())

print("POST Response:")
data = {
    "name": "nNewItem",
    "price": 100,
    "discount": 110
}
response = requests.post(url, data=data)
print(response.status_code)
print(response.json())

print("PUT Response:")
response = requests.put(url)
print(response.status_code)
print(response.json())

print("DELETE Response:")
response = requests.delete(url)
print(response.status_code)
print(response.json())