import requests
import sys
from urllib.parse import urljoin

# Base URL for the API server
BASE_URL = "https://v2202209183503201737.happysrv.de/"

def test_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Test an API endpoint and return whether it's functional"""
    url = urljoin(BASE_URL, endpoint)
    print(f"Testing {method} {url}...")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            print(f"Method {method} not supported")
            return False
        
        print(f"Status code: {response.status_code}")
        if response.status_code == expected_status:
            print(f"✅ Success: {response.status_code}")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response text: {response.text[:200]}...")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response text: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    # Test if server is running
    print(f"Testing server at {BASE_URL}...")
    try:
        response = requests.get(BASE_URL)
        print(f"Server is running at {BASE_URL}")
        print(f"Status code: {response.status_code}")
        print(f"Response text: {response.text[:200]}...")
    except Exception as e:
        print(f"Server is not accessible at {BASE_URL}. Error: {str(e)}")
        sys.exit(1)
    
    # Test API Documentation endpoints
    print("\nTesting API Documentation endpoints:")
    test_endpoint("swagger/")
    test_endpoint("redoc/")
    
    # Test Core API endpoints
    print("\nTesting Core API endpoints:")
    test_endpoint("api/auth/login/", method="POST", data={"username": "test", "password": "test"}, expected_status=400)
    test_endpoint("api/auth/users/")
    
    # Test Publications API endpoints
    print("\nTesting Publications API endpoints:")
    test_endpoint("api/publications/publications/")
    test_endpoint("api/publications/public/publications/")
    
    # Test Comments API endpoints
    print("\nTesting Comments API endpoints:")
    test_endpoint("api/comments/comments/")
    
    # Test AI Assistant API endpoints
    print("\nTesting AI Assistant API endpoints:")
    test_endpoint("api/ai/ai-models/")
    
    print("\nLive server testing completed.")

if __name__ == "__main__":
    main()