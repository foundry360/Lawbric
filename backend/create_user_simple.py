#!/usr/bin/env python
"""
Simple script to create a test user via the register API endpoint
Usage: python create_user_simple.py <email> <password> [full_name] [role]
Example: python create_user_simple.py admin@test.com password123 "Admin User" admin
"""

import sys
import requests
import json

API_URL = "http://localhost:9001"

def create_user(email: str, password: str, full_name: str = None, role: str = "paralegal"):
    """Create a user via the register endpoint"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": full_name or email.split('@')[0],
                "role": role,
                "title": "attorney"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] User created successfully!")
            print(f"   Email: {email}")
            print(f"   Full Name: {full_name or email.split('@')[0]}")
            print(f"   Role: {role}")
            print(f"\nYou can now login with:")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            print(f"\nAccess token: {data.get('access_token', 'N/A')[:50]}...")
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error')
            print(f"[ERROR] Failed to create user: {error_msg}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to backend at {API_URL}")
        print("   Make sure the backend server is running on port 9000")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to create user: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_user_simple.py <email> <password> [full_name] [role]")
        print("\nExample:")
        print("  python create_user_simple.py admin@test.com password123")
        print("  python create_user_simple.py admin@test.com password123 'Admin User' admin")
        print("\nRoles: admin, attorney, paralegal (default: paralegal)")
        print("\nNote: Backend server must be running on http://localhost:9001")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else None
    role = sys.argv[4] if len(sys.argv) > 4 else "paralegal"
    
    create_user(email, password, full_name, role)







