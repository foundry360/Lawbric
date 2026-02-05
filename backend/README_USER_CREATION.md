# Creating Test Users

Since we've migrated to JWT authentication, you can create test users in two ways:

## Option 1: Using the Register API (Recommended)

Make sure your backend server is running on `http://localhost:9001`, then:

```bash
cd backend
python create_user_simple.py admin@test.com password123 "Admin User" admin
```

Or use curl (Linux/Mac):
```bash
curl -X POST http://localhost:9001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"password123","full_name":"Admin User","role":"admin"}'
```

Or use PowerShell (Windows):
```powershell
Invoke-WebRequest -Uri "http://localhost:9001/api/v1/auth/register" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email":"admin@test.com","password":"password123","full_name":"Admin User","role":"admin"}'
```

## Option 2: Direct Database Insert (If backend not running)

If the backend isn't running, you can use the `create_test_user.py` script (requires bcrypt to work properly):

```bash
cd backend
python create_test_user.py admin@test.com password123 "Admin User" admin
```

## Available Roles

- `admin` - Full admin access
- `attorney` - Attorney role
- `paralegal` - Paralegal role (default)

## Login

After creating a user, you can login at the login page with:
- Email: The email you used
- Password: The password you used







