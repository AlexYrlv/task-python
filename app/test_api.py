import requests

BASE_URL = "http://localhost:8000"

def test_add_service():
    url = f"{BASE_URL}/service"
    data = {
        "name": "Service1",
        "state": "работает",
        "description": "Описание сервиса 1"
    }
    response = requests.post(url, json=data)
    print("Add Service:", response.status_code, response.json())

def test_get_services():
    url = f"{BASE_URL}/services"
    response = requests.get(url)
    print("Get Services:", response.status_code, response.json())

def test_get_service_history():
    url = f"{BASE_URL}/service/Service1"
    response = requests.get(url)
    print("Get Service History:", response.status_code, response.json())

def test_get_sla():
    url = f"{BASE_URL}/sla/Service1?interval=24h"
    response = requests.get(url)
    print("Get SLA:", response.status_code, response.json())

if __name__ == "__main__":
    test_add_service()
    test_get_services()
    test_get_service_history()
    test_get_sla()
