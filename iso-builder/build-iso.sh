#!/bin/bash
# ============================================================================
# Kalpana OS - ISO Builder
# ============================================================================
# Creates a bootable Arch Linux-based ISO with Kalpana OS pre-installed.
# Requires: archiso package on Arch Linux
# ============================================================================

set -e

# Configuration
ISO_NAME="kalpana-os"
ISO_VERSION="0.1.0"
ISO_LABEL="KALPANA_OS"
WORK_DIR="/tmp/kalpana-iso-build"
OUT_DIR="$(pwd)/out"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE_DIR="${SCRIPT_DIR}/profile"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${CYAN}[KALPANA]${NC} $1"
}

success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
    fi
}

# Check dependencies
check_deps() {
    log "Checking dependencies..."
    
    local deps=(archiso mksquashfs xorriso)
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            error "Missing dependency: $dep"
        fi
    done
    
    success "All dependencies present"
}

# Create archiso profile
create_profile() {
    log "Creating Kalpana OS profile..."
    
    # Copy base profile
    if [[ -d /usr/share/archiso/configs/releng ]]; then
        cp -r /usr/share/archiso/configs/releng "${PROFILE_DIR}"
    else
        error "archiso base profile not found"
    fi
    
    # Customize profile
    customize_profile
    
    success "Profile created"
}

# Customize the archiso profile
customize_profile() {
    log "Customizing profile..."
    
    # Update profiledef.sh
    cat > "${PROFILE_DIR}/profiledef.sh" << 'EOF'
#!/usr/bin/env bash
# Kalpana OS Profile Definition

iso_name="kalpana-os"
iso_label="KALPANA_OS"
iso_publisher="Kalpana OS Project"
iso_application="Kalpana OS Live/Installer"
iso_version="0.1.0"
install_dir="kalpana"
buildmodes=('iso')
bootmodes=('bios.syslinux.mbr' 'bios.syslinux.eltorito' 
           'uefi-ia32.grub.eltorito' 'uefi-x64.grub.eltorito'
           'uefi-ia32.grub.esp' 'uefi-x64.grub.esp')
arch="x86_64"
pacman_conf="${profile}/pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '15' '-b' '1M')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/root"]="0:0:750"
  ["/root/.automated_script.sh"]="0:0:755"
  ["/etc/kalpana"]="0:0:755"
  ["/opt/kalpana"]="0:0:755"
)
EOF

    # Add Kalpana packages to package list
    cat >> "${PROFILE_DIR}/packages.x86_64" << 'EOF'

# === Kalpana OS Packages ===

# Core System
base
base-devel
linux
linux-firmware
linux-headers

# Boot
grub
efibootmgr

# Network
networkmanager
wireless_tools
wpa_supplicant
iwd

# Desktop (Wayland)
wayland
xorg-xwayland
weston
sway
foot
wofi
waybar
mako
grim
slurp
wl-clipboard

# GTK/GUI
gtk4
python-gobject
zenity

# Audio
pipewire
pipewire-pulse
pipewire-alsa
wireplumber

# Python (Kalpana)
python
python-pip
python-numpy
python-opencv
python-requests

# Utilities
git
vim
nano
htop
neofetch
wget
curl
unzip
brightnessctl
playerctl
espeak-ng
pulseaudio-utils

# Security
nftables
fail2ban
rkhunter

# Development
openssh
tmux
EOF

    success "Package list updated"
}

# Copy Kalpana OS files to airootfs
copy_kalpana_files() {
    log "Copying Kalpana OS files..."
    
    local airootfs="${PROFILE_DIR}/airootfs"
    
    # Create directories
    mkdir -p "${airootfs}/opt/kalpana"
    mkdir -p "${airootfs}/etc/kalpana"
    mkdir -p "${airootfs}/usr/lib/systemd/system"
    mkdir -p "${airootfs}/usr/local/bin"
    
    # Copy Kalpana components
    local kalpana_src="${SCRIPT_DIR}/.."
    
    cp -r "${kalpana_src}/kalpana-core" "${airootfs}/opt/kalpana/"
    cp -r "${kalpana_src}/kalpana-shell" "${airootfs}/opt/kalpana/"
    cp -r "${kalpana_src}/kalpana-security" "${airootfs}/opt/kalpana/"
    cp -r "${kalpana_src}/kalpana-ui" "${airootfs}/opt/kalpana/"
    cp -r "${kalpana_src}/kalpana-tools" "${airootfs}/opt/kalpana/"
    
    # Copy systemd units
    cp "${kalpana_src}/systemd-units/"*.service "${airootfs}/usr/lib/systemd/system/"
    
    # Create launcher scripts
    create_launcher_scripts "${airootfs}"
    
    # Create configuration files
    create_config_files "${airootfs}"
    
    success "Kalpana files copied"
}

