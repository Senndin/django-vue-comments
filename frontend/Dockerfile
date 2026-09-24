# Збірка SPA і роздача її через nginx (T5, етап 16).

FROM node:22-alpine AS build

WORKDIR /app

# Залежності окремим шаром: доки package-lock.json не змінився, npm ci не перезапускається.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Другий етап: у підсумковий образ потрапляє лише зібрана статика — ані Node, ані
# node_modules у ньому немає (образ менший і поверхня атаки теж).
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
