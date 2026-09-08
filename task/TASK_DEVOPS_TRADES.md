# Тестовое задание DevOps: упаковка и деплой дашборда сделок

Инструменты: Docker, Docker Compose, Kubernetes (`kind` или `minikube`),
Helm **или** kustomize на выбор.

Приложение — твой дашборд из ветки `feature/trades-dashboard`: FastAPI-бэкенд,
React-фронтенд на Vite, данные из `trades.csv`. Сейчас оно запускается только
руками из виртуального окружения. Задача — довести его до состояния, в котором
оно разворачивается одной командой локально и в Kubernetes.

Задание из трёх частей. Часть 1 меняет код, части 2 и 3 его упаковывают.

## Что уже известно про приложение

| Свойство | Сейчас | Что с этим делать |
|---|---|---|
| Путь к БД | захардкожен `sqlite:///solution/backend/trades.db` в `database.py` | вынести в переменную окружения |
| Запуск API | `uvicorn --host 127.0.0.1` | в контейнере слушать `0.0.0.0` |
| Фронтенд → API | Vite dev-proxy `/api` → `localhost:8000`, работает только в `npm run dev` | в production нужен статический билд и реверс-прокси |
| Данные | `task/data/seed.py` генерирует CSV на 100 000 строк, `seed_db.py` грузит его в БД построчно, в PostgreSQL это занимает несколько минут, **предварительно удаляя все записи** | загрузка выполняется один раз при развёртывании; учесть время в таймаутах |
| Health-эндпоинт | нет, есть только `GET /` с JSON | добавить |
| Тесты | 17 тестов `pytest`, запускаются локально | должны проходить внутри контейнера |
| Секреты | нет | появятся вместе с PostgreSQL |

## Часть 1. Подготовка кода

Разрешены только перечисленные изменения. Логику API, фронтенда и формат
ответов не трогать, все 17 тестов должны проходить.

1. `DATABASE_URL` читается из переменной окружения. Если не задана, поведение
   как сейчас (SQLite в `solution/backend/trades.db`).
2. Приложение работает с PostgreSQL через тот же `DATABASE_URL`. Модели уже на
   SQLAlchemy, но проверь типы `Numeric` и `DateTime` с таймзоной: результаты
   `/api/stats` на PostgreSQL должны совпадать с SQLite до копейки.
3. Два эндпоинта:
   - `GET /health` → `200 {"status":"ok"}`, к БД не обращается
   - `GET /ready` → `200`, если `SELECT 1` к БД проходит, иначе `503`
4. В `solution/DECISIONS.md` новая запись: почему для развёртывания выбрана
   PostgreSQL, хотя раньше был выбран SQLite. В том же формате, что и
   существующие записи.
5. Если `npm run build` фронтенда не проходит (сейчас `tsc` падает на
   неиспользуемой переменной), исправить минимальным изменением. Логику не
   трогать.

## Часть 2. Docker Compose

### Требования

1. `Dockerfile` бэкенда: multi-stage, процесс не от root, без исходников
   фронтенда в итоговом образе.
2. `Dockerfile` фронтенда: сборка `npm run build` в одной стадии, итоговая
   стадия на nginx раздаёт `dist/` и проксирует `/api` на бэкенд. Наружу
   торчит только фронтенд.
3. `docker-compose.yml`: `frontend`, `backend`, `postgres` (16+). Запуск одной
   командой. Дашборд открывается на `http://localhost:8080`, порт бэкенда на
   хост не публикуется.
4. Бэкенд стартует после готовности PostgreSQL. Способ выбирается кандидатом.
5. Генерация CSV и загрузка в БД выполняются **отдельно от основного процесса
   бэкенда**, один раз при первом развёртывании. При повторном `up` данные не
   стираются. Способ обосновать в README.
6. Данные PostgreSQL в named volume, переживают `down` и `up`.
7. Пароль PostgreSQL не лежит в git. В репозитории `.env.example` с
   плейсхолдерами.
8. `HEALTHCHECK` у всех трёх сервисов.
9. Тесты запускаются одной командой в контейнере: отдельная стадия сборки
   (`docker build --target test`) или сервис compose. Команда в README.
10. `README.md` переписан: первый запуск, повторный запуск, проверка, тесты,
    полный сброс.

### Приёмка

1. Развёртывание с нуля по README без ручных правок.
2. `http://localhost:8080` открывает дашборд, метрики и таблица заполнены
   данными. `curl localhost:8080/api/stats` отдаёт JSON.
3. `curl localhost:8000` с хоста не отвечает.
4. `docker compose ps` — три сервиса `healthy`.
5. `docker compose down` затем `up` — данные на месте, повторной загрузки CSV
   не было (по логам и по времени старта).
