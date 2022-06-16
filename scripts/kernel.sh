#!/bin/bash

function log() {
    echo -e "[INFO] $1"
}

function logerr() {
    echo -e "[ERRO] $1"
}

log "Update ubuntu"
apt-get update

log "Update kernel version"
apt-get install -qq \
    linux-image-5.0.0-23-generic \
    linux-modules-5.0.0-23-generic \
    linux-headers-5.0.0-23-generic &&
    grub-set-default 1 &&
    update-grub

reboot
