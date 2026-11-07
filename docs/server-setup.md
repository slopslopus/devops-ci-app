# devops-ci-app: подготовка сервера к ПР-11 (Ansible-деплой)

## GHCR-образ

- Реестр: `ghcr.io/slopslopus/devops-ci-app`
- Тег для деплоя: полный SHA последнего зелёного коммита main:
  `ghcr.io/slopslopus/devops-ci-app:01995dd8491d11e44465bf1a3e5f83fd93e9a187`
- Тег `latest` только для ручной проверки, в деплое не использовать

## Требования к узлу

- ОС: Ubuntu 24.04 LTS
- Docker Engine + compose-плагин (`docker compose version` отвечает)
- Пользователь `deploy` в группе `docker` (без sudo на каждый вызов docker)
- Каталог приложения: `/opt/devops-ci-app` (владелец `deploy:deploy`)
- UFW: разрешены входящие `22/tcp`, `80/tcp`, `443/tcp`; остальное закрыто
- Доступность `ghcr.io` на чтение; видимость пакета: public
  (при приватном пакете — аутентификация чтения, см. ниже)
- Порт: публикация `5000` контейнера на loopback узла
- Health endpoint: `/health` отвечает `{"status":"ok"}`

## Подготовка узла (выполнить один раз)

```bash
# 1. Обновления и базовые пакеты
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg ufw

# 2. Docker Engine + compose-плагин (официальный репозиторий Docker)
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
docker --version
docker compose version

# 3. Пользователь deploy
sudo useradd -m -s /bin/bash deploy || true
sudo usermod -aG docker deploy

# 4. Каталог приложения
sudo mkdir -p /opt/devops-ci-app
sudo chown deploy:deploy /opt/devops-ci-app

# 5. UFW: SSH/HTTP/HTTPS, остальное закрыто
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status numbered
```

## GHCR login (только если пакет приватный)

```bash
# Токен: classic PAT с правом read:packages (вводить по запросу, в истории не хранить)
docker login ghcr.io --username <github-username>
```

Проверить чтение образа:

```bash
docker pull ghcr.io/slopslopus/devops-ci-app:01995dd8491d11e44465bf1a3e5f83fd93e9a187
```

## Почему не собирать на VM

Проверенный образ уже собран и протестирован CI. Сборка на каждой VM
повторяет работу, вносит риск расхождения окружений и лишает деплой
привязки к проверенной версии. Ansible должен загрузить образ по SHA
и запустить контейнер, а не собирать приложение заново.
