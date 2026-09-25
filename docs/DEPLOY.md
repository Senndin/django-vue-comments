# Deployment

How to run the project on a fresh VDS (Ubuntu 24.04 is assumed; any distribution with
Docker works the same way). Everything runs in containers, so nothing but Docker is
installed on the host.

Estimated time: 15 minutes.

---

## 1. Prepare the server

```bash
ssh root@<server-ip>
adduser deploy && usermod -aG sudo deploy      # do not work as root
su - deploy
```

Install Docker Engine and the Compose plugin:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker                                   # apply the new group without re-login
docker compose version                          # v2.x expected
```

Open the ports:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp        # only if you are going to enable HTTPS
sudo ufw enable
```

> Docker publishes ports past `ufw`, so nothing else must be exposed by accident:
> in `docker-compose.yml` PostgreSQL, Redis and the backend are bound to `127.0.0.1`
> on purpose. Only nginx listens on `0.0.0.0`.

---

## 2. Get the code and the configuration

```bash
git clone <repository-url> ~/comments
cd ~/comments
cp .env.example .env
```

Edit `.env` — at minimum:

```dotenv
DJANGO_SECRET_KEY=<a long random string>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
POSTGRES_PASSWORD=<a strong password>
```

Generate the secret key:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

If you have no domain yet, put the server IP into `DJANGO_ALLOWED_HOSTS` and
`http://<server-ip>` into `DJANGO_CSRF_TRUSTED_ORIGINS`.

Optional — real e-mail notifications instead of the worker log:

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=notifications@example.com
EMAIL_HOST_PASSWORD=<password>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=notifications@example.com
```

---

## 3. First run

```bash
docker compose up --build -d
docker compose ps            # db and redis must be "healthy"
docker compose logs -f backend
```

The backend applies migrations and collects static files on start, so no extra commands are
needed. Create an administrator:

```bash
docker compose exec backend python manage.py createsuperuser
```

Check the result: `http://<domain-or-ip>/` — the comment list, `…/admin/` — the admin site.

---

## 4. HTTPS (optional but recommended)

The simplest way is a certificate from Let's Encrypt obtained on the host and passed into
the nginx container.

```bash
sudo apt install certbot
sudo systemctl stop docker.socket 2>/dev/null || true
docker compose stop frontend                    # free port 80 for the challenge
sudo certbot certonly --standalone -d example.com -d www.example.com
docker compose start frontend
```

Add the certificate and a TLS server block to `frontend/nginx.conf`:

```nginx
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name example.com www.example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # …the rest of the configuration stays exactly as it is in the repository…
}
```

Mount the certificates and publish 443 in `docker-compose.yml`:

```yaml
  frontend:
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - media:/app/media:ro
      - static:/app/staticfiles:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
```

Then switch the application into HTTPS mode:

```dotenv
DJANGO_HTTPS=True
```

and restart: `docker compose up -d --build`.

Renewal (certbot installs a timer itself); nginx has to pick up the new files:

```bash
sudo certbot renew --pre-hook "docker compose -f ~/comments/docker-compose.yml stop frontend" \
                   --post-hook "docker compose -f ~/comments/docker-compose.yml start frontend"
```

> `DJANGO_HTTPS=True` also enables HSTS for one hour. Raise
> `SECURE_HSTS_SECONDS` in `backend/config/settings.py` only after you are sure the
> certificate renews correctly: the header is hard to take back.

---

## 5. Updating

```bash
cd ~/comments
git pull
docker compose up -d --build
```

Migrations and `collectstatic` run automatically on backend start. Nothing else is needed;
the database lives in the `pgdata` volume and survives rebuilds.

---

## 6. Backups

The database and the uploaded files are the only state worth keeping.

```bash
# database
docker compose exec -T db pg_dump -U comments comments | gzip > backup-$(date +%F).sql.gz

# uploaded files
docker run --rm -v django-vue-comments_media:/media -v "$PWD":/backup alpine \
  tar czf /backup/media-$(date +%F).tar.gz -C /media .
```

Restore:

```bash
gunzip -c backup-2026-09-25.sql.gz | docker compose exec -T db psql -U comments comments
```

---

## 7. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `400 Bad Request` on every page | The host is missing from `DJANGO_ALLOWED_HOSTS`. |
| Admin login fails with a CSRF error | Add the site address to `DJANGO_CSRF_TRUSTED_ORIGINS`, with the scheme. |
| The admin site has no styles | `collectstatic` did not run — check `docker compose logs backend`. |
| Attachments are 404 | The `media` volume is not mounted into the `frontend` service. |
| New comments do not appear live | WebSocket is blocked: check that nginx passes `Upgrade`/`Connection` and that the proxy in front of the server (if any) allows WebSocket. |
| `413 Request Entity Too Large` | The file is bigger than the 6 MB limit in `frontend/nginx.conf`. |
| Notification e-mails never leave | Without SMTP settings they are printed in `docker compose logs worker` — this is the default behaviour. |
| Everything is slow after a restart | The cache is cold; the first request to each page rebuilds it. |
