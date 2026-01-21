import requests

def test_get(url: str):
    print("GET Response:")
    response = requests.get(url)
    print(response.status_code)
    print(type(response.text))
    print(response.json())
    print(type(response.json()))

    for item in response.json():
        print(item.get("name"))

def test_post(url: str):
    print("POST Response:")
    data = {
        "name": "nNewItem",
        "price": 100,
        "discount": 115
    }
    response = requests.post(url, data=data)
    print(response.status_code)
    print(response.json())

def test_put(url: str):
    print("PUT Response:")
    response = requests.put(url)
    print(response.status_code)
    print(response.json())

def test_delete(url: str):
    print("DELETE Response:")
    response = requests.delete(url)
    print(response.status_code)
    print(response.json())


if __name__ == "__main__":
    url = "http://localhost:8000/api/item/"
    test_get(url)
    # test_post(url)
    # test_put(url)
    # test_delete(url)
