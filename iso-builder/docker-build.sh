#!/bin/bash
# ============================================================================
# Kalpana OS - Docker ISO Builder
# ============================================================================
# Builds Kalpana OS ISO using Docker (works on macOS/Linux/Windows)
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
IMAGE_NAME="kalpana-iso-builder"
CONTAINER_NAME="kalpana-build"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${CYAN}[KALPANA]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

# Check Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Docker is required. Install from: https://docker.com"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "Docker daemon is not running. Start Docker Desktop."
        exit 1
    fi
    
    success "Docker is available"
}

# Build Docker image
build_image() {
    log "Building Docker image..."
    
    docker build --platform linux/amd64 -t "$IMAGE_NAME" -f - "$PROJECT_DIR" << 'DOCKERFILE'
FROM --platform=linux/amd64 archlinux:latest

# Initialize keyring and update system
RUN pacman-key --init && \
    pacman-key --populate archlinux && \
    pacman -Sy --noconfirm archlinux-keyring && \
    pacman -Syu --noconfirm

# Install archiso and dependencies
RUN pacman -S --noconfirm \
    archiso \
    mkinitcpio \
    mkinitcpio-archiso \
    git \
    squashfs-tools \
    libisoburn \
    dosfstools \
    e2fsprogs \
    mtools \
    which

# Verify archiso is installed
RUN command -v mkarchiso && ls -la /usr/bin/mkarchiso

# Create work directory
WORKDIR /build

# Copy project files
COPY . /build/kalpana-os

# Make scripts executable
RUN chmod +x /build/kalpana-os/iso-builder/*.sh

# Run the build script
CMD ["/bin/bash", "-c", "cd /build/kalpana-os/iso-builder && ./build-iso.sh build"]
DOCKERFILE

    success "Docker image built"
}

# Run build
run_build() {
    log "Starting ISO build in container..."
    
    # Create output directory
    mkdir -p "$PROJECT_DIR/out"
    
    # Run container with privileged mode (required for loop devices)
    docker run --rm \
        --platform linux/amd64 \
        --privileged \
        --name "$CONTAINER_NAME" \
        -v "$PROJECT_DIR/out:/build/kalpana-os/out" \
        "$IMAGE_NAME"
    
    success "Build complete!"
    log "ISO available at: $PROJECT_DIR/out/"
}

# Clean up
cleanup() {
    log "Cleaning up..."
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    docker rmi "$IMAGE_NAME" 2>/dev/null || true
    success "Cleanup complete"
}

# Main
main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║    🧠 KALPANA OS - Docker ISO Builder                      ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
    
    case "${1:-build}" in
        build)
            check_docker
            build_image
            run_build
            ;;
        clean)
            cleanup
            ;;
        image)
            check_docker
            build_image
            ;;
        *)
            echo "Usage: $0 {build|clean|image}"
            exit 1
            ;;
    esac
}

main "$@"
