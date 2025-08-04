import requests
import json
import sys
import time
from urllib.parse import urlparse, parse_qs

# Configuration
API_BASE_URL = "https://v2202209183503201737.happysrv.de/srahmel/living-science-documents/api"
EMAIL = "test@example.com"  # Replace with a valid test email
PASSWORD = "testpassword123"  # Initial password
NEW_PASSWORD = "newtestpassword123"  # New password after reset

# Test endpoints
LOGIN_URL = f"{API_BASE_URL}/auth/login/"
PASSWORD_RESET_URL = f"{API_BASE_URL}/api/auth/password-reset/"
PASSWORD_RESET_CONFIRM_URL = f"{API_BASE_URL}/api/auth/password-reset/confirm/"

def print_step(message):
    """Print a step message with formatting"""
    print("\n" + "="*80)
    print(f"STEP: {message}")
    print("="*80)

def print_response(response):
    """Print response details"""
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_login(username, password):
    """Test login with given credentials"""
    print_step(f"Testing login with username: {username}, password: {password}")
    
    data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(LOGIN_URL, json=data)
    print_response(response)
    
    if response.status_code == 200:
        print("✅ Login successful!")
        return response.json().get("access")
    else:
        print("❌ Login failed!")
        return None

def request_password_reset(email):
    """Request a password reset email"""
    print_step(f"Requesting password reset for email: {email}")
    
    data = {
        "email": email
    }
    
    response = requests.post(PASSWORD_RESET_URL, json=data)
    print_response(response)
    
    if response.status_code == 200:
        print("✅ Password reset request successful!")
        print("📧 Check your email for the reset link")
        return True
    else:
        print("❌ Password reset request failed!")
        return False

def reset_password(token, email, new_password):
    """Reset password with token"""
    print_step(f"Resetting password with token for email: {email}")
    
    data = {
        "token": token,
        "email": email,
        "password": new_password
    }
    
    response = requests.post(PASSWORD_RESET_CONFIRM_URL, json=data)
    print_response(response)
    
    if response.status_code == 200:
        print("✅ Password reset successful!")
        return True
    else:
        print("❌ Password reset failed!")
        return False

def main():
    # Step 1: Request password reset (skipping initial login test)
    print_step("PASSWORD RESET REQUEST")
    reset_requested = request_password_reset(EMAIL)
    
    if not reset_requested:
        print("Password reset request failed.")
        return
    
    # Step 3: Get reset token from user input
    print("\n" + "="*80)
    print("MANUAL STEP REQUIRED")
    print("="*80)
    print("Check your email for the password reset link.")
    print("Extract the 'token' parameter from the URL and enter it below:")
    token = input("Enter token: ")
    
    if not token:
        print("No token provided. Exiting test.")
        return
    
    # Step 4: Reset password
    reset_success = reset_password(token, EMAIL, NEW_PASSWORD)
    
    if not reset_success:
        print("Password reset failed.")
        return
    
    # Step 5: Test login with new password
    print_step("TESTING LOGIN WITH NEW PASSWORD")
    time.sleep(2)  # Small delay to ensure password reset is processed
    new_access_token = test_login(EMAIL, NEW_PASSWORD)
    
    if new_access_token:
        print("\n" + "="*80)
        print("🎉 PASSWORD RESET FLOW SUCCESSFUL! 🎉")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ PASSWORD RESET FLOW FAILED! ❌")
        print("="*80)

if __name__ == "__main__":
    main()