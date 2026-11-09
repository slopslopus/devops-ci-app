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

## 10. Ansible

Расположение проекта: каталог `ansible/` в корне репозитория
(`site.yml`, `verify.yml`, `ansible.cfg`, `inventory/`, `group_vars/`, `roles/`).
Управляющий узел — хостовая macOS с Ansible и коллекциями
из `ansible/requirements.yml`
(`ansible.posix`, `community.docker`, `community.general`).
Управляемый узел — VM `devops-vm` (`192.168.64.2`): Ubuntu Server 24.04,
архитектура `aarch64` (стенд UTM на ARM64; методичка описывает x86_64 —
репозиторий Docker и проверки ОС используют `arm64`/`aarch64`).

Inventory:

- `ansible/inventory/bootstrap.ini` — первичный запуск от `student`
  по паролю (`--ask-pass --ask-become-pass`);
- `ansible/inventory/prod.ini` (выбран по умолчанию в `ansible.cfg`) —
  последующие запуски от `devops` по ключу `~/.ssh/devops_vm`, без пароля.

Учётные записи: bootstrap — `student` (пароль, sudo с паролем);
prod — `devops` (ключ из ПР-5, `NOPASSWD: ALL` в `/etc/sudoers.d/devops`,
член групп `sudo` и `docker`).

Роли и их ответственность:

- `base` — проверка платформы (Ubuntu 24.04, `aarch64`), базовые пакеты
  (включая `python3-requests` для модулей `community.docker`),
  официальный репозиторий Docker, служба Docker;
- `ssh` — пользователь `devops`, SSH-ключ, sudoers, hardening SSH
  (`PermitRootLogin no`, `PasswordAuthentication no`), UFW `22/tcp`, `80/tcp`;
- `nginx` — reverse proxy на `127.0.0.1:5000`, удаление default-сайта,
  `nginx -t` перед reload (handler);
- `app` — загрузка образа, контейнер `devops-ci-app`
  (`127.0.0.1:5000->5000`, `restart unless-stopped`), проверка `/health`
  с `until`.

Образ: эталон ПР-10 — `ghcr.io/slopslopus/devops-ci-app` по полному SHA
коммита (см. раздел «GHCR-образ» выше). Примечание о стенде: образ GHCR
собран только под `amd64` и не запускается на ARM64-стенде
(`exec format error`), поэтому в `ansible/group_vars/all.yml` для ПР-11
задан пересобранный из того же `Dockerfile` образ из registry хоста:
`192.168.64.1:5055/devops-ci-app:pr11-arm64`.
Порт контейнера: `5000` (публикация только на loopback узла).
Health endpoint: `/health` → `{"status":"ok"}` (напрямую и через Nginx).

Команды:

```bash
cd ansible
ansible-playbook -i inventory/bootstrap.ini site.yml --ask-pass --ask-become-pass  # первичный запуск
ansible-playbook site.yml          # повторный запуск (идемпотентность: changed=0)
ansible-playbook verify.yml        # read-only аудит (ничего не меняет)
```

`verify.yml` использует тот же `prod.ini`, выполняет только проверки
(`assert`, `uri`, `command` с `changed_when: false`): ОС/`aarch64`, Docker,
пользователь `devops` (ключ, passwordless sudo), hardening SSH (`sshd -T`),
UFW `22`/`80`, конфиг и сервис Nginx, контейнер running с образом
из `app_image:app_tag`, `/health` напрямую и через Nginx.
В CI отдельный read-only плейбук удобен тем, что подтверждает состояние
без риска изменить его; `command: sshd -T` снабжён `changed_when: false`,
чтобы чтение эффективной конфигурации не засчитывалось как изменение
и повторные прогоны давали `changed=0`.
