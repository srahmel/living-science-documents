from django.urls import reverse

def test_reverse():
    try:
        url = reverse('register')
        print(f"URL for 'register': {url}")
    except Exception as e:
        print(f"Error resolving 'register': {e}")

    try:
        url = reverse('login')
        print(f"URL for 'login': {url}")
    except Exception as e:
        print(f"Error resolving 'login': {e}")

if __name__ == "__main__":
    import os
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "science_repo.settings")
    django.setup()
    test_reverse()
