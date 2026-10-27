#!/bin/sh
# Первичная настройка сервера «Клетки» (Ubuntu 24.04, чистая система без панели).
# Ставит: обновления, файрвол, вход только по ключу, PocketBase (база и аккаунты) и Caddy (HTTPS).
# Запуск на сервере от root:  sh server-setup.sh api.example.ru
set -eu
DOMAIN="${1:?укажите домен API, например kurkinsavvyn.fvds.ru}"
PB_VERSION="${PB_VERSION:-0.30.0}"

echo "== обновления"
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get upgrade -yq
apt-get install -yq curl unzip ufw debian-keyring debian-archive-keyring apt-transport-https gnupg

echo "== файрвол: только SSH и веб"
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "== вход только по ключу"
mkdir -p /etc/ssh/sshd_config.d
printf 'PasswordAuthentication no\nPermitRootLogin prohibit-password\n' > /etc/ssh/sshd_config.d/10-kletka.conf
systemctl reload ssh || systemctl reload sshd

echo "== PocketBase $PB_VERSION"
id kletka >/dev/null 2>&1 || useradd --system --home /opt/kletka --shell /usr/sbin/nologin kletka
mkdir -p /opt/kletka
cd /opt/kletka
curl -fsSL -o pb.zip "https://github.com/pocketbase/pocketbase/releases/download/v${PB_VERSION}/pocketbase_${PB_VERSION}_linux_amd64.zip"
unzip -o -q pb.zip pocketbase && rm pb.zip
chown -R kletka:kletka /opt/kletka
cat > /etc/systemd/system/kletka.service <<UNIT
[Unit]
Description=Kletka API (PocketBase)
After=network.target

[Service]
User=kletka
WorkingDirectory=/opt/kletka
ExecStart=/opt/kletka/pocketbase serve --http=127.0.0.1:8090
Restart=always
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now kletka

echo "== Caddy (HTTPS-сертификат получит сам)"
if ! command -v caddy >/dev/null; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -q && apt-get install -yq caddy
fi
cat > /etc/caddy/Caddyfile <<CADDY
$DOMAIN {
	encode gzip
	reverse_proxy 127.0.0.1:8090
}
CADDY
systemctl reload caddy || systemctl restart caddy

echo "== готово: https://$DOMAIN/_/  — админка PocketBase"
