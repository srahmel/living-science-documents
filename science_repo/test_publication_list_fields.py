import requests
import json

# URL of the API endpoint
url = "http://localhost:8000/api/publications/publications/"

# Make the request
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    
    # Check if there are any results
    if 'results' in data and len(data['results']) > 0:
        # Get the first publication
        publication = data['results'][0]
        
        # Print the publication details
        print("Publication details:")
        print(f"ID: {publication.get('id')}")
        print(f"Meta DOI: {publication.get('meta_doi')}")
        print(f"Title: {publication.get('title')}")
        print(f"Short Title: {publication.get('short_title')}")
        print(f"Created At: {publication.get('created_at')}")
        print(f"Status: {publication.get('status')}")
        print(f"Current Version Number: {publication.get('current_version_number')}")
        
        # Check if authors field exists
        if 'authors' in publication:
            print("\nAuthors:")
            for author in publication['authors']:
                print(f"  - {author.get('name')} ({author.get('email')})")
                if author.get('user_details'):
                    print(f"    User: {author['user_details'].get('username')}")
        else:
            print("\nAuthors field is missing!")
        
        # Check if created_by field exists
        if 'created_by' in publication:
            print("\nCreated By:")
            created_by = publication['created_by']
            if created_by:
                print(f"  User ID: {created_by.get('id')}")
                print(f"  Username: {created_by.get('username')}")
                print(f"  Full Name: {created_by.get('full_name')}")
                print(f"  ORCID: {created_by.get('orcid')}")
            else:
                print("  No creator information available")
        else:
            print("\nCreated By field is missing!")
        
        # Check if metadata field exists
        if 'metadata' in publication:
            print("\nMetadata:")
            metadata = publication['metadata']
            if metadata:
                print(json.dumps(metadata, indent=2))
            else:
                print("  No metadata available")
        else:
            print("\nMetadata field is missing!")
        
        # Print the full publication JSON for reference
        print("\nFull publication JSON:")
        print(json.dumps(publication, indent=2))
    else:
        print("No publications found in the response.")
else:
    print(f"Request failed with status code {response.status_code}")
    print(response.text)