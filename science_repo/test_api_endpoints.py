import requests
import sys
import json
from urllib.parse import urljoin

BASE_URL = "http://localhost:8000/"  # Adjust if your server runs on a different port

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
        
        if response.status_code == expected_status:
            print(f"✅ Success: {response.status_code}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response: {response.text[:100]}...")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    # Test if server is running
    try:
        response = requests.get(BASE_URL)
        print(f"Server is running at {BASE_URL}")
    except:
        print(f"Server is not running at {BASE_URL}. Please start the server first.")
        sys.exit(1)
    
    # API Documentation endpoints
    test_endpoint("swagger/")
    test_endpoint("redoc/")
    
    # Core API endpoints
    test_endpoint("api/auth/login/", method="POST", data={"username": "test", "password": "test"}, expected_status=400)
    test_endpoint("api/auth/register/", method="POST", data={"username": "testuser", "email": "test@example.com", "password": "testpassword"}, expected_status=400)
    test_endpoint("api/auth/users/")
    test_endpoint("api/auth/analytics/summary/")
    
    # Publications API endpoints
    test_endpoint("api/publications/publications/")
    test_endpoint("api/publications/document-versions/")
    test_endpoint("api/publications/authors/")
    test_endpoint("api/publications/citation/formats/")
    test_endpoint("api/publications/citation/styles/")
    test_endpoint("api/publications/public/publications/")
    
    # Comments API endpoints
    test_endpoint("api/comments/comment-types/")
    test_endpoint("api/comments/comments/")
    
    # AI Assistant API endpoints
    test_endpoint("api/ai/ai-models/")
    test_endpoint("api/ai/ai-prompts/")
    
    print("\nAPI testing completed.")

if __name__ == "__main__":
    main()