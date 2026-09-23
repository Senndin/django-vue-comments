# Comments SPA

Single-page comment system with cascading replies: Django + DRF backend, Vue 3 frontend,
PostgreSQL, Redis, WebSocket updates, background queue and JWT auth — all in Docker.

Test assignment for dZENcode (Junior+ level).

## Status

Work in progress, built stage by stage. Right now the repository contains the backend
skeleton only: Django project, custom user model, settings from environment variables.

## Stack

Python 3.14 · Django 5.2 LTS · Django REST Framework · PostgreSQL 17 · Redis 7 ·
Django Channels · Celery · Vue 3 · Vite · Docker Compose · nginx

## Local development (backend)

```bash
cp .env.example .env
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

Tests and linter:

```bash
pytest
ruff check . && ruff format --check .
```

A full README (features, architecture, API, Docker quick start, environment variables)
comes with the final stage.
