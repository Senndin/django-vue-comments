#!/bin/sh
# Старт контейнера бекенду: схема БД → статика → ASGI-сервер.
# set -e — будь-яка помилка зупиняє старт, щоб контейнер не піднявся «наполовину».
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# exec — daphne стає процесом №1 і отримує сигнали Docker (зупинка без kill по таймауту).
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
