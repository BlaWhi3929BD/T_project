# Дашборд аналитики по сделкам

Это одностраничное приложение для визуализации и анализа торговых сделок. Включает в себя API на FastAPI, интерактивный дашборд на React и поддержку развёртывания через Docker Compose и Kubernetes.

## Структура

- `solution/backend/`: FastAPI API, работа с БД (PostgreSQL / SQLite), логика агрегации и тесты.
- `solution/frontend/`: React-приложение (TypeScript, Vite, Nginx).
- `docker-compose.yml`: Конфигурация Docker Compose для локального запуска.
- `task/`: Исходные данные (`trades.csv`) и скрипт генерации (`seed.py`).
- `solution/DECISIONS.md`: Журнал технических решений.

---

## 1. Локальный запуск (без Docker)

### Бэкенд

#### Настройка:
```bash
# 0. Клонировать репозиторий:
git clone -b feature/trades-dashboard --single-branch https://github.com/BlaWhi3929BD/T_project.git

cd T_project

# 1. Создать виртуальное окружение:
# Bash / Linux / macOS:
python3 -m venv .venv

# Windows (PowerShell):
# python -m venv .venv

# 2. Активация:
# Bash:
source .venv/bin/activate

# Fish:
# source .venv/bin/activate.fish

# Windows (PowerShell):
# .venv\Scripts\Activate.ps1

# Windows (CMD):
# .venv\Scripts\activate.bat

# 3. Установить зависимости:
pip install -r requirements.txt

# 4. Сгенерировать CSV и загрузить данные в SQLite:
python task/data/seed.py

# Bash / Linux / macOS:
PYTHONPATH=solution/backend python -m app.seed --if-empty

# Fish:
# env PYTHONPATH=solution/backend python -m app.seed --if-empty

# Windows PowerShell:
# $env:PYTHONPATH = "solution/backend"
# python -m app.seed --if-empty
```

#### Запуск:
```bash
# Bash:
PYTHONPATH=solution/backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

# Fish:
# env PYTHONPATH=solution/backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

# Windows PowerShell:
# $env:PYTHONPATH = "solution/backend"
# python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Windows CMD:
# set PYTHONPATH=solution/backend
# python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
API доступно по адресу `http://localhost:8000`. Документация Swagger — `http://localhost:8000/docs`.

### Фронтенд

#### Запуск:
```bash
cd solution/frontend

# Установить зависимости:
npm install

# Запустить сервер разработки:
npm run dev
```
Фронтенд будет доступен по адресу `http://localhost:3000` (с проксированием `/api` на бэкенд).

---

## 2. Развёртывание через Docker Compose (Рекомендуется)

### Предварительные требования и установка Docker

Для развёртывания проекта необходимы **Docker** и **Docker Compose (v2+)**.

<details>
<summary><b>Гайд по установке Docker и Docker Compose</b></summary>

#### Debian-based (Ubuntu / Debian / Linux Mint)
```bash
# 1. Установка пакетов Docker и плагина Docker Compose:
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2

# 2. Запуск службы и добавление текущего пользователя в группу docker:
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
```

#### Fedora-based (Fedora / RHEL / CentOS)
```bash
# 1. Установка Docker Engine и Compose плагина:
sudo dnf install -y docker docker-compose-plugin

# 2. Запуск службы и добавление пользователя в группу docker:
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
```

#### Arch-based (Arch Linux / Manjaro / EndeavourOS)
```bash
# 1. Установка пакетов из официальных репозиториев:
sudo pacman -S --noconfirm docker docker-compose

# 2. Запуск службы и добавление пользователя в группу docker:
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
```

#### Windows
1. Скачайте и установите [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/).
2. В процессе установки убедитесь, что выбрана опция **Use WSL 2 instead of Hyper-V** (рекомендуется).
3. Перезагрузите компьютер и запустите Docker Desktop.

#### Проверка установки:
```bash
docker --version
docker compose version
```
</details>

### Первый запуск (с нуля)
1. Скопируйте файл с переменными окружения:
   ```bash
   cp .env.example .env
   ```
   *(При необходимости отредактируйте параметры БД в `.env`)*

