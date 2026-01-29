# pgAdmin Connection Guide - Step by Step

## The user EXISTS in the database - here's how to see it:

## Step 1: Access pgAdmin
- Open http://localhost:5050 in your browser
- Login with:
  - Email: `admin@legalai.com`
  - Password: `admin123`

## Step 2: Add Server Connection

1. **Right-click on "Servers"** in the left panel
2. Select **"Create" → "Server"**

3. **General Tab:**
   - Name: `LegalAI Database` (or any name you prefer)

4. **Connection Tab - USE THESE EXACT SETTINGS:**
   ```
   Host name/address: postgres
   Port: 5432
   Maintenance database: legalai
   Username: legalai
   Password: legalai123
   ```
   
   **IMPORTANT:** 
   - If connecting from pgAdmin running in Docker, use `postgres` as the hostname
   - If connecting from your local machine (not Docker), use `localhost` as the hostname
   - Make sure "Save password" is checked

5. Click **"Save"**

## Step 3: View the User

1. Expand: **Servers → LegalAI Database → Databases → legalai → Schemas → public → Tables**
2. Right-click on **`users`** table
3. Select **"View/Edit Data" → "All Rows"**

You should see:
```
id | email                        | full_name      | role  | tenant_id | is_active
1  | jgelsomino@foundry360.us     | Joe Gelsomino  | admin | 1         | t
```

## Troubleshooting

### If you see "Connection refused":
- Make sure the PostgreSQL container is running: `docker ps | grep postgres`
- Try using `localhost` instead of `postgres` if connecting from outside Docker

### If you see "Authentication failed":
- Username: `legalai`
- Password: `legalai123`
- Database: `legalai`

### If the table appears empty:
- Make sure you're looking at the `public` schema
- Refresh the table (right-click → Refresh)
- Check you're connected to the `legalai` database, not `postgres`

## Verify via Command Line

If you still can't see it in pgAdmin, verify it exists:
```bash
docker exec legalai-postgres-dev psql -U legalai -d legalai -c "SELECT * FROM users;"
```

This should show the user. If it does, the issue is with your pgAdmin connection settings.



