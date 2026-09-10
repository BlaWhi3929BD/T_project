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

# 4. Загрузить данные из CSV в SQLite:
python solution/backend/scripts/seed_db.py
```

#### Запуск:
```bash
# Bash:
PYTHONPATH=solution/backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

# Fish:
# env PYTHONPATH=solution/backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

# Windows (PowerShell / CMD):
# set PYTHONPATH=solution/backend
# venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
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
   *Что происходит при первом запуске:* поднимается PostgreSQL 16, сервис `db-seed` один раз импортирует 100 000 строк из `trades.csv` в БД, после чего стартуют бэкенд и фронтенд.

### Проверка работоспособности
- **Дашборд:** открыть в браузере `http://localhost:8080` (графики и таблица должны быть заполнены данными).
- **Метрики API:** `curl http://localhost:8080/api/stats` (отдаёт JSON).
- **Эндпоинты здоровья:**
  - `curl http://localhost:8080/health` → `200 {"status":"ok"}`
  - `curl http://localhost:8080/ready` → `200 {"status":"ready"}`
- **Безопасность портов:** `curl http://localhost:8000` с хоста **не отвечает** (порт бэкенда изолирован внутри сети Docker).
- **Статус контейнеров:** `docker compose ps` — все три сервиса (`trades-postgres`, `trades-backend`, `trades-frontend`) должны быть в состоянии `healthy` (trades-frontend иногда может быть unhealthy).

### Повторный запуск (без пересоздания и без повторного сидинга)
Если вы остановили контейнеры через `docker compose down`:
```bash
docker compose up -d
```
*Данные в PostgreSQL сохраняются в именованном томе (`postgres_data`). Повторная загрузка CSV не производится, время старта минимально.*

### Запуск тестов в контейнере
Для запуска всех тестов `pytest` внутри изолированного контейнера бэкенда:
```bash
docker build --target test -t trades-backend-test -f solution/backend/Dockerfile solution/backend
docker run --rm -v $(pwd)/task/data:/app/task/data trades-backend-test
```
*(Либо через Docker Compose):*

```bash
docker compose run --rm backend-test
```

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
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | sudo tee /etc/apt/sources.list.dir/kubernetes.list
sudo chmod 644 /etc/apt/sources.list.dir/kubernetes.list
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

### Деплой приложения одной командой
1. Сделайте образы бэкенда и фронтенда доступными для кластера:
   ```bash
   # Для minikube (загрузка локально собранных образов):
   docker build -t trades-backend:latest -f solution/backend/Dockerfile .
   docker build -t trades-frontend:latest -f solution/frontend/Dockerfile solution/frontend
   minikube image load trades-backend:latest
   minikube image load trades-frontend:latest
   ```
2. Разверните все ресурсы одной командой через **Kustomize**:
   ```bash
   kubectl apply -k k8s/
   ```
   *Что происходит:* Создается пространство имен `trades-dashboard`, поднимается PostgreSQL (`StatefulSet` + PV), запускается Job `db-seed` (импортирует данные ровно один раз), стартуют поды бэкенда и фронтенда, а Ingress маршрутизирует трафик.

### Проверка работоспособности в кластере
```bash
# Получить список всех ресурсов в пространстве имен
kubectl get all -n trades-dashboard

# Ожидаемый результат:
# - Все поды в состоянии Running
# - Job db-seed-xxxxx завершен со статусом Completed
```
После этого дашборд будет доступен по адресу: `http://trades.local` (с использованием `minikube tunnel` или напрямую по IP).

### Обновление конфигурации
Вы можете безопасно обновлять манифесты и делать повторный `apply`:
```bash
kubectl apply -k k8s/
```
*Загруженное количество сделок в БД не изменится, повторный сидинг Job производиться не будет.*

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

Замеры скорости производились на полном датасете (100 000 записей) без фильтров при помощи утилиты `ab` (Apache Benchmark) локально при уровне конкурентности `-c 5` (100 запросов):

| Эндпоинт | Требование SLA (одиночные запросы) | Фактический результат под нагрузкой (p95, c=5) |
|---|---|---|
| `GET /api/stats` | < 200 мс | **~11.0 сек** (высокая нагрузка из-за обработки Pandas + SQLite) |
| `GET /api/trades` | < 100 мс | **~82 мс** (полностью соответствует SLA) |

> **Примечание по производительности `/api/stats`:**
> Высокое время отклика под нагрузкой связано с тем, что расчет сложной метрики накопленной доходности (Equity Curve) для 100 000 записей выполняется «на лету» средствами библиотеки `pandas` на бэкенде в синхронном режиме (для точности группировки во временной зоне `Asia/Almaty`), что блокирует однопоточный цикл событий FastAPI при параллельных запросах. Одиночные запросы после прогрева укладываются в рамки лимитов.

#### Команды для воспроизведения замера:
```bash
# Прогрев:
curl -s "http://127.0.0.1:8000/api/stats" > /dev/null

# Замер /api/stats:
ab -n 100 -c 5 http://127.0.0.1:8000/api/stats

# Замер /api/trades:
ab -n 100 -c 5 "http://127.0.0.1:8000/api/trades?page=1&page_size=50"
```

---

## Дополнительная документация
Подробное обоснование всех принятых технических решений находится в файле `solution/DECISIONS.md`.