2. Запустите сборку и развёртывание одной командой:
   ```bash
   docker compose up --build -d
   ```
   *Что происходит при первом запуске:* поднимается PostgreSQL 16, backend генерирует `trades.csv` внутри контейнера и выполняет идемпотентную загрузку до старта Uvicorn. После успешного seed запускаются API и frontend.

   Пароль PostgreSQL не хранится в `docker-compose.yml`. Перед запуском замените
   `change-me` в `.env` на собственное значение. Compose завершится с ошибкой,
   если обязательные переменные не заданы.

### Проверка работоспособности
- **Дашборд:** открыть в браузере `http://localhost:8080` (графики и таблица должны быть заполнены данными).
- **Метрики API:** `curl http://localhost:8080/api/stats` (отдаёт JSON).
- **Эндпоинты здоровья:**
  - `curl http://localhost:8080/health` → `200 {"status":"ok"}`
  - `curl http://localhost:8080/ready` → `200 {"status":"ready"}`
- **Безопасность портов:** `curl http://localhost:8000` с хоста **не отвечает** (порт бэкенда изолирован внутри сети Docker).
- **Статус контейнеров:** `docker compose ps` — все три сервиса (`trades-postgres`, `trades-backend`, `trades-frontend`) должны быть в состоянии `healthy`.

### Повторный запуск (без пересоздания и без повторного сидинга)
Если вы остановили контейнеры через `docker compose down`:
```bash
docker compose up -d
```
*Данные в PostgreSQL сохраняются в именованном томе (`postgres_data`). Повторная загрузка CSV не производится, время старта минимально.*

### Запуск тестов в контейнере
Для запуска всех тестов `pytest` внутри тестового образа бэкенда:
```bash
docker compose --profile test run --rm backend-test
```
Тестовый сервис находится в профиле `test` и не запускается при обычном
`docker compose up`.

### Полный сброс (удаление данных и контейнеров)

Для полного уничтожения окружения вместе с базой данных и томами:

```bash
docker compose down -v
```

---
## Тестирование локально (без Docker)

Для запуска автотестов на бэкенде:

```bash
.venv/bin/pytest solution/backend/tests/

```

---

## 3. Развёртывание в Kubernetes (minikube + kustomize)

### Предварительные требования и подготовка кластера
Необходимы запущенные **minikube** (или **kind**) и утилита **kubectl**.

<details>
<summary><b>Гайд по установке Kubernetes (minikube и kubectl)</b></summary>

#### Debian-based (Ubuntu / Debian / Linux Mint)
```bash
# 1. Установка kubectl (официальный бинарник):
sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates curl
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
sudo chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo chmod 644 /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update && sudo apt-get install -y kubectl

# 2. Установка minikube:
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64
```

#### Fedora-based (Fedora / RHEL / CentOS)
```bash
# 1. Установка kubectl:
cat <<EOF | sudo tee /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://pkgs.k8s.io/core:/stable:/v1.31/rpm/
enabled=1
gpgcheck=1
gpgkey=https://pkgs.k8s.io/core:/stable:/v1.31/rpm/repodata/repomd.xml.key
EOF
sudo dnf install -y kubectl

# 2. Установка minikube:
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64
```

#### Arch-based (Arch Linux / Manjaro)
```bash
# 1. Установка kubectl и minikube:
sudo pacman -S --noconfirm kubectl minikube
```

#### Windows
1. **Через winget (рекомендуется):**
   ```powershell
   winget install -e --id Kubernetes.kubectl
   winget install -e --id Kubernetes.minikube
   ```
