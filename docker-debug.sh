#!/bin/bash

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========== Docker Debug Script ==========${NC}"

# Check if Docker is running
echo -e "${YELLOW}Checking if Docker is running...${NC}"
if ! docker info >/dev/null 2>&1; then
  echo -e "${RED}Docker is not running. Please start Docker and try again.${NC}"
  exit 1
else
  echo -e "${GREEN}Docker is running.${NC}"
fi

# List all containers
echo -e "\n${YELLOW}Listing all containers...${NC}"
docker ps -a

# Check container status
echo -e "\n${YELLOW}Checking container status...${NC}"
BACKEND_RUNNING=$(docker ps -q -f name=fact-check-backend)
FRONTEND_RUNNING=$(docker ps -q -f name=fact-check-frontend)

if [ -z "$BACKEND_RUNNING" ]; then
  echo -e "${RED}Backend container is not running!${NC}"
  echo -e "${YELLOW}Checking backend container logs...${NC}"
  docker logs fact-check-backend 2>&1 | tail -50
else
  echo -e "${GREEN}Backend container is running.${NC}"
fi

if [ -z "$FRONTEND_RUNNING" ]; then
  echo -e "${RED}Frontend container is not running!${NC}"
  echo -e "${YELLOW}Checking frontend container logs...${NC}"
  docker logs fact-check-frontend 2>&1 | tail -50
else
  echo -e "${GREEN}Frontend container is running.${NC}"
fi

# Check network connectivity
echo -e "\n${YELLOW}Checking network connectivity...${NC}"
if [ ! -z "$BACKEND_RUNNING" ] && [ ! -z "$FRONTEND_RUNNING" ]; then
  echo -e "${YELLOW}Testing if frontend can connect to backend...${NC}"
  docker exec fact-check-frontend wget -q --spider --timeout=2 http://backend:8000 && \
    echo -e "${GREEN}Frontend can connect to backend.${NC}" || \
    echo -e "${RED}Frontend cannot connect to backend!${NC}"
fi

# Check file permissions in containers
echo -e "\n${YELLOW}Checking file permissions in frontend container...${NC}"
if [ ! -z "$FRONTEND_RUNNING" ]; then
  echo -e "${YELLOW}Static files in Nginx:${NC}"
  docker exec fact-check-frontend ls -la /usr/share/nginx/html | head -10
fi

echo -e "\n${YELLOW}Checking file permissions in backend container...${NC}"
if [ ! -z "$BACKEND_RUNNING" ]; then
  echo -e "${YELLOW}Uploads directory:${NC}"
  docker exec fact-check-backend ls -la /app/uploads
fi

# Check environment variables
echo -e "\n${YELLOW}Checking if .env file is properly mounted...${NC}"
if [ ! -z "$BACKEND_RUNNING" ]; then
  echo -e "${YELLOW}Checking for environment variables in backend:${NC}"
  docker exec fact-check-backend env | grep -E "OPENAI|MODEL|ALLOWED" | \
    sed 's/\(OPENAI_API_KEY=\).*/\1[REDACTED]/' || \
    echo -e "${RED}No environment variables found!${NC}"
fi

echo -e "\n${BLUE}========== Debugging Suggestions ==========${NC}"
echo -e "${GREEN}If containers are not running:${NC}"
echo -e "1. Run 'docker-compose logs' to see detailed error messages"
echo -e "2. Make sure your .env file exists and has the correct values"
echo -e "3. Try rebuilding with 'docker-compose up -d --build'"

echo -e "\n${GREEN}If permission errors:${NC}"
echo -e "1. Check the file ownership in the containers"
echo -e "2. Make sure volumes are correctly mounted"

echo -e "\n${GREEN}If network errors:${NC}"
echo -e "1. Check if all services are running"
echo -e "2. Verify the service names in docker-compose.yml match what's used in the code"
echo -e "3. Check if nginx configuration is correctly set up for proxying"

echo -e "\n${GREEN}For other issues:${NC}"
echo -e "1. Try stopping all containers with 'docker-compose down'"
echo -e "2. Remove all volumes with 'docker-compose down -v'"
echo -e "3. Rebuild from scratch with 'docker-compose up -d --build'"

echo -e "\n${BLUE}========== End of Debugging Info ==========${NC}" 