6. `docker compose exec backend id` — не root.
7. Команда тестов из README — 17 passed.
8. `git grep -i password` не находит реальных значений. `docker history`
   образов не содержит секретов.
9. Размер образов: фронтенд не больше 60 МБ, бэкенд не больше 500 МБ
   (`pandas` используется в расчёте статистики и нужен в runtime).

### Плюсом будет

- образ бэкенда меньше 400 МБ без потери функциональности
- `trivy` или `docker scout` без HIGH и CRITICAL, вывод в README
- `hadolint` без предупреждений
- образы тегируются по `git rev-parse --short HEAD`, не `latest`

## Часть 3. Kubernetes

Локальный кластер `kind` или `minikube`. Создание кластера и установка
ingress-контроллера в README.

### Требования

1. Отдельный `namespace`, единые labels `app.kubernetes.io/name` и
   `app.kubernetes.io/component` у всех ресурсов.
2. PostgreSQL: `StatefulSet` на одну реплику, `volumeClaimTemplates`,
   headless `Service`, пароль в `Secret`, обе пробы, `requests` и `limits`.
3. Бэкенд: `Deployment` на одну реплику, `ConfigMap` для несекретного,
   `Secret` для `DATABASE_URL`, `readinessProbe` на `/ready`, `livenessProbe`
   на `/health`, `requests` и `limits`, `securityContext` (`runAsNonRoot`,
   `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false`, capabilities
   сброшены).
4. Фронтенд: `Deployment`, пробы, ресурсы, `securityContext` с `runAsNonRoot`
   и `allowPrivilegeEscalation: false`.
5. Загрузка данных: `Job`, выполняется **только при первой установке**, не при
   каждом `upgrade`. Учти, что `seed_db.py` удаляет все записи, а `spec` у Job
   неизменяемый: повторный `apply` с другим образом упадёт. Как это решено и
   что произойдёт при повторном запуске Job, написать в README.
6. `Ingress`, host `trades.local`: `/api`, `/health` и `/ready` на бэкенд,
   всё остальное на фронтенд.
   На Windows и macOS с minikube на docker-драйвере адрес `minikube ip`
   снаружи недоступен, используй `minikube tunnel` или `kubectl port-forward`
   на сервис ingress-контроллера. Указать в README.
7. Упаковка: Helm chart с `values.yaml` **или** kustomize. Установка одной
   командой.
8. `README.md`: кластер, установка, проверка, обновление, удаление.

### Приёмка

1. Развёртывание по README.
2. Все поды `Running` и `READY`, Job `Completed`.
3. `curl -H "Host: trades.local" http://<ingress>/health` → `200`,
   `/ready` → `200`, `/` → HTML дашборда, `/api/stats` → JSON.
4. `kubectl delete pod <под бэкенда>` — под пересоздаётся сам, через минуту
   `/api/stats` снова отвечает.
5. `kubectl delete pod <под PostgreSQL>` — под пересоздаётся, `/api/stats`
   отдаёт те же значения, что до удаления.
6. `helm upgrade` или `kubectl apply -k` поверх работающего — без ошибок,
   количество сделок в БД не изменилось (проверяется `/api/trades`, поле
   `total`).
7. `kubectl scale deployment/<backend> --replicas=2` — `2/2` Ready,
   `/api/stats` отвечает. В README один абзац: почему это работает на
   PostgreSQL и не работало бы на SQLite.
8. В поде бэкенда: `id` не root, `touch /test` завершается ошибкой.
   В поде фронтенда: `id` не root.
9. Реальные пароли отсутствуют в git, передаются при установке (`--set`,
   не коммитимый values-файл или `kubectl create secret` по README).

### Плюсом будет

- две реплики бэкенда и обновление без простоя: `PodDisruptionBudget`,
  `maxUnavailable: 0`, проверка циклом `curl` во время
  `kubectl rollout restart`
- `readOnlyRootFilesystem` для nginx во фронтенде
- kustomize overlays или Helm values для `dev` (1 реплика) и `prod`
  (2 реплики, другие лимиты)
- `HorizontalPodAutoscaler` для бэкенда с работающим `metrics-server`
- `NetworkPolicy`: к PostgreSQL ходит только бэкенд, к бэкенду только фронтенд
  и ingress-контроллер. Указать, какой CNI поставлен и зачем

## Вне рамок задания

TLS, облачные провайдеры, CI/CD, Prometheus и Grafana, резервное копирование
БД, репликация PostgreSQL, изменение логики API и фронтенда.

## Сдача

Та же ветка или новая от неё, история из осмысленных коммитов. Изменения
кода части 1 отдельными коммитами от инфраструктуры. Структура:

```
solution/backend/Dockerfile
solution/frontend/Dockerfile
docker-compose.yml
.env.example
k8s/  или  chart/
README.md
solution/DECISIONS.md
```

`trades.csv` и `trades.db` в git не попадают.