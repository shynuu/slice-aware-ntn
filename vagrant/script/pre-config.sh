#!/bin/bash

function log() {
    echo -e "[INFO] $1"
}

function logerr() {
    echo -e "[ERRO] $1"
}

DOCKER_COMPOSE_VERSION='1.29.0'
VAGRANT_UID='1000'

log "Start pre-config script."

log "Update ubuntu"
apt-get update

log "Update kernel version: 5.0.0-23-generic"
apt -y install git gcc cmake autoconf libtool pkg-config libmnl-dev libyaml-dev
# apt-get install -qq \
#     linux-image-5.0.0-23-generic \
#     linux-modules-5.0.0-23-generic \
#     linux-headers-5.0.0-23-generic &&
#     grub-set-default 1 &&
#     update-grub

# log "Install Ubuntu Desktop"
# apt-get install -qq ubuntu-desktop

log "Install Virtualbox dkms"
apt-get install -qq virtualbox-guest-dkms

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
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - &>/dev/null
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update -qq
apt-get install -qq \
        docker-ce \
        docker-ce-cli \
        containerd.io
groupadd docker | true
usermod -aG docker $(id -nu $VAGRANT_UID)
setfacl -m user:$(id -nu $VAGRANT_UID):rw /var/run/docker.sock
systemctl enable docker

log "Verify docker install"
docker --version

log "Install docker-compose version: $DOCKER_COMPOSE_VERSION"
curl -sL "https://github.com/docker/compose/releases/download/$DOCKER_COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose &&
    chmod +x /usr/local/bin/docker-compose &&
    curl -L https://raw.githubusercontent.com/docker/compose/$DOCKER_COMPOSE_VERSION/contrib/completion/bash/docker-compose -o /etc/bash_completion.d/docker-compose

log "Verify docker-compose install"
docker-compose --version

log "Install pypi"
apt-get install -y python3-pip

log "End pre-config script."
