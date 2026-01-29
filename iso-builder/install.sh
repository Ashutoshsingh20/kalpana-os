#!/bin/bash
# ============================================================================
# Kalpana OS - Installer Script
# ============================================================================
# Installs Kalpana OS to a target disk.
# Run from live environment.
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${CYAN}[KALPANA]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# Kalpana banner
show_banner() {
    clear
    echo -e "${CYAN}"
    cat << 'EOF'
    ██╗  ██╗ █████╗ ██╗     ██████╗  █████╗ ███╗   ██╗ █████╗ 
    ██║ ██╔╝██╔══██╗██║     ██╔══██╗██╔══██╗████╗  ██║██╔══██╗
    █████╔╝ ███████║██║     ██████╔╝███████║██╔██╗ ██║███████║
    ██╔═██╗ ██╔══██║██║     ██╔═══╝ ██╔══██║██║╚██╗██║██╔══██║
    ██║  ██╗██║  ██║███████╗██║     ██║  ██║██║ ╚████║██║  ██║
    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
                                                    
                    🧠 AI-Native OS Installer
EOF
    echo -e "${NC}"
}

# Detect available disks
detect_disks() {
    log "Available disks:"
    echo ""
    lsblk -d -o NAME,SIZE,MODEL | grep -v "loop\|sr"
    echo ""
}

# Get user input for disk
get_target_disk() {
    read -p "Enter target disk (e.g., sda, nvme0n1): " DISK
    
    if [[ ! -b "/dev/${DISK}" ]]; then
        error "Invalid disk: /dev/${DISK}"
    fi
    
    TARGET_DISK="/dev/${DISK}"
    
    warn "This will ERASE ALL DATA on ${TARGET_DISK}!"
    read -p "Are you sure? (yes/no): " confirm
    
    if [[ "$confirm" != "yes" ]]; then
        error "Installation cancelled"
    fi
}

# Partition disk
partition_disk() {
    log "Partitioning ${TARGET_DISK}..."
    
    # Detect if UEFI or BIOS
    if [[ -d /sys/firmware/efi ]]; then
        BOOT_MODE="uefi"
        log "Detected UEFI boot mode"
    else
        BOOT_MODE="bios"
        log "Detected BIOS boot mode"
    fi
    
    # Wipe disk
    wipefs -a "${TARGET_DISK}"
    
    if [[ "$BOOT_MODE" == "uefi" ]]; then
        # GPT + EFI partition
        parted -s "${TARGET_DISK}" mklabel gpt
        parted -s "${TARGET_DISK}" mkpart ESP fat32 1MiB 513MiB
        parted -s "${TARGET_DISK}" set 1 esp on
        parted -s "${TARGET_DISK}" mkpart primary ext4 513MiB 100%
        
        # Determine partition names
        if [[ "${TARGET_DISK}" == *"nvme"* ]]; then
            EFI_PART="${TARGET_DISK}p1"
            ROOT_PART="${TARGET_DISK}p2"
        else
            EFI_PART="${TARGET_DISK}1"
            ROOT_PART="${TARGET_DISK}2"
        fi
        
        # Format
        mkfs.fat -F32 "${EFI_PART}"
        mkfs.ext4 -F "${ROOT_PART}"
        
    else
        # MBR + single root partition
        parted -s "${TARGET_DISK}" mklabel msdos
        parted -s "${TARGET_DISK}" mkpart primary ext4 1MiB 100%
        parted -s "${TARGET_DISK}" set 1 boot on
        
        if [[ "${TARGET_DISK}" == *"nvme"* ]]; then
            ROOT_PART="${TARGET_DISK}p1"
        else
            ROOT_PART="${TARGET_DISK}1"
        fi
        
        mkfs.ext4 -F "${ROOT_PART}"
        EFI_PART=""
    fi
    
    success "Disk partitioned"
}

