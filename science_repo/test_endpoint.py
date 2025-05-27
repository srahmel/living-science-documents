from django.test import Client
from django.urls import reverse

def test_endpoint():
    client = Client()

    # Try different URL patterns
    urls_to_try = [
        '/api/auth/register/',
        '/srahmel/living-science-documents/api/auth/register/',
        '/api/auth/auth/register/',
        '/srahmel/living-science-documents/api/auth/auth/register/'
    ]

    for url in urls_to_try:
        print(f"Trying URL: {url}")
        response = client.get(url)
        print(f"Status code: {response.status_code}")
        print(f"Content: {response.content[:100]}\n")

if __name__ == "__main__":
    import os
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "science_repo.settings")
    django.setup()

    # Add 'testserver' to ALLOWED_HOSTS
    from django.conf import settings
    settings.ALLOWED_HOSTS.append('testserver')

    test_endpoint()
