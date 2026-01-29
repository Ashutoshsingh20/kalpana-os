#!/bin/bash
# Kalpana OS Development Test Script
# Run from kalpana-os directory

set -e

echo "🧪 Kalpana OS Development Test Suite"
echo "====================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Test 1: Core daemon starts
test_core_daemon() {
    echo -e "\n${YELLOW}Test 1: Kalpana Core Daemon${NC}"
    
    cd "$PROJECT_ROOT/kalpana-core/src"
    
    # Start core in background
    python3 main.py &
    CORE_PID=$!
    
    sleep 2
    
    # Check if running
    if ps -p $CORE_PID > /dev/null; then
        echo -e "${GREEN}✅ Core daemon started successfully${NC}"
        
        # Check socket exists
        if [ -S "/tmp/kalpana-core.sock" ]; then
            echo -e "${GREEN}✅ IPC socket created${NC}"
        else
            echo -e "${RED}❌ IPC socket not found${NC}"
        fi
        
        # Kill the daemon
        kill $CORE_PID 2>/dev/null || true
        wait $CORE_PID 2>/dev/null || true
    else
        echo -e "${RED}❌ Core daemon failed to start${NC}"
        return 1
    fi
}

# Test 2: IPC Client
test_ipc_client() {
    echo -e "\n${YELLOW}Test 2: IPC Client${NC}"
    
    cd "$PROJECT_ROOT/kalpana-core/src"
    
    # Start core daemon
    python3 main.py &
    CORE_PID=$!
    sleep 2
    
    # Run IPC client test
    python3 ipc_client.py
    RESULT=$?
    
    # Cleanup
    kill $CORE_PID 2>/dev/null || true
    wait $CORE_PID 2>/dev/null || true
    
    if [ $RESULT -eq 0 ]; then
        echo -e "${GREEN}✅ IPC client test passed${NC}"
    else
        echo -e "${RED}❌ IPC client test failed${NC}"
    fi
}

# Test 3: Shell (non-interactive)
test_shell() {
    echo -e "\n${YELLOW}Test 3: Kalpana Shell${NC}"
    
    cd "$PROJECT_ROOT/kalpana-shell/src"
    
    # Just check import works
    python3 -c "from shell import KalpanaShell; print('Shell module OK')"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Shell module loads correctly${NC}"
    else
        echo -e "${RED}❌ Shell module failed to load${NC}"
    fi
}

# Run all tests
echo ""
test_core_daemon
test_ipc_client  
test_shell

echo -e "\n${GREEN}====================================="
echo "All tests completed!"
echo -e "=====================================${NC}"
