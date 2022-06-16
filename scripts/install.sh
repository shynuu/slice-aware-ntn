#!/bin/bash

function log() {
    echo -e "[INFO] $1"
}

function logerr() {
    echo -e "[ERRO] $1"
}

log "Update ubuntu"
apt-get update

log "Update dependencies"
apt -y install git gcc cmake autoconf libtool pkg-config libmnl-dev libyaml-dev

log "Install latest version of docker"
apt-get remove -qq \
    docker \
    docker-engine \
    docker.io \
    containerd \
    runc

apt-get install -qq \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common

mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

apt-get update -qq
apt-get install -qq \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-compose-plugin
    
groupadd docker | true
systemctl enable docker

log "Verify docker install"
docker --version

log "Verify docker-compose install"
docker-compose --version

log "Install pypi"
apt-get install -y python3-pip

log "Install gtp5g kernel module"
cd /tmp &&
    git clone https://github.com/free5gc/gtp5g &&
    cd gtp5g &&
    make clean &&
    make &&
    make install

log "gtp5g kernel module is located here:"
find /lib/modules/$(uname -r) -type f -name gtp5g*
