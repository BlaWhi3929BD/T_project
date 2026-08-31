solution/
├── backend/                # Бэкенд на FastAPI
│   ├── app/
│   │   ├── api/            # Эндпоинты
│   │   ├── core/           # Конфигурация и расчеты (PnL, MDD)
│   │   ├── db/             # Модели и подключение к БД
│   │   ├── schemas/        # Pydantic схемы (DTO)
│   │   └── main.py         # Точка входа
│   ├── tests/              # Автотесты
│   ├── scripts/            # Скрипты загрузки данных
│   └── requirements.txt
├── frontend/               # Фронтенд на Vite + React + TS
│   ├── src/
│   │   ├── api/            # Клиент для запросов
│   │   ├── components/     # UI компоненты (Фильтры, Таблица, График)
│   │   ├── hooks/          # Кастомные хуки для логики и URL
│   │   ├── types/          # TS интерфейсы
│   │   ├── utils/          # Форматирование денег и дат
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── tsconfig.json
├── DECISIONS.md            # Журнал решений
├── README.md               # Инструкция по запуску
└── docker-compose.yml      # Для быстрого поднятия БД
