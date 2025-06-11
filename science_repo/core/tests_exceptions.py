from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import json

class APIExceptionHandlingTest(TestCase):
    """
    Test that API endpoints return JSON responses even when errors occur.
    """
    
    def setUp(self):
        self.client = APIClient()
    
    def test_404_returns_json(self):
        """
        Test that a 404 error returns a JSON response.
        """
        # Make a request to a non-existent endpoint with 'api' in the URL
        response = self.client.get('/api/non-existent-endpoint/')
        
        # Check that the response status code is 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Check that the response content type is JSON
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Try to parse the response content as JSON
        try:
            json_content = json.loads(response.content)
            # Check that the JSON contains a 'detail' field
            self.assertIn('detail', json_content)
        except json.JSONDecodeError:
            self.fail("Response content is not valid JSON")
    
    def test_method_not_allowed_returns_json(self):
        """
        Test that a method not allowed error returns a JSON response.
        """
        # Get a URL that exists but doesn't support POST
        url = reverse('csrf_token')
        
        # Make a POST request to the URL
        response = self.client.post(url)
        
        # Check that the response status code is 405 (Method Not Allowed)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Check that the response content type is JSON
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Try to parse the response content as JSON
        try:
            json_content = json.loads(response.content)
            # Check that the JSON contains a 'detail' field
            self.assertIn('detail', json_content)
        except json.JSONDecodeError:
            self.fail("Response content is not valid JSON")