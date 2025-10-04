import requests
import json

def test_login():
    url = "http://localhost:5000/api/login"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            print(f"JSON Response: {response.json()}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()