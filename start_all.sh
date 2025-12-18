#!/bin/bash
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

export MYSQL_HOST=localhost
export REDIS_HOST=localhost
export NACOS_SERVER_ADDR=127.0.0.1:8848
export RABBITMQ_HOST=localhost
export CHROMA_HOST=localhost
export JAEGER_HOST=localhost

export NACOS_USERNAME=""
export NACOS_PASSWORD=""
export NACOS_NAMESPACE=""

PYTHON_EXEC="/opt/anaconda3/envs/fastapi_env/bin/python"

cleanup() {
    echo -e "${BLUE}Stopping all services...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit
}
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}Starting LLM Micro-Architecture Services...${NC}"

echo -e "${BLUE}Starting Vector Service (Port 50051)...${NC}"
$PYTHON_EXEC -m backend.vector_service.main &
PID_VECTOR=$!
sleep 2

echo -e "${BLUE}Starting Knowledge Service (Port 50052)...${NC}"
$PYTHON_EXEC -m backend.knowledge_service.main &
PID_KNOWLEDGE=$!
sleep 2

echo -e "${BLUE}Starting Cost Service (Port 50053)...${NC}"
$PYTHON_EXEC -m backend.cost_service.main &
PID_COST=$!
sleep 2

echo -e "${BLUE}Starting Auth Service (Port 8003)...${NC}"
$PYTHON_EXEC -m backend.auth_service.main &
PID_AUTH=$!
sleep 3

echo -e "${BLUE}Starting RAG Engine (Port 8002)...${NC}"
$PYTHON_EXEC -m backend.rag_engine.main &
PID_RAG=$!
sleep 3

# Gateway is usually the entry point. Let's check its port.
echo -e "${BLUE}Starting Gateway Service (Port 8081)...${NC}"
$PYTHON_EXEC -m backend.gateway_service.main &
PID_GATEWAY=$!
sleep 3

echo -e "${BLUE}Starting Frontend...${NC}"
cd frontend
npm run dev &
PID_FRONTEND=$!
cd ..

echo -e "${GREEN}All services started! Access the application at http://localhost:5173${NC}"
echo -e "${BLUE}Press Ctrl+C to stop all services.${NC}"

wait
