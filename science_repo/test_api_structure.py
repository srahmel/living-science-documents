import importlib
import inspect
from django.urls import URLPattern, URLResolver
from django.urls.resolvers import RoutePattern, RegexPattern
from django.core.management import call_command
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'science_repo.settings')
django.setup()

# Import URL modules
from science_repo.urls import urlpatterns as main_urlpatterns
from core.urls import urlpatterns as core_urlpatterns
from publications.urls import urlpatterns as publications_urlpatterns
from comments.urls import urlpatterns as comments_urlpatterns
from ai_assistant.urls import urlpatterns as ai_urlpatterns

def get_pattern_name(pattern):
    """Extract the name from a URL pattern"""
    if hasattr(pattern, 'name'):
        return pattern.name
    return None

def get_pattern_path(pattern):
    """Extract the path from a URL pattern"""
    if isinstance(pattern.pattern, RoutePattern):
        return pattern.pattern._route
    elif isinstance(pattern.pattern, RegexPattern):
        return pattern.pattern.regex.pattern
    return str(pattern.pattern)

def get_view_name(view_func):
    """Get the name of a view function or class"""
    if hasattr(view_func, 'view_class'):
        return view_func.view_class.__name__
    elif hasattr(view_func, '__name__'):
        return view_func.__name__
    return str(view_func)

def check_url_patterns(patterns, prefix=''):
    """Recursively check URL patterns and their associated views"""
    results = []

    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            # This is a URL resolver (includes other URL patterns)
            new_prefix = prefix + get_pattern_path(pattern)
            sub_results = check_url_patterns(pattern.url_patterns, new_prefix)
            results.extend(sub_results)
        elif isinstance(pattern, URLPattern):
            # This is a URL pattern (points to a view)
            path = prefix + get_pattern_path(pattern)
            name = get_pattern_name(pattern)
            view = get_view_name(pattern.callback)

            results.append({
                'path': path,
                'name': name,
                'view': view,
                'status': 'Unknown'  # We can't determine status without making a request
            })

    return results

def main():
    print("Checking API structure...")

    # Check main URL patterns
    print("\n=== Main URL Patterns ===")
    main_results = check_url_patterns(main_urlpatterns, '/')
    for result in main_results:
        print(f"Path: {result['path']}")
        print(f"Name: {result['name']}")
        print(f"View: {result['view']}")
        print("---")

    # Check core URL patterns
    print("\n=== Core API Endpoints ===")
    core_results = check_url_patterns(core_urlpatterns, '/api/auth/')
    for result in core_results:
        print(f"Path: {result['path']}")
        print(f"Name: {result['name']}")
        print(f"View: {result['view']}")
        print("---")

    # Check publications URL patterns
    print("\n=== Publications API Endpoints ===")
    pub_results = check_url_patterns(publications_urlpatterns, '/api/publications/')
    for result in pub_results:
        print(f"Path: {result['path']}")
        print(f"Name: {result['name']}")
        print(f"View: {result['view']}")
        print("---")

    # Check comments URL patterns
    print("\n=== Comments API Endpoints ===")
    comments_results = check_url_patterns(comments_urlpatterns, '/api/comments/')
    for result in comments_results:
        print(f"Path: {result['path']}")
        print(f"Name: {result['name']}")
        print(f"View: {result['view']}")
        print("---")

    # Check AI assistant URL patterns
    print("\n=== AI Assistant API Endpoints ===")
    ai_results = check_url_patterns(ai_urlpatterns, '/api/ai/')
    for result in ai_results:
        print(f"Path: {result['path']}")
        print(f"Name: {result['name']}")
        print(f"View: {result['view']}")
        print("---")

    # Summary
    total_endpoints = len(main_results) + len(core_results) + len(pub_results) + len(comments_results) + len(ai_results)
    print(f"\nTotal API endpoints found: {total_endpoints}")
    print("API structure check completed.")

if __name__ == "__main__":
    main()
