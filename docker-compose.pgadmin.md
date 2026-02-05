# pgAdmin Setup Guide

pgAdmin has been added to the Docker Compose configuration. This provides a web-based interface for managing PostgreSQL databases.

## Accessing pgAdmin

1. Start the services:
   ```bash
   docker-compose up -d
   # or for development
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. Access pgAdmin at: http://localhost:5050

3. Login credentials:
   - **Email**: `admin@legalai.com` (or set `PGADMIN_EMAIL` in `.env`)
   - **Password**: `admin123` (or set `PGADMIN_PASSWORD` in `.env`)

## Connecting to PostgreSQL from pgAdmin

1. Right-click on "Servers" in the left panel
2. Select "Create" → "Server"
3. In the "General" tab:
   - **Name**: LegalAI Database (or any name you prefer)
4. In the "Connection" tab:
   - **Host name/address**: `postgres` (or `legalai-postgres` / `legalai-postgres-dev` depending on your compose file)
   - **Port**: `5432`
   - **Maintenance database**: `legalai` (or your `POSTGRES_DB` value)
   - **Username**: `legalai` (or your `POSTGRES_USER` value)
   - **Password**: `legalai123` (or your `POSTGRES_PASSWORD` value)
5. Click "Save"

## Environment Variables

You can customize the PostgreSQL and pgAdmin settings by adding these to your `.env` file:

```env
# PostgreSQL
POSTGRES_USER=legalai
POSTGRES_PASSWORD=legalai123
POSTGRES_DB=legalai

# pgAdmin
PGADMIN_EMAIL=admin@legalai.com
PGADMIN_PASSWORD=admin123
```

## Switching from SQLite to PostgreSQL

To use PostgreSQL instead of SQLite, update your backend `DATABASE_URL`:

```env
# In docker-compose.yml or docker-compose.dev.yml
DATABASE_URL=postgresql://legalai:legalai123@postgres:5432/legalai
```

Note: You'll need to run database migrations to set up the PostgreSQL schema.






