#!/bin/bash
# Kalpana OS ISO Builder Configuration
# Based on archiso

set -e

ISO_NAME="kalpana-os"
ISO_VERSION="0.1.0"
ISO_LABEL="KALPANA_$(date +%Y%m)"
ISO_PUBLISHER="Kalpana Project"
ISO_APPLICATION="Kalpana OS Live/Install ISO"

ARCH="x86_64"
WORK_DIR="./work"
OUT_DIR="./out"

# Packages to include in base ISO
PACKAGES=(
    # Base
    base
    linux
    linux-firmware
    grub
    efibootmgr
    
    # Core utilities
    vim
    nano
    git
    curl
    wget
    
    # Networking
    networkmanager
    openssh
    iproute2
    iptables-nft
    nftables
    
    # Python (for Kalpana)
    python
    python-pip
    python-asyncio
    
    # Security tools
    nmap
    tcpdump
    wireshark-cli
    
    # Wayland
    wayland
    weston
    
    # Development (optional, can be removed for minimal)
    base-devel
)

# Kalpana-specific files to include
KALPANA_FILES=(
    "/kalpana/core"
    "/kalpana/shell"
    "/kalpana/policy"
    "/kalpana/audit"
)

echo "Kalpana OS ISO Builder Configuration Loaded"
echo "  ISO: $ISO_NAME-$ISO_VERSION"
echo "  Arch: $ARCH"
echo "  Packages: ${#PACKAGES[@]}"
