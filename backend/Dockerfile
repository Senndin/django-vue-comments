# Образ бекенду: Django + Daphne. Той самий Python, що й локально (A31).
FROM python:3.14-slim

# PYTHONDONTWRITEBYTECODE — не створювати .pyc у контейнері;
# PYTHONUNBUFFERED — віддавати логи одразу, а не після заповнення буфера.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Залежності копіюємо окремо від коду: поки requirements.txt не змінився,
# Docker бере цей шар із кешу і не перевстановлює пакети на кожну правку коду.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
