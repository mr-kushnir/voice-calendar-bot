# Развертывание на Yandex Cloud

Полное руководство по развертыванию Voice Calendar Telegram Bot на Yandex Cloud.

## 📋 Предварительные требования

### 1. Установите Yandex Cloud CLI

**Linux/macOS:**
```bash
curl https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
```

**Windows (PowerShell):**
```powershell
iex (New-Object System.Net.WebClient).DownloadString('https://storage.yandexcloud.net/yandexcloud-yc/install.ps1')
```

### 2. Инициализируйте CLI

```bash
yc init
```

Следуйте инструкциям для:
- Авторизации
- Выбора облака
- Выбора каталога (folder)
- Настройки зоны доступности

### 3. Установите Docker

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

**macOS:**
```bash
brew install --cask docker
```

**Windows:**
Скачайте и установите Docker Desktop: https://www.docker.com/products/docker-desktop

### 4. Создайте SSH ключ (если нет)

```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

## 🌐 Настройка Yandex Cloud

### 1. Создайте сеть и подсеть

```bash
# Создать сеть
yc vpc network create \
  --name bot-network \
  --description "Network for Voice Calendar Bot"

# Создать подсеть
yc vpc subnet create \
  --name bot-subnet \
  --network-name bot-network \
  --zone ru-central1-a \
  --range 10.128.0.0/24
```

### 2. Получите ID подсети

```bash
yc vpc subnet list
```

Скопируйте `ID` созданной подсети.

### 3. Получите ID каталога

```bash
yc config list
```

Скопируйте `folder-id`.

## ⚙️ Настройка переменных окружения

### 1. Создайте `.env` файл в корне проекта

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# OpenAI (for STT and NLP)
OPENAI_API_KEY=your_openai_api_key

# ElevenLabs (for TTS)
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Yandex Calendar (CalDAV)
YANDEX_CALENDAR_LOGIN=your_yandex_login
YANDEX_CALENDAR_PASSWORD=your_yandex_password
YANDEX_CALENDAR_URL=https://caldav.yandex.ru

# Google Calendar (ICS)
GOOGLE_CALENDAR_ICS_URL=your_google_calendar_ics_url

# Yandex Tracker (optional, for Test Agent)
YANDEX_TRACKER_TOKEN=your_tracker_token
YANDEX_TRACKER_ORG_ID=your_org_id
YANDEX_TRACKER_QUEUE=EXTEST

# Logging
LOG_LEVEL=INFO
```

### 2. Установите переменные для развертывания

**Linux/macOS:**
```bash
export YC_FOLDER_ID="your_folder_id"
export YC_SUBNET_ID="your_subnet_id"
```

**Windows (PowerShell):**
```powershell
$env:YC_FOLDER_ID="your_folder_id"
$env:YC_SUBNET_ID="your_subnet_id"
```

## 🚀 Развертывание

### Вариант 1: Автоматическое развертывание (Python)

```bash
python scripts/deploy_yandex_cloud.py
```

### Вариант 2: Автоматическое развертывание (Bash)

```bash
chmod +x scripts/deploy_yandex_cloud.sh
./scripts/deploy_yandex_cloud.sh
```

### Вариант 3: Ручное развертывание

#### Шаг 1: Собрать Docker образ

```bash
docker build -t voice-calendar-bot:latest .
```

#### Шаг 2: Экспортировать образ

```bash
docker save voice-calendar-bot:latest -o voice-calendar-bot.tar
gzip voice-calendar-bot.tar
```

#### Шаг 3: Создать VM

```bash
yc compute instance create \
  --name voice-calendar-bot \
  --folder-id $YC_FOLDER_ID \
  --zone ru-central1-a \
  --platform standard-v3 \
  --cores 2 \
  --memory 2GB \
  --create-boot-disk size=20GB,image-family=ubuntu-2204-lts \
  --network-interface subnet-id=$YC_SUBNET_ID,nat-ip-version=ipv4 \
  --ssh-key ~/.ssh/id_rsa.pub \
  --metadata-from-file user-data=cloud-init.yaml
```

#### Шаг 4: Получить IP адрес VM

```bash
yc compute instance list
```

#### Шаг 5: Скопировать файлы на VM

```bash
VM_IP="your_vm_ip"

scp voice-calendar-bot.tar.gz ubuntu@$VM_IP:/tmp/
scp .env ubuntu@$VM_IP:/tmp/
scp docker-compose.yml ubuntu@$VM_IP:/tmp/
```

#### Шаг 6: Настроить приложение на VM

```bash
ssh ubuntu@$VM_IP

# На VM:
cd /tmp
gunzip voice-calendar-bot.tar.gz
sudo docker load -i voice-calendar-bot.tar

sudo mkdir -p /opt/voice-calendar-bot
sudo mv docker-compose.yml /opt/voice-calendar-bot/
sudo mv .env /opt/voice-calendar-bot/
cd /opt/voice-calendar-bot

# Запустить бота
sudo docker-compose up -d
```

## 🔍 Мониторинг и управление

