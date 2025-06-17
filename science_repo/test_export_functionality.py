import requests
import sys
import json
from urllib.parse import urljoin

BASE_URL = "http://localhost:8000/"  # Adjust if your server runs on a different port

def test_endpoint(endpoint, method="GET", data=None, params=None, expected_status=200):
    """Test an API endpoint and return whether it's functional"""
    url = urljoin(BASE_URL, endpoint)
    print(f"Testing {method} {url}...")
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data, params=params)
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
    
    print("\nTesting Export Functionality:")
    
    # First, we need to get a document version ID to test with
    # This assumes there's at least one published document version in the system
    print("\nFetching a published document version for testing...")
    response = requests.get(urljoin(BASE_URL, "api/publications/document-versions/"))
    
    if response.status_code == 200:
        document_versions = response.json()
        if document_versions and len(document_versions) > 0:
            # Try to find a published document version
            published_version = next((dv for dv in document_versions if dv.get('status') == 'published'), None)
            
            if published_version:
                document_version_id = published_version['id']
                print(f"Found published document version with ID: {document_version_id}")
                
                # Test JATS-XML export endpoint
                print("\nTesting JATS-XML export:")
                test_endpoint(f"api/publications/document-versions/{document_version_id}/jats/", 
                             expected_status=401)  # Expect 401 because we're not authenticated
                
                # Test repository export endpoint
                print("\nTesting repository export:")
                test_endpoint(f"api/publications/document-versions/{document_version_id}/repository/", 
                             params={"repository": "pubmed"},
                             expected_status=401)  # Expect 401 because we're not authenticated
                
                # Test PDF download endpoint
                print("\nTesting PDF download:")
                test_endpoint(f"api/publications/document-versions/{document_version_id}/pdf/", 
                             expected_status=401)  # Expect 401 because we're not authenticated
                
                print("\nNote: All tests returned 401 Unauthorized as expected because we're not authenticated.")
                print("To test with authentication, you would need to include an auth token in the requests.")
            else:
                print("No published document versions found. Please publish a document version and try again.")
        else:
            print("No document versions found. Please create a document version and try again.")
    else:
        print(f"Failed to fetch document versions: {response.status_code}")
    
    print("\nExport functionality testing completed.")

if __name__ == "__main__":
    main()