# Create launcher scripts
create_launcher_scripts() {
    local airootfs="$1"
    
    # Kalpana Shell launcher
    cat > "${airootfs}/usr/local/bin/kalpana-shell" << 'EOF'
#!/bin/bash
exec python3 /opt/kalpana/kalpana-shell/src/shell.py "$@"
EOF
    chmod +x "${airootfs}/usr/local/bin/kalpana-shell"
    
    # Kalpana UI launcher
    cat > "${airootfs}/usr/local/bin/kalpana-ui" << 'EOF'
#!/bin/bash
exec python3 /opt/kalpana/kalpana-ui/src/webui.py "$@"
EOF
    chmod +x "${airootfs}/usr/local/bin/kalpana-ui"
    
    # Kalpana Core launcher
    cat > "${airootfs}/usr/local/bin/kalpana-core" << 'EOF'
#!/bin/bash
exec python3 /opt/kalpana/kalpana-core/src/main.py "$@"
EOF
    chmod +x "${airootfs}/usr/local/bin/kalpana-core"
}

# Create configuration files
create_config_files() {
    local airootfs="$1"
    
    # Hostname
    echo "kalpana" > "${airootfs}/etc/hostname"
    
    # Hosts file
    cat > "${airootfs}/etc/hosts" << 'EOF'
127.0.0.1   localhost
::1         localhost
127.0.1.1   kalpana.local kalpana
EOF

    # Kalpana motd
    cat > "${airootfs}/etc/motd" << 'EOF'

    ██╗  ██╗ █████╗ ██╗     ██████╗  █████╗ ███╗   ██╗ █████╗ 
    ██║ ██╔╝██╔══██╗██║     ██╔══██╗██╔══██╗████╗  ██║██╔══██╗
    █████╔╝ ███████║██║     ██████╔╝███████║██╔██╗ ██║███████║
    ██╔═██╗ ██╔══██║██║     ██╔═══╝ ██╔══██║██║╚██╗██║██╔══██║
    ██║  ██╗██║  ██║███████╗██║     ██║  ██║██║ ╚████║██║  ██║
    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
                                                    
    🧠 AI-Native Operating System
    
    Commands:
    • kalpana-shell  - Start Kalpana Shell
    • kalpana-ui     - Start Web UI (http://localhost:7777)
    • kalpana-core   - Start Core daemon
    
EOF

    # Auto-start Kalpana on login
    cat > "${airootfs}/etc/profile.d/kalpana.sh" << 'EOF'
# Kalpana OS environment
export KALPANA_HOME=/opt/kalpana
export PATH="$PATH:/opt/kalpana/bin"

# Show welcome
if [[ -f /etc/motd ]]; then
    cat /etc/motd
fi
EOF
}

# Build the ISO
build_iso() {
    log "Building ISO..."
    
    # Clean work directory
    rm -rf "${WORK_DIR}"
    mkdir -p "${WORK_DIR}"
    mkdir -p "${OUT_DIR}"
    
    # Build
    mkarchiso -v -w "${WORK_DIR}" -o "${OUT_DIR}" "${PROFILE_DIR}"
    
    success "ISO built successfully!"
    log "Output: ${OUT_DIR}/${ISO_NAME}-${ISO_VERSION}-x86_64.iso"
}

# Clean up
cleanup() {
    log "Cleaning up..."
    rm -rf "${WORK_DIR}"
    success "Cleanup complete"
}

# Main
main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║    🧠 KALPANA OS - ISO BUILDER                             ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
    
    check_root
    check_deps
    
    case "${1:-build}" in
        build)
            create_profile
            copy_kalpana_files
            build_iso
            ;;
        clean)
            cleanup
            rm -rf "${PROFILE_DIR}"
            ;;
        profile)
            create_profile
            copy_kalpana_files
            success "Profile ready at ${PROFILE_DIR}"
            ;;
        *)
            echo "Usage: $0 {build|clean|profile}"
            exit 1
            ;;
    esac
}

main "$@"
