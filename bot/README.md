# 🤖 Telegram Bot for "Follow My Reading" project — Dockerized

---

## 🚀 Quick start

### 🔧 Requirements
- Installed Docker ([instruction](https://docs.docker.com/engine/install/))

---

### 📦 Installation

1. **Clone repo or copy files**
   ```bash
   git clone https://github.com/gghost1/follow_my_reading.git
   cd bot
   ```
2. **Enter your bot token**
   ```python
   # /data.py
   TOKEN = '<< telegram bot token >>'
   ```

3. **build Docker-image:**
   ```bash
   docker build -t bot .
   ```

4. **Run container:**
   ```bash
   docker run -d --name bot tg-bot
   ```

---

## ⚙️ Managing

| Команда                        | Описание                     |
|-------------------------------|------------------------------|
| `docker ps`                   | Show current containers      |
| `docker stop tg-bot`          | Stop bot                     |
| `docker start tg-bot`         | Restart bot                  |
| `docker rm -f tg-bot`         | Delete container             |
| `docker logs -f tg-bot`       | Show logs                    |

---

## 🧹 Cleaning Docker

> ⚠️ Delete all images, containers and data.

```bash
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker rmi $(docker images -q)
docker volume rm $(docker volume ls -q)
docker system prune -a --volumes -f
```

---