### Просмотр логов

```bash
ssh ubuntu@$VM_IP 'cd /opt/voice-calendar-bot && sudo docker-compose logs -f'
```

### Просмотр статуса

```bash
ssh ubuntu@$VM_IP 'cd /opt/voice-calendar-bot && sudo docker-compose ps'
```

### Перезапуск бота

```bash
ssh ubuntu@$VM_IP 'cd /opt/voice-calendar-bot && sudo docker-compose restart'
```

### Остановка бота

```bash
ssh ubuntu@$VM_IP 'cd /opt/voice-calendar-bot && sudo docker-compose down'
```

### Обновление бота

```bash
# 1. Пересобрать образ локально
docker build -t voice-calendar-bot:latest .
docker save voice-calendar-bot:latest -o voice-calendar-bot.tar
gzip -f voice-calendar-bot.tar

# 2. Скопировать на VM
scp voice-calendar-bot.tar.gz ubuntu@$VM_IP:/tmp/

# 3. Обновить на VM
ssh ubuntu@$VM_IP << 'EOF'
cd /tmp
gunzip -f voice-calendar-bot.tar.gz
sudo docker load -i voice-calendar-bot.tar
cd /opt/voice-calendar-bot
sudo docker-compose down
sudo docker-compose up -d
EOF
```

## 🔧 Настройка systemd сервиса

На VM создается systemd сервис для автоматического запуска бота при перезагрузке:

```bash
# Проверить статус сервиса
sudo systemctl status voice-calendar-bot

# Остановить сервис
sudo systemctl stop voice-calendar-bot

# Запустить сервис
sudo systemctl start voice-calendar-bot

# Перезапустить сервис
sudo systemctl restart voice-calendar-bot

# Отключить автозапуск
sudo systemctl disable voice-calendar-bot

# Включить автозапуск
sudo systemctl enable voice-calendar-bot
```

## 📊 Мониторинг ресурсов

### На VM

```bash
ssh ubuntu@$VM_IP

# CPU и память
htop

# Использование диска
df -h

# Docker статистика
sudo docker stats
```

### Через Yandex Cloud Console

1. Откройте https://console.cloud.yandex.ru/
2. Перейдите в Compute Cloud → Виртуальные машины
3. Выберите `voice-calendar-bot`
4. Просмотрите метрики: CPU, память, сеть, диск

## 🛡️ Безопасность

### Firewall (группы безопасности)

```bash
# Создать группу безопасности
yc vpc security-group create \
  --name bot-sg \
  --network-name bot-network \
  --rule "direction=ingress,port=22,protocol=tcp,v4-cidrs=[0.0.0.0/0]" \
  --rule "direction=egress,protocol=any,v4-cidrs=[0.0.0.0/0]"

# Применить к VM
yc compute instance update voice-calendar-bot \
  --security-group-ids <security-group-id>
```

### Обновление системы на VM

```bash
ssh ubuntu@$VM_IP

sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get autoremove -y
```

## 💰 Стоимость

Примерная стоимость работы бота на Yandex Cloud:

- **VM (2 vCPU, 2 GB RAM):** ~800-1000 ₽/месяц
- **Диск (20 GB HDD):** ~80-100 ₽/месяц
- **Исходящий трафик:** ~5-20 ₽/месяц (зависит от использования)

**Итого:** ~900-1200 ₽/месяц (~$10-13/месяц)

## 🐛 Troubleshooting

### Бот не запускается

```bash
# Проверить логи
ssh ubuntu@$VM_IP 'cd /opt/voice-calendar-bot && sudo docker-compose logs'

# Проверить .env файл
ssh ubuntu@$VM_IP 'cat /opt/voice-calendar-bot/.env'

# Проверить Docker контейнеры
ssh ubuntu@$VM_IP 'sudo docker ps -a'
```

### Ошибки сети

```bash
# Проверить подключение к интернету
ssh ubuntu@$VM_IP 'ping -c 4 8.8.8.8'

# Проверить DNS
ssh ubuntu@$VM_IP 'nslookup telegram.org'
```

### Нехватка памяти

```bash
# Увеличить память VM
yc compute instance update voice-calendar-bot \
  --memory 4GB
```

### Нехватка места на диске

```bash
# Увеличить размер диска
yc compute disk update <disk-id> --size 30GB

# На VM расширить файловую систему
ssh ubuntu@$VM_IP 'sudo resize2fs /dev/vda2'
```

## 📚 Дополнительные ресурсы

- [Документация Yandex Cloud](https://cloud.yandex.ru/docs/)
- [Yandex Cloud CLI](https://cloud.yandex.ru/docs/cli/)
- [Compute Cloud](https://cloud.yandex.ru/docs/compute/)
- [Docker документация](https://docs.docker.com/)

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи бота
2. Проверьте статус Docker контейнеров
3. Проверьте переменные окружения
4. Проверьте подключение к API сервисам (Telegram, OpenAI, ElevenLabs)

---

**Дата:** 2025-11-05
**Версия:** MVP2
**Статус:** Production Ready