2. **Либо вручную:**
   - Скачайте и запустите [установщик minikube для Windows](https://storage.googleapis.com/minikube/releases/latest/minikube-installer.exe).
   - Скачайте [kubectl.exe](https://dl.k8s.io/release/v1.31.0/bin/windows/amd64/kubectl.exe) и добавьте путь к файлу в системную переменную `PATH`.

#### Проверка установки:
```bash
kubectl version --client
minikube version
```
</details>

<details>
<summary><b>Инструкция по настройке кластера и Ingress в minikube</b></summary>

#### 1. Запуск minikube с докер-драйвером:
```bash
minikube start --driver=docker
```

#### 2. Включение Ingress-контроллера (NGINX Ingress):
```bash
minikube addons enable ingress
```

#### 3. Настройка локального DNS для резолва `trades.local`:
Добавьте IP-адрес вашего кластера в `/etc/hosts` (для Linux/macOS) или `C:\Windows\System32\drivers\etc\hosts` (для Windows):
```text
<IP-АДРЕС-КЛАСТЕРА> trades.local
```
*Узнать IP-адрес кластера можно командой `minikube ip`.*

*(На macOS и Windows с docker-драйвером Ingress недоступен по прямому IP. Используйте туннель в отдельном терминале):*
```bash
minikube tunnel
# И добавьте в hosts:
# 127.0.0.1 trades.local
```
</details>

### Деплой приложения
1. Для Kubernetes создайте Secret командой до применения Kustomize:
   ```bash
   kubectl create namespace trades-dashboard --dry-run=client -o yaml | kubectl apply -f -
   kubectl -n trades-dashboard create secret generic postgres-secret \
     --from-literal=POSTGRES_DB=trades_db \
     --from-literal=POSTGRES_USER=trades_user \
     --from-literal=POSTGRES_PASSWORD='replace-me' \
     --from-literal=DATABASE_URL='postgresql://trades_user:replace-me@postgres:5432/trades_db' \
     --dry-run=client -o yaml | kubectl apply -f -
   ```
   Файл `k8s/postgres-secret.yaml` не подключён в Kustomize и оставлен только
   как справочный шаблон; production-секреты создаются отдельной командой.

2. Сделайте образы бэкенда и фронтенда доступными для кластера:
   ```bash
   # Для minikube (загрузка локально собранных образов):
   TAG=$(git rev-parse --short HEAD)
   docker build -t trades-backend:$TAG -f solution/backend/Dockerfile .
   docker build -t trades-frontend:$TAG -f solution/frontend/Dockerfile solution/frontend
   minikube image load trades-backend:$TAG
   minikube image load trades-frontend:$TAG
   ```
   В PowerShell сначала задайте тег так:
   ```powershell
   $env:TAG = (git rev-parse --short HEAD)
   docker build -t "trades-backend:$env:TAG" -f solution/backend/Dockerfile .
   docker build -t "trades-frontend:$env:TAG" -f solution/frontend/Dockerfile solution/frontend
   minikube image load "trades-backend:$env:TAG"
   minikube image load "trades-frontend:$env:TAG"
   ```
3. Укажите этот тег в local overlay перед развёртыванием:
   ```bash
   sed -i -E "s/(newTag: ).*/\1$TAG/" k8s/overlays/local/kustomization.yaml
   ```
   Команда безопасна при повторном запуске: она заменяет текущее значение
   `newTag`, независимо от того, было ли там `latest` или предыдущий SHA. Для
   fish используйте тот же вызов после `set TAG (git rev-parse --short HEAD)`.
   В PowerShell используйте:
   ```powershell
   (Get-Content k8s/overlays/local/kustomization.yaml) -replace '(newTag: ).*', ('$1' + $env:TAG) |
     Set-Content k8s/overlays/local/kustomization.yaml
   ```
4. Разверните ресурсы через **Kustomize**:
   ```bash
   kubectl apply -k k8s/
   ```
   *Что происходит:* создаются namespace, PostgreSQL (`StatefulSet` + PVC),
   backend и frontend. Backend ждёт готовности PostgreSQL, генерирует CSV и
   выполняет seed до запуска Uvicorn. Отдельного Job для загрузки данных нет.
   На backend настроен `startupProbe` с окном до 10 минут: во время первой
   генерации и загрузки данных Kubernetes не запускает liveness-проверку и не
   перезапускает pod преждевременно. После запуска Uvicorn `/health` проходит
   startup/liveness, а `/ready` подтверждает доступность PostgreSQL.

Для production-режима используйте overlay с двумя репликами backend и
`PodDisruptionBudget`:
```bash
kubectl apply -k k8s/overlays/production/
```
Перед применением production overlay замените `newTag` в
`k8s/overlays/production/kustomization.yaml` на tag собранных образов:
```bash
sed -i -E "s/(newTag: ).*/\1$TAG/" k8s/overlays/production/kustomization.yaml
```
Local overlay остаётся вариантом по умолчанию для minikube и одной реплики.

### Проверка работоспособности в кластере
```bash
# Получить список всех ресурсов в пространстве имен
kubectl get all -n trades-dashboard

# Ожидаемый результат:
# - Все поды в состоянии Running
# - backend и frontend имеют Ready-поды
# - PostgreSQL имеет Ready-под
```
После этого дождитесь готовности всех Pod:
```bash
kubectl wait --for=condition=ready pod --all -n trades-dashboard --timeout=15m
```
Десятиминутное окно startup probe входит в общий таймаут ожидания. Если pod не
становится готовым за 15 минут, проверьте `kubectl describe pod` и логи backend:
это обычно означает недоступный PostgreSQL, ошибку Secret или неудачный seed.
Дашборд будет доступен по адресу `http://trades.local` (с использованием
`minikube tunnel` или напрямую по IP).

### Обновление конфигурации
Вы можете безопасно обновлять манифесты и делать повторный `apply`:
```bash
kubectl apply -k k8s/
```
*Загруженное количество сделок в БД не изменится, повторный отдельный Job не
запускается.*

При повторном запуске entrypoint сравнивает количество строк в таблице с
количеством строк в CSV. Полный датасет пропускается. Если загрузка была
прервана до commit, транзакция откатывается, и следующий запуск выполняет её
заново. Поэтому перезапуск Pod безопасен и не оставляет частично загруженную
таблицу.

### Обновление образов
Для выкладки новой версии соберите образы с новым тегом, снова загрузите их
в minikube и замените старые значения `image` в манифестах. Новый тег меняет
Pod template, поэтому Deployment создаёт новые Pod. Не используйте `latest`
вместе с `IfNotPresent`: Kubernetes может оставить старый локальный образ.

### Масштабирование бэкенда
Вы можете масштабировать бэкенд на несколько реплик:
```bash
kubectl scale deployment/backend --replicas=2 -n trades-dashboard
```
> **Почему это работает на PostgreSQL и не работало бы на SQLite?**
> PostgreSQL является полноценной клиент-серверной СУБД, поддерживающей конкурентные транзакции и сетевой доступ. Несколько реплик бэкенда могут одновременно и безопасно общаться с одной базой данных. В случае с SQLite, файл базы данных блокировался бы на запись (`database is locked`), а совместный доступ подов к одному файлу через сетевые тома (типа NFS) привел бы к повреждению данных из-за отсутствия координации блокировок на уровне ОС.

### Удаление всех ресурсов
```bash
kubectl delete -k k8s/
```

---

## 4. Производительность и бенчмарки

Контрольная проверка выполняется на полном датасете (100 000 записей) без
фильтров. Статистика агрегируется SQL-запросами в базе данных, а не загружает
весь датасет в pandas на каждый запрос. Для повторяемого замера используйте
`ab` с параметрами ниже на конкретном окружении:

| Эндпоинт | Требование SLA (одиночные запросы) | Одиночный запрос | Нагрузка `-n 100 -c 5` |
|---|---:|---:|---:|
| `GET /api/stats` | < 200 мс | **166.9 мс** | p95 **301 мс**, max 330 мс |
| `GET /api/trades` | < 100 мс | Не измерялся отдельно | p95 **70 мс**, max 82 мс |

> **Примечание по производительности `/api/stats`:**
> Дневные суммы и базовые агрегаты вычисляются в SQL, а обработчик использует
> синхронный режим FastAPI для синхронного SQLAlchemy. В текущем локальном
> окружении одиночный запрос укладывается в SLA, но при пяти параллельных
> запросах p95 превышает 200 мс. Поэтому SLA для конкурентной нагрузки не
> считается выполненным; результат зависит от СУБД, индексов и ресурсов
> контейнера.

#### Команды для воспроизведения замера:
```bash
# Прогрев:
curl -s "http://127.0.0.1:8000/api/stats" > /dev/null

# Замер /api/stats:
ab -n 100 -c 5 http://127.0.0.1:8000/api/stats

# Замер /api/trades:
ab -n 100 -c 5 "http://127.0.0.1:8000/api/trades?page=1&page_size=50"

# Отдельный замер одиночного запроса:
ab -n 1 -c 1 http://127.0.0.1:8000/api/stats
```

---

## Дополнительная документация
Подробное обоснование всех принятых технических решений находится в файле `solution/DECISIONS.md`.
