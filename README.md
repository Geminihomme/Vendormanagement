# Vendor Management Platform

A web application for managing vendors, contracts, and compliance tracking.

## Architecture

```
User's Browser (React Frontend)
        |
        v
   FastAPI Backend  (Python)
        |
        v
   PostgreSQL Database
```

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### Running with Docker
```bash
docker-compose up --build
```

This starts:
- **Backend API** at http://localhost:8000
- **Frontend** at http://localhost:3000
- **PostgreSQL** database on port 5432

### Running for Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

## Project Structure
```
Vendormanagement/
├── backend/          # Python/FastAPI - handles business logic and data
│   ├── app/
│   │   ├── api/      # API endpoints (URLs your frontend calls)
│   │   ├── models/   # Database table definitions
│   │   ├── schemas/  # Data validation rules
│   │   ├── services/ # Business logic
│   │   └── main.py   # App entry point
│   └── requirements.txt
├── frontend/         # React/TypeScript - the user interface
│   ├── src/
│   │   ├── components/  # Reusable UI pieces
│   │   ├── pages/       # Full page views
│   │   ├── services/    # Code that talks to the backend
│   │   └── types/       # TypeScript type definitions
│   └── package.json
└── docker-compose.yml  # Runs everything together
```
