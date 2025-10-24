# Getting Started with the Udoy Learning Platform

This repository contains a monorepo with both the FastAPI backend and the Vite-powered React frontend. Follow the steps below to set up each service locally.

## Prerequisites
- Python 3.11+
- Node.js 18+
- npm 9+
- Docker and Docker Compose (optional, for containerized setup)

## Backend Setup (FastAPI)
1. Change into the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Visit the interactive API docs at `http://127.0.0.1:8000/docs`.

## Frontend Setup (Vite + React)
1. In a new terminal, move into the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Provide the backend API URL in `.env` if it differs from the default `http://localhost:8000`:
   ```bash
   echo "VITE_API_BASE_URL=http://localhost:8000" > .env
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```
5. Access the frontend at the URL shown in the terminal output (typically `http://localhost:5173`).

## Containerized Development (Optional)
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Build and start both services:
   ```bash
   docker compose up --build
   ```
3. Access the frontend at `http://localhost:8080` and the API at `http://localhost:8000`.

## Seeding Admin Credentials
On first startup, the backend seeds an administrator account using the credentials defined in the environment variables. The defaults are:
- **Email:** `admin@udoy.local`
- **Password:** `admin123`

Use these credentials to log into the platform and perform initial configuration tasks.
