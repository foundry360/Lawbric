#!/usr/bin/env python
"""Test password verification for the super admin user"""

import sys
import os
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

POSTGRES_URL = "postgresql://legalai:legalai123@localhost:5432/legalai"

engine = create_engine(POSTGRES_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Get the user's hashed password
    result = db.execute(
        text("SELECT hashed_password FROM users WHERE email = 'admin@superuser.com'")
    )
    row = result.fetchone()
    
    if not row:
        print("User not found!")
        sys.exit(1)
    
    hashed_password = row[0]
    print(f"Hashed password (first 50 chars): {hashed_password[:50]}...")
    
    # Test password verification
    password = "12345678"
    password_bytes = password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    
    is_valid = bcrypt.checkpw(password_bytes, hash_bytes)
    print(f"Password '12345678' is valid: {is_valid}")
    
    # Also test with passlib
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        is_valid_passlib = pwd_context.verify(password, hashed_password)
        print(f"Password '12345678' is valid (passlib): {is_valid_passlib}")
    except Exception as e:
        print(f"Passlib test failed: {e}")
        
finally:
    db.close()
    engine.dispose()

