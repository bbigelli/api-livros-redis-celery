# 📚 API de Livros com Redis e Celery

API REST desenvolvida com FastAPI para gerenciamento de livros, utilizando Redis como camada de cache e Celery para processamento assíncrono de tarefas longas.

## 🚀 Tecnologias Utilizadas

- **FastAPI** - Framework web moderno e rápido
- **Redis** - Banco de dados em memória para cache
- **Celery** - Sistema de filas para tarefas assíncronas
- **Docker** - Containerização do Redis

## ✨ Funcionalidades

- ✅ CRUD completo de livros
- ✅ Cache Redis para consultas frequentes
- ✅ Invalidação automática de cache
- ✅ Tarefas assíncronas com Celery:
  - Soma de dois números (delay de 5 segundos)
  - Fatorial de um número
- ✅ Task IDs numéricos sequenciais
- ✅ Documentação interativa automática

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Docker Desktop (recomendado) ou Redis instalado
- Git

### 🔧 Instalação da API
Passo 1: Clone o repositório
bash
git clone https://github.com/bbigelli/api-livros-redis-celery.git
cd api-livros-redis-celery

### # Instalar todas as dependências
pip install -r requirements.txt

### Inicie o Redis com Docker
docker run -d --name redis-livros -p 6379:6379 redis:latest

### ▶️ Como Executar
Terminal 1: Celery Worker

celery -A celery_app worker --loglevel=info --pool=solo

### Terminal 2: API FastAPI

uvicorn main:app --reload --host 0.0.0.0 --port 8000

### 📚 Endpoints da API
### Livros

Método	Endpoint	                Descrição
GET	    /listar-livros-com-cache	Lista livros com cache
GET	    /listar-livros-sem-cache	Lista livros sem cache
POST	  /adicionar-livro	        Adiciona novo livro
PUT	    /atualizar-livro/{id}	    Atualiza livro
DELETE	/deletar-livro/{id}	      Remove livro

### Cache
Método	Endpoint	     Descrição
GET	    /status-cache	 Status do Redis
GET	    /ver-cache	   Conteúdo do cache
DELETE	/limpar-cache	 Limpa cache

### Tarefas
Método	Endpoint	                  Descrição
POST	  /disparar-soma	            Tarefa de soma
POST	  /disparar-fatorial	        Tarefa de fatorial
GET	    /status-tarefa/{task_id}	  Status da tarefa

# Ambiente Kafka com Docker Compose

Este projeto configura um ambiente completo para desenvolvimento com Apache Kafka usando Docker Compose.

## 📋 Serviços Incluídos

| Serviço | Imagem | Porta | Descrição |
|---------|--------|------|-----------|
| **ZooKeeper** | confluentinc/cp-zookeeper | 2181 | Serviço de coordenação necessário para o Kafka |
| **Kafka** | confluentinc/cp-kafka | 9092 | Broker de mensagens para streaming de dados |
| **Kafka-UI** | provectuslabs/kafka-ui | 8080 | Interface gráfica para gerenciamento e monitoramento |

## 🚀 Pré-requisitos

- Docker (versão 20.10 ou superior)
- Docker Compose (versão 2.0 ou superior)

## 📦 Como Executar

### Passo 1: Clone ou baixe os arquivos
Certifique-se de ter o arquivo `docker-compose.yml` na raiz do projeto.

### Passo 2: Inicie os serviços

docker-compose up -d

### Passo 3: Verifique se os containers estão rodando

docker ps

### Passo 4: Acesse a interface do Kafka-UI

http://localhost:8080