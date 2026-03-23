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