# Mount partitions
mount_partitions() {
    log "Mounting partitions..."
    
    mount "${ROOT_PART}" /mnt
    
    if [[ -n "$EFI_PART" ]]; then
        mkdir -p /mnt/boot/efi
        mount "${EFI_PART}" /mnt/boot/efi
    fi
    
    success "Partitions mounted"
}

# Install base system
install_base() {
    log "Installing base system..."
    
    # Base packages
    pacstrap /mnt base base-devel linux linux-firmware \
        networkmanager grub efibootmgr \
        python python-pip python-numpy \
        vim nano git wget curl \
        pipewire wireplumber \
        sway foot waybar wofi \
        espeak-ng brightnessctl playerctl
    
    success "Base system installed"
}

# Copy Kalpana OS
install_kalpana() {
    log "Installing Kalpana OS..."
    
    # Copy Kalpana files
    mkdir -p /mnt/opt/kalpana
    cp -r /opt/kalpana/* /mnt/opt/kalpana/
    
    # Copy systemd units
    cp /usr/lib/systemd/system/kalpana-*.service /mnt/usr/lib/systemd/system/
    
    # Copy launcher scripts
    cp /usr/local/bin/kalpana-* /mnt/usr/local/bin/
    
    # Enable services
    arch-chroot /mnt systemctl enable kalpana-core.service
    arch-chroot /mnt systemctl enable NetworkManager.service
    
    success "Kalpana OS installed"
}

# Configure system
configure_system() {
    log "Configuring system..."
    
    # Generate fstab
    genfstab -U /mnt >> /mnt/etc/fstab
    
    # Set timezone
    arch-chroot /mnt ln -sf /usr/share/zoneinfo/UTC /etc/localtime
    arch-chroot /mnt hwclock --systohc
    
    # Locale
    echo "en_US.UTF-8 UTF-8" > /mnt/etc/locale.gen
    arch-chroot /mnt locale-gen
    echo "LANG=en_US.UTF-8" > /mnt/etc/locale.conf
    
    # Hostname
    echo "kalpana" > /mnt/etc/hostname
    cat > /mnt/etc/hosts << 'EOF'
127.0.0.1   localhost
::1         localhost
127.0.1.1   kalpana.local kalpana
EOF
    
    success "System configured"
}

# Install bootloader
install_bootloader() {
    log "Installing bootloader..."
    
    if [[ "$BOOT_MODE" == "uefi" ]]; then
        arch-chroot /mnt grub-install --target=x86_64-efi \
            --efi-directory=/boot/efi --bootloader-id=KalpanaOS
    else
        arch-chroot /mnt grub-install --target=i386-pc "${TARGET_DISK}"
    fi
    
    # Configure GRUB
    sed -i 's/GRUB_TIMEOUT=5/GRUB_TIMEOUT=3/' /mnt/etc/default/grub
    sed -i 's/GRUB_DISTRIBUTOR="Arch"/GRUB_DISTRIBUTOR="Kalpana OS"/' /mnt/etc/default/grub
    
    arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg
    
    success "Bootloader installed"
}

# Create user
create_user() {
    log "Creating user..."
    
    read -p "Enter username: " username
    
    arch-chroot /mnt useradd -m -G wheel,audio,video -s /bin/bash "$username"
    
    log "Set password for $username:"
    arch-chroot /mnt passwd "$username"
    
    # Enable sudo for wheel group
    echo "%wheel ALL=(ALL:ALL) ALL" > /mnt/etc/sudoers.d/wheel
    
    success "User created"
}

# Finalize
finalize() {
    log "Finalizing installation..."
    
    # Unmount
    umount -R /mnt
    
    success "Installation complete!"
    echo ""
    log "Remove installation media and reboot to start Kalpana OS"
    log "Login and run: kalpana-shell"
    echo ""
}

# Main
main() {
    show_banner
    
    detect_disks
    get_target_disk
    partition_disk
    mount_partitions
    install_base
    install_kalpana
    configure_system
    install_bootloader
    create_user
    finalize
}

main "$@"
