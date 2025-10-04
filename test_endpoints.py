#!/usr/bin/env python3
"""
Test API endpoints
"""
import requests
import json

def test_api():
    base_url = "http://localhost:5001"
    
    # Test categories endpoint
    try:
        print("🧪 Testing categories endpoint...")
        response = requests.get(f"{base_url}/api/classification/categories")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Categories count: {len(data.get('categories', []))}")
            print("Categories:")
            for cat in data.get('categories', [])[:3]:
                print(f"  - {cat.get('name')} (ID: {cat.get('id')})")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Categories test failed: {e}")
    
    # Test security levels endpoint
    try:
        print("\n🔒 Testing security levels endpoint...")
        response = requests.get(f"{base_url}/api/classification/security-levels")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Security levels count: {len(data.get('security_levels', []))}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Security levels test failed: {e}")
    
    # Test analytics endpoint
    try:
        print("\n📊 Testing analytics endpoint...")
        response = requests.get(f"{base_url}/analytics")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Analytics data:", json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Analytics test failed: {e}")

if __name__ == "__main__":
    test_api()