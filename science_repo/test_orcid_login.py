import requests
import sys
import json
from urllib.parse import urljoin

# Base URL for the API server
BASE_URL = "https://v2202209183503201737.happysrv.de/"

def test_orcid_login():
    """Test the ORCID login endpoint"""
    url = urljoin(BASE_URL, "api/auth/orcid/login/")
    print(f"Testing ORCID login at {url}...")
    
    try:
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            # Check if the response contains the auth_url field
            if response.status_code == 200 and 'auth_url' in response.json():
                auth_url = response.json()['auth_url']
                print(f"✅ ORCID login endpoint is working!")
                print(f"Auth URL: {auth_url}")
                
                # We won't actually redirect to this URL as it would require user interaction
                print("\nNote: The auth URL would redirect to ORCID for authentication.")
                print("This test only verifies that the endpoint is accessible and returns the expected response structure.")
            else:
                print("❌ ORCID login endpoint is not returning the expected response structure!")
        except:
            print(f"Response text: {response.text[:200]}...")
            print("❌ ORCID login endpoint is not returning valid JSON!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_orcid_login()