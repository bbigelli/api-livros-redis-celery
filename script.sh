#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DEPLOYMENT="deployment.yaml"
SERVICE="service.yaml"
DEPLOYMENT_NAME="api-livros"
SERVICE_NAME="api-livros-service"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploy da API de Livros no Kubernetes${NC}"
echo -e "${GREEN}========================================${NC}"

# Configura ambiente do Minikube
echo -e "\n${YELLOW}Configurando ambiente Docker do Minikube...${NC}"
eval $(minikube docker-env)

# Build da imagem
echo -e "\n${YELLOW}Build da imagem Docker...${NC}"
if [ -f "Dockerfile" ]; then
    docker build -t api-livros:latest .
    echo -e "${GREEN}✅ Imagem api-livros construída${NC}"
else
    echo -e "${RED}❌ Dockerfile não encontrado${NC}"
    exit 1
fi

# Aplica os recursos
echo -e "\n${YELLOW}Aplicando deployment...${NC}"
kubectl apply -f $DEPLOYMENT

echo -e "\n${YELLOW}Aplicando service...${NC}"
kubectl apply -f $SERVICE

# Aguarda pods
echo -e "\n${YELLOW}Aguardando pods iniciarem...${NC}"
kubectl wait --for=condition=available --timeout=120s deployment/$DEPLOYMENT_NAME

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment está rodando!${NC}"
else
    echo -e "${YELLOW}Verificando status dos pods...${NC}"
    kubectl get pods
fi

# Port-forward
echo -e "\n${GREEN}✅ Aplicação disponível em: http://localhost:8000${NC}"
echo -e "${YELLOW}Pressione Ctrl+C para parar${NC}\n"

kubectl port-forward service/$SERVICE_NAME 8000:8000