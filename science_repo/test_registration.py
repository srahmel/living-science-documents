import requests
import sys
import json
import uuid
from urllib.parse import urljoin

# The URL provided in the issue description
BASE_URL = "https://v2202209183503201737.happysrv.de/srahmel/living-science-documents/"

def test_registration():
    """Test the registration endpoint"""
    url = urljoin(BASE_URL, "api/auth/register/")
    print(f"Testing registration at {url}...")
    
    # Generate a unique username to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    
    # Create registration data with all required fields
    registration_data = {
        "username": f"testuser_{unique_id}",
        "password": "TestPassword123!",
        "password2": "TestPassword123!",
        "email": f"test_{unique_id}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "dsgvo_consent": True,
        "affiliation": "Test University",
        "research_field": "Computer Science",
        "qualification": "PhD"
    }
    
    try:
        response = requests.post(url, json=registration_data)
        print(f"Status code: {response.status_code}")
        
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response text: {response.text[:200]}...")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            
            # Test login with the new user
            login_url = urljoin(BASE_URL, "api/auth/login/")
            login_data = {
                "username": registration_data["username"],
                "password": registration_data["password"]
            }
            
            print(f"\nTesting login with new user at {login_url}...")
            login_response = requests.post(login_url, json=login_data)
            print(f"Status code: {login_response.status_code}")
            
            try:
                print(f"Response: {json.dumps(login_response.json(), indent=2)}")
                if login_response.status_code == 200:
                    print("✅ Login successful!")
                    
                    # Test accessing a protected endpoint with the token
                    token = login_response.json().get("access")
                    if token:
                        users_url = urljoin(BASE_URL, "api/auth/users/")
                        headers = {"Authorization": f"Bearer {token}"}
                        
                        print(f"\nTesting access to protected endpoint at {users_url}...")
                        users_response = requests.get(users_url, headers=headers)
                        print(f"Status code: {users_response.status_code}")
                        
                        if users_response.status_code == 200:
                            print("✅ Access to protected endpoint successful!")
                        else:
                            print("❌ Access to protected endpoint failed!")
                else:
                    print("❌ Login failed!")
            except:
                print(f"Response text: {login_response.text[:200]}...")
        else:
            print("❌ Registration failed!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_registration()