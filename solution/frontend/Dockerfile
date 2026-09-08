# Стадия сборки (build stage)
FROM node:20-alpine AS build

WORKDIR /app

# Копируем package файлы и устанавливаем зависимости
COPY package*.json ./
RUN npm ci

# Копируем исходный код и собираем проект
COPY . .
RUN npm run build

# Финальная стадия на nginx (production stage)
FROM nginx:1.25-alpine

# Копируем кастомную конфигурацию nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копируем собранный фронтенд в директорию nginx для раздачи статики
COPY --from=build /app/dist /usr/share/nginx/html

# Настройка безопасности (запуск не от root)
# Создаем временные директории для nginx и выдаем права пользователю nginx
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d

USER nginx

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1
