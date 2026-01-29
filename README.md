# Kalpana OS

## Vision
Kalpana OS is an AI-native, security-first operating system where Kalpana AI acts as the **mandatory system authority**. Based on Arch Linux.

## Project Structure

```
kalpana-os/
├── kalpana-core/       # Root-level authority daemon
├── kalpana-shell/      # Natural language shell
├── kalpana-ui/         # Wayland desktop environment
├── kalpana-security/   # Network & security stack
├── systemd-units/      # Boot configuration
├── iso-builder/        # Arch ISO customization
├── docs/               # Documentation
├── scripts/            # Build & utility scripts
└── tests/              # System tests
```

## Quick Start (Development)

```bash
# Test in Arch VM
./scripts/setup-dev-vm.sh

# Build ISO
./scripts/build-iso.sh
```

## Architecture

Kalpana Core starts as the first user-space service and mediates ALL system actions.

## License
Proprietary - Kalpana Project
