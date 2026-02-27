# Docker Guide — CognOS

Quick start with Docker. Zero configuration needed.

## Quick Start (30 seconds)

```bash
# Build locally
docker build -t base76/cognos:latest .

# Run
docker run -p 8788:8788 base76/cognos:latest

# Test in another terminal
curl http://localhost:8788/healthz
# Returns: {"status":"ok","service":"operational-cognos-gateway"}
```

## Using Docker Hub (Pre-built)

```bash
docker run -p 8788:8788 base76/cognos:latest
```

## Try the API

### Health Check
```bash
curl http://localhost:8788/healthz
```

### Chat Completions (Mock Mode)
```bash
curl -X POST http://localhost:8788/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello, what is 2+2?"}],
    "cognos": {"mode": "monitor"}
  }'
```

Response includes `"cognos"` envelope with decision, risk, trace_id:
```json
{
  "id": "chatcmpl_...",
  "choices": [...],
  "cognos": {
    "decision": "PASS",
    "risk": 0.12,
    "trace_id": "tr_...",
    "signals": {...},
    "attestation": {...}
  }
}
```

## Docker Compose (Recommended for Development)

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f cognos

# Stop
docker-compose down
```

Data persists in `cognos-data` volume.

## Environment Variables

### Default (Zero Config)
```bash
COGNOS_MOCK_UPSTREAM=true       # Use mock responses (no API keys needed)
COGNOS_TRACE_DB=/data/traces.sqlite3
```

### Live Upstream (Optional)

#### OpenAI
```bash
docker run -p 8788:8788 \
  -e COGNOS_MOCK_UPSTREAM=false \
  -e COGNOS_UPSTREAM_BASE_URL="https://api.openai.com/v1" \
  -e COGNOS_UPSTREAM_API_KEY="sk-..." \
  base76/cognos:latest
```

#### Claude (via OpenRouter)
```bash
docker run -p 8788:8788 \
  -e COGNOS_MOCK_UPSTREAM=false \
  -e COGNOS_UPSTREAM_BASE_URL="https://openrouter.ai/api/v1" \
  -e COGNOS_UPSTREAM_API_KEY="sk-or-..." \
  base76/cognos:latest
```

#### Local Ollama
```bash
# First, make sure Ollama is running on your machine
# Then run with local network access:
docker run -p 8788:8788 \
  --network host \
  -e COGNOS_MOCK_UPSTREAM=false \
  -e COGNOS_UPSTREAM_BASE_URL="http://localhost:11434/v1" \
  -e COGNOS_ALLOW_NO_UPSTREAM_AUTH=true \
  base76/cognos:latest
```

## Data Persistence

### Option 1: Named Volume (Recommended)
```bash
docker run -p 8788:8788 \
  -v cognos-data:/data \
  base76/cognos:latest
```

Traces persist across container restarts.

### Option 2: Host Directory
```bash
mkdir -p ./cognos-data
docker run -p 8788:8788 \
  -v $(pwd)/cognos-data:/data \
  base76/cognos:latest
```

Query traces from host:
```bash
sqlite3 cognos-data/traces.sqlite3 "SELECT trace_id, decision FROM traces LIMIT 10;"
```

## Production Deployment

### Security Checklist

- [ ] Use non-root user (included in Dockerfile)
- [ ] Set `COGNOS_GATEWAY_API_KEY` for authentication
- [ ] Use health checks (included in Dockerfile)
- [ ] Mount `/data` to persistent storage
- [ ] Use environment variables (not .env file)
- [ ] Set resource limits

### Example: Production Run

```bash
docker run -d \
  --name cognos-prod \
  --restart unless-stopped \
  --memory 512m \
  --cpus 1.0 \
  -p 8788:8788 \
  -e COGNOS_MOCK_UPSTREAM=false \
  -e COGNOS_UPSTREAM_BASE_URL="https://openrouter.ai/api/v1" \
  -e COGNOS_UPSTREAM_API_KEY="sk-or-..." \
  -e COGNOS_GATEWAY_API_KEY="your-secret-key" \
  -e COGNOS_TRACE_DB=/data/traces.sqlite3 \
  -v cognos-data:/data \
  base76/cognos:latest
```

### With Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name cognos.example.com;

    location / {
        proxy_pass http://localhost:8788;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Building Custom Images

### Override Default Settings
```bash
# Create custom Dockerfile
FROM base76/cognos:latest
ENV COGNOS_UPSTREAM_BASE_URL="https://api.mycompany.com/v1"
```

Build:
```bash
docker build -t my-cognos:latest .
docker run -p 8788:8788 my-cognos:latest
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs <container_id>

# Run with verbose output
docker run --rm base76/cognos:latest python3 -m uvicorn --help
```

### Health Check Failing
```bash
# Check if port is accessible
docker exec <container_id> curl http://localhost:8788/healthz

# Manual health check
curl -v http://localhost:8788/healthz
```

### Database Locked
```bash
# SQLite may lock if multiple processes access simultaneously
# Solution: Use a proper database (PostgreSQL) for production
# Temporary: Restart container to reset locks
docker restart <container_id>
```

### Memory Issues
```bash
# Increase memory allocation
docker run -p 8788:8788 --memory 1g base76/cognos:latest

# Check usage
docker stats
```

## Publishing to Docker Hub

(For maintainers)

```bash
# Build for multiple architectures (requires docker buildx)
docker buildx build --platform linux/amd64,linux/arm64 \
  -t base76/cognos:latest \
  -t base76/cognos:v0.1.0 \
  --push .

# Or single arch
docker build -t base76/cognos:latest .
docker push base76/cognos:latest
```

## Integration Examples

### Python with Docker
```python
import subprocess
import time
import httpx

# Start container
subprocess.Popen(["docker", "run", "-p", "8788:8788", "base76/cognos:latest"])
time.sleep(3)  # Wait for startup

# Use CognOS
client = httpx.Client()
response = client.post("http://localhost:8788/v1/chat/completions", json={
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hi"}],
    "cognos": {"mode": "monitor"}
})
print(response.json()["cognos"]["decision"])
```

### Node.js with Docker
```javascript
const axios = require('axios');

const response = await axios.post('http://localhost:8788/v1/chat/completions', {
  model: 'gpt-4o-mini',
  messages: [{ role: 'user', content: 'Hi' }],
  cognos: { mode: 'monitor' }
});

console.log(response.data.cognos.decision);
```

## Container Specifications

- **Base Image:** `python:3.12-slim`
- **Image Size:** ~150 MB
- **User:** `cognos:cognos` (UID 1000, non-root)
- **Working Dir:** `/app`
- **Data Dir:** `/data` (mounted volume)
- **Port:** `8788`
- **Health Check:** Every 30s (5s start grace)

## Next Steps

1. **Build:** `docker build -t base76/cognos .`
2. **Run:** `docker run -p 8788:8788 base76/cognos`
3. **Test:** `curl http://localhost:8788/healthz`
4. **Integrate:** Use from your app or via SDK
5. **Deploy:** Use `docker-compose` for multi-service setups

---

**Need help?** Check `README.md` or `TESTING_SETUP.md`.
