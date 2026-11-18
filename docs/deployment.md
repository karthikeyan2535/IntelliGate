# IntelliGate Deployment Guide

IntelliGate provides a containerized setup supporting local developer testing, on-premise clusters, and cloud environments.

---

## 1. Quick Start with Docker Compose

Ensure Docker and Docker Compose are installed, then clone the repository:

```bash
git clone https://github.com/your-org/intelligate.git
cd intelligate
```

Copy the example environment configuration:
```bash
cp .env.example .env
```

Generate secure encryption secrets:
```bash
python -c "from cryptography.fernet import Fernet; import secrets; print('FERNET_KEY=' + Fernet.generate_key().decode()); print('SECRET_KEY=' + secrets.token_hex(32))"
```
Paste the outputs into `.env`.

Launch the full stack:
```bash
docker compose up -d
```

### Services Started:
- **IntelliGate Backend**: `http://localhost:8000` (FastAPI, OpenAPI docs at `/docs`)
- **IntelliGate Dashboard**: `http://localhost:3000` (Next.js Dashboard)
- **PostgreSQL 17**: `localhost:5432`
- **Redis 7.4**: `localhost:6379`
- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3001` (user: `admin`, password: `admin`)

---

## 2. Local Development (Without Docker)

### Backend:
```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\activate, On Linux/Mac: source venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

### Frontend:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

