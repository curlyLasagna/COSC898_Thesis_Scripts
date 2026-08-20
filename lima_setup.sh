#!/usr/bin/env sh

set -eux

CONFIG_PATH=${1}/.

# Clear any pre-existing config files
limactl shell nixos sudo rm -rf '/etc/nixos/*'
# Copy the nixos flake config generated from host machine
# Using /tmp/conf due to permission issues
limactl copy -r $CONFIG_PATH nixos:/tmp/conf
# Copy host-generated flake config then rebuild
limactl shell nixos sudo cp -r '/tmp/conf/.' /etc/nixos/
limactl shell nixos sudo nix
