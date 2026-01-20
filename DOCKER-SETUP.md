# Docker Setup - Quick Start

## Prerequisites

Install Docker Desktop for Windows: https://www.docker.com/products/docker-desktop/

## Quick Start (Development)

```bash
# Start both services
docker-compose -f docker-compose.dev.yml up

# Or in detached mode (runs in background)
docker-compose -f docker-compose.dev.yml up -d
```

**That's it!** Both servers will start automatically.

- Backend: http://localhost:9000
- Frontend: http://localhost:3000

## Stop Services

```bash
docker-compose -f docker-compose.dev.yml down
```

## Production Build

```bash
docker-compose up --build
```

## Benefits

✅ **No Python/Node setup needed** - Everything is in containers  
✅ **Same environment every time** - No "works on my machine" issues  
✅ **Auto-restart on crash** - Containers restart automatically  
✅ **Isolated dependencies** - No conflicts with system packages  
✅ **Ready for GCP** - Same Docker setup works in Cloud Run  

## Troubleshooting

### Rebuild after code changes:
```bash
docker-compose -f docker-compose.dev.yml up --build
```

### View logs:
```bash
docker-compose -f docker-compose.dev.yml logs -f
```

### Stop and remove everything:
```bash
docker-compose -f docker-compose.dev.yml down -v
```

### Check if containers are running:
```bash
docker ps
```

## Environment Variables

Create `.env` file in project root:
```env
# Frontend
NEXT_PUBLIC_SUPABASE_URL=your_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_key

# Backend
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key  # Optional: use if LLM_PROVIDER=anthropic
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
SUPABASE_SERVICE_KEY=your_service_key
```

Docker Compose will automatically load these from the `.env` file in the project root.


