import requests

url = "http://localhost:8000/api/country-datetime/"
# params = {
#     "timezone": "Asia/Tokyo"
# }
params = {
    "timezone": "US/E"
}

# response = requests.get(url, params=params)
#
# print(response.json())
# print(response.status_code)
# print(response.text)
# print(response.headers)

response = requests.put(url, data=params)
print(response.status_code)
print(response.text)