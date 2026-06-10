#!/bin/bash
# User-data para el EC2 de Vigía (Amazon Linux 2023).
# Instala Docker + compose plugin, habilita el servicio y crea swap de 2GB
# (colchón para la ingesta del corpus completo en instancias de 2GB RAM).
set -euxo pipefail

# Docker
dnf install -y docker git
systemctl enable --now docker
usermod -aG docker ec2-user

# Docker compose plugin (binario oficial)
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Swap 2GB
if ! swapon --show | grep -q swapfile; then
  dd if=/dev/zero of=/swapfile bs=128M count=16
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
