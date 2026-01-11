# Anti‑Spam Telegram Bot — Полное руководство по установке и запуску

> Этот документ написан так, чтобы даже человек без опыта в Linux смог запустить проект.

---

## 📦 Что делает бот

Бот для групп Telegram, который:

- фильтрует запрещённые слова,
- требует капчу для новых пользователей,
- ведёт логи нарушений,
- хранит настройки каждой группы в базе данных,
- работает на `Aiogram 3 + Async SQLAlchemy`,
- поддерживает запуск как systemd‑служба.

---

## 🖥 Требования сервера

Минимально:

- Linux (рекомендовано: Ubuntu/Debian/Mint)
- RAM: 256 MB+
- Python ≥ 3.10
- Интернет
- Доступ к Telegram API

---

## 1. 🐍 Установка Python

### Проверка версии

```bash
python3 --version
```

Если Python <3.10 — ставим:

#### Ubuntu / Mint / Debian:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip -y
```

Проверяем снова:

```bash
python3 --version
```

---

## 2. 📁 Установка проекта

### Клонируем репозиторий:

```bash
git clone https://github.com/<ваш_репозиторий>/Anti-Spam-Bot.git
cd Anti-Spam-Bot
```

---

## 3. 🔐 Создание `.env`

В проекте есть шаблон:

```
.env.template
```

Создаём реальный файл:

```bash
cp .env.template .env
```

Открываем для заполнения:

```bash
nano .env
```

Заполняем:

```env
BOT_TOKEN=ваш_токен_бота
DB_URL=sqlite+aiosqlite:///database.db
```

Сохранение в nano:
`CTRL + O → ENTER → CTRL + X`

---

## 4. 🧩 Создание виртуального окружения

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Проверяем:

```bash
which python
```

---

## 5. 📦 Установка зависимостей

```bash
pip install --upgrade pip wheel
pip install -r requirements.txt
```

---

## 6. 🏃 Запуск вручную (первый тест)

```bash
source .venv/bin/activate
python main.py
```

Если бот не упал — отлично.

---

## 7. 🗃 Автозапуск через systemd

### Создаём сервис:

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Вставляем:

```
[Unit]
Description=Telegram Anti-Spam Bot
After=network.target

[Service]
Type=simple
User=%i
WorkingDirectory=/home/%i/Anti-Spam-Bot
Environment="BOT_ENV=production"
ExecStart=/home/%i/Anti-Spam-Bot/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> `%i` заменяем на имя пользователя

### Применяем:

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

### Проверка статуса:

```bash
systemctl status telegram-bot
```

### Логи сервиса:

```bash
journalctl -u telegram-bot -f
```

---

## 8. 🗃 Обновление версии на сервере

```bash
cd Anti-Spam-Bot
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart telegram-bot
```

---

## 9. 🧹 Очистка логов

```bash
journalctl --vacuum-size=50M
```

---

## 🎯 Итог

После выполнения всех шагов бот:
✔ работает в фоне
✔ перезапускается при ошибках
✔ не требует ручного запуска
✔ переживает обновления системы
✔ стартует после ребута сервера
