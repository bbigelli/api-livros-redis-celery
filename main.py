"""
API REST para Gerenciamento de Livros com Redis e Celery
Endpoints semânticos para melhor compreensão
"""

from fastapi import FastAPI, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field
import json
import redis.asyncio as redis
import os
from celery.result import AsyncResult
from celery_app import celery_app, calcular_soma, calcular_fatorial, gerar_task_id, salvar_task_id_mapping, obter_task_uuid

# ==================== CONFIGURAÇÕES ====================
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CACHE_TTL = 300  # 5 minutos
CACHE_KEY_LIVROS = "livros"

# ==================== INICIALIZAÇÃO ====================
app = FastAPI(
    title="API de Livros com Redis e Celery",
    description="API para gerenciamento de livros com cache Redis e tarefas assíncronas Celery",
    version="1.0.0"
)

# ==================== MODELOS DE DADOS ====================
class Livro(BaseModel):
    """Modelo principal de um livro"""
    id: Optional[int] = Field(default=None, description="ID único do livro")
    titulo: str = Field(..., min_length=1, max_length=200, description="Título do livro")
    autor: str = Field(..., min_length=1, max_length=100, description="Autor do livro")
    ano: int = Field(..., ge=1400, le=2024, description="Ano de publicação")
    
    class Config:
        json_schema_extra = {
            "example": {
                "titulo": "Dom Casmurro",
                "autor": "Machado de Assis",
                "ano": 1899
            }
        }

class LivroUpdate(BaseModel):
    """Modelo para atualização parcial de um livro"""
    titulo: Optional[str] = Field(None, min_length=1, max_length=200)
    autor: Optional[str] = Field(None, min_length=1, max_length=100)
    ano: Optional[int] = Field(None, ge=1400, le=2024)

class TarefaSomaRequest(BaseModel):
    """Modelo para requisição de tarefa de soma"""
    a: float = Field(..., description="Primeiro número")
    b: float = Field(..., description="Segundo número")

class TarefaFatorialRequest(BaseModel):
    """Modelo para requisição de tarefa de fatorial"""
    n: int = Field(..., ge=0, le=100, description="Número para calcular fatorial")

class TarefaResponse(BaseModel):
    """Modelo de resposta para tarefas disparadas"""
    task_id: int
    status: str
    mensagem: str

# ==================== BANCO DE DADOS SIMULADO ====================
livros_db: List[Livro] = []
redis_client = None
proximo_id = 1

# ==================== FUNÇÕES AUXILIARES REDIS ====================
async def get_redis_connection():
    """Retorna o cliente Redis (singleton)"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
            decode_responses=True
        )
    return redis_client

async def salvar_cache_lista_livros(livros: List[Livro]) -> bool:
    """Salva a lista completa de livros no Redis"""
    try:
        client = await get_redis_connection()
        # Usando model_dump() para Pydantic v2
        livros_json = [livro.model_dump() for livro in livros]
        
        await client.setex(
            CACHE_KEY_LIVROS,
            CACHE_TTL,
            json.dumps(livros_json, ensure_ascii=False)
        )
        print(f"✅ Cache salvo: {len(livros)} livros")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar cache: {e}")
        return False

async def buscar_cache_lista_livros() -> Optional[List[Livro]]:
    """Busca a lista de livros do Redis"""
    try:
        client = await get_redis_connection()
        dados = await client.get(CACHE_KEY_LIVROS)
        if dados:
            livros_json = json.loads(dados)
            livros = [Livro(**livro_json) for livro_json in livros_json]
            print(f"✅ Cache recuperado: {len(livros)} livros")
            return livros
        print("ℹ️ Cache não encontrado")
        return None
    except Exception as e:
        print(f"❌ Erro ao buscar cache: {e}")
        return None

async def invalidar_cache_lista_livros() -> bool:
    """Remove o cache da lista de livros"""
    try:
        client = await get_redis_connection()
        await client.delete(CACHE_KEY_LIVROS)
        print("✅ Cache invalidado")
        return True
    except Exception as e:
        print(f"❌ Erro ao invalidar cache: {e}")
        return False

async def encontrar_livro_por_id(livro_id: int) -> Optional[Livro]:
    """Busca um livro no banco de dados por ID"""
    for livro in livros_db:
        if livro.id == livro_id:
            return livro
    return None

# ==================== ENDPOINTS DE LIVROS ====================

@app.get("/listar-livros-com-cache", response_model=List[Livro], tags=["Livros"])
async def listar_livros_com_cache():
    """
    Retorna a lista completa de livros utilizando cache Redis.
    """
    livros_cache = await buscar_cache_lista_livros()
    if livros_cache is not None:
        return livros_cache
    
    if livros_db:
        await salvar_cache_lista_livros(livros_db)
    
    return livros_db

@app.get("/listar-livros-sem-cache", response_model=List[Livro], tags=["Livros"])
async def listar_livros_sem_cache():
    """
    Retorna a lista completa de livros diretamente do banco de dados.
    """
    return livros_db

@app.post("/adicionar-livro", response_model=Livro, status_code=status.HTTP_201_CREATED, tags=["Livros"])
async def adicionar_livro(livro: Livro):
    """
    Adiciona um novo livro à coleção.
    """
    global proximo_id
    
    livro.id = proximo_id
    proximo_id += 1
    
    livros_db.append(livro)
    
    await invalidar_cache_lista_livros()
    
    return livro

@app.put("/atualizar-livro/{livro_id}", response_model=Livro, tags=["Livros"])
async def atualizar_livro(livro_id: int, livro_update: LivroUpdate):
    """
    Atualiza as informações de um livro específico.
    """
    livro = await encontrar_livro_por_id(livro_id)
    if not livro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Livro com ID {livro_id} não encontrado"
        )
    
    # Atualiza apenas os campos fornecidos
    update_data = livro_update.model_dump(exclude_unset=True)
    
    for campo, valor in update_data.items():
        setattr(livro, campo, valor)
    
    await invalidar_cache_lista_livros()
    
    return livro

@app.delete("/deletar-livro/{livro_id}", tags=["Livros"])
async def deletar_livro(livro_id: int):
    """
    Remove um livro da coleção.
    """
    livro = await encontrar_livro_por_id(livro_id)
    if not livro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Livro com ID {livro_id} não encontrado"
        )
    
    livros_db.remove(livro)
    await invalidar_cache_lista_livros()
    
    return {
        "mensagem": f"Livro '{livro.titulo}' (ID: {livro_id}) removido com sucesso",
        "id_removido": livro_id
    }

# ==================== ENDPOINTS DE CACHE ====================

@app.get("/status-cache", tags=["Cache"])
async def status_cache():
    """
    Retorna informações detalhadas sobre o cache Redis.
    """
    try:
        client = await get_redis_connection()
        await client.ping()
        
        dados_lista = await client.get(CACHE_KEY_LIVROS)
        
        return {
            "redis_conectado": True,
            "cache_ativo": dados_lista is not None,
            "tamanho_cache": len(json.loads(dados_lista)) if dados_lista else 0,
            "ttl_configurado": CACHE_TTL,
            "chave_cache": CACHE_KEY_LIVROS
        }
    except Exception as e:
        return {
            "redis_conectado": False,
            "erro": str(e)
        }

@app.get("/ver-cache", tags=["Cache"])
async def ver_cache():
    """
    Visualiza o conteúdo atual do cache.
    """
    livros = await buscar_cache_lista_livros()
    
    if livros:
        return {
            "cache_existe": True,
            "quantidade": len(livros),
            "livros": livros
        }
    else:
        return {
            "cache_existe": False,
            "mensagem": "Nenhum dado em cache"
        }

@app.delete("/limpar-cache", tags=["Cache"])
async def limpar_cache():
    """
    Remove todos os caches do Redis.
    """
    sucesso = await invalidar_cache_lista_livros()
    if sucesso:
        return {
            "mensagem": "✅ Cache limpo com sucesso",
            "cache_removido": CACHE_KEY_LIVROS
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao limpar cache"
        )

# ==================== ENDPOINTS DE TAREFAS CELERY ====================

@app.post("/disparar-soma", response_model=TarefaResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Tarefas"])
async def disparar_tarefa_soma(dados: TarefaSomaRequest):
    """
    Dispara uma tarefa assíncrona para calcular a soma de dois números.
    """
    # Gera ID numérico para a tarefa
    task_id_int = gerar_task_id()
    
    # Dispara a tarefa no Celery
    tarefa = calcular_soma.delay(dados.a, dados.b)
    
    # Salva o mapeamento entre ID inteiro e UUID do Celery
    salvar_task_id_mapping(task_id_int, tarefa.id)
    
    return TarefaResponse(
        task_id=task_id_int,
        status="Tarefa iniciada",
        mensagem=f"Calculando soma de {dados.a} + {dados.b} em background"
    )

@app.post("/disparar-fatorial", response_model=TarefaResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Tarefas"])
async def disparar_tarefa_fatorial(dados: TarefaFatorialRequest):
    """
    Dispara uma tarefa assíncrona para calcular o fatorial de um número.
    """
    # Gera ID numérico para a tarefa
    task_id_int = gerar_task_id()
    
    # Dispara a tarefa no Celery
    tarefa = calcular_fatorial.delay(dados.n)
    
    # Salva o mapeamento entre ID inteiro e UUID do Celery
    salvar_task_id_mapping(task_id_int, tarefa.id)
    
    return TarefaResponse(
        task_id=task_id_int,
        status="Tarefa iniciada",
        mensagem=f"Calculando fatorial de {dados.n}! em background"
    )

@app.get("/status-tarefa/{task_id:int}", tags=["Tarefas"])
async def verificar_status_tarefa(task_id: int):
    """
    Verifica o status de uma tarefa assíncrona.
    """
    # Obtém o UUID do Celery a partir do ID inteiro
    task_uuid = obter_task_uuid(task_id)
    
    if not task_uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {task_id} não encontrada"
        )
    
    resultado = AsyncResult(task_uuid, app=celery_app)
    
    # Verifica o estado da tarefa
    estado = resultado.state
    
    if estado == 'PENDING':
        return {
            "task_id": task_id,
            "status": "PENDENTE",
            "mensagem": "A tarefa está aguardando processamento"
        }
    elif estado == 'STARTED':
        return {
            "task_id": task_id,
            "status": "EXECUTANDO",
            "mensagem": "A tarefa está sendo processada"
        }
    elif estado == 'SUCCESS':
        return {
            "task_id": task_id,
            "status": "CONCLUÍDA",
            "resultado": resultado.result,
            "mensagem": "Tarefa concluída com sucesso"
        }
    elif estado == 'FAILURE':
        return {
            "task_id": task_id,
            "status": "FALHA",
            "erro": str(resultado.info),
            "mensagem": "A tarefa falhou durante a execução"
        }
    elif estado == 'RETRY':
        return {
            "task_id": task_id,
            "status": "REEXECUTANDO",
            "mensagem": "A tarefa será reexecutada"
        }
    elif estado == 'REVOKED':
        return {
            "task_id": task_id,
            "status": "CANCELADA",
            "mensagem": "A tarefa foi cancelada"
        }
    else:
        return {
            "task_id": task_id,
            "status": estado,
            "mensagem": f"Estado: {estado}"
        }

# ==================== ENDPOINT RAIZ ====================
@app.get("/")
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "nome": "API de Livros com Redis e Celery",
        "versao": "1.0.0",
        "documentacao": "/docs",
        "endpoints": {
            "livros": [
                "GET /listar-livros-com-cache",
                "GET /listar-livros-sem-cache",
                "POST /adicionar-livro",
                "PUT /atualizar-livro/{id}",
                "DELETE /deletar-livro/{id}"
            ],
            "cache": [
                "GET /status-cache",
                "GET /ver-cache",
                "DELETE /limpar-cache"
            ],
            "tarefas": [
                "POST /disparar-soma",
                "POST /disparar-fatorial",
                "GET /status-tarefa/{task_id}"
            ]
        }
    }

# ==================== EVENTOS DE INICIALIZAÇÃO ====================
@app.on_event("startup")
async def startup_event():
    """Inicializa conexões e adiciona dados de exemplo"""
    global proximo_id, redis_client
    
    print("\n" + "=" * 60)
    print("🚀 INICIANDO API DE LIVROS COM REDIS E CELERY")
    print("=" * 60)
    
    # Conecta ao Redis
    try:
        redis_client = redis.from_url(
            f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
            decode_responses=True
        )
        await redis_client.ping()
        print("✅ CONEXÃO REDIS: Estabelecida com sucesso")
        print(f"   Host: {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        print(f"⚠️ CONEXÃO REDIS: Não disponível - {e}")
        print("   A API continuará funcionando sem cache")
        redis_client = None
    
    # Dados de exemplo
    print("\n📚 Carregando livros de exemplo...")
    
    livros_exemplo = [
        Livro(id=1, titulo="1984", autor="George Orwell", ano=1949),
        Livro(id=2, titulo="O Pequeno Príncipe", autor="Antoine de Saint-Exupéry", ano=1943),
        Livro(id=3, titulo="Dom Quixote", autor="Miguel de Cervantes", ano=1605),
        Livro(id=4, titulo="Cem Anos de Solidão", autor="Gabriel García Márquez", ano=1967),
        Livro(id=5, titulo="A Metamorfose", autor="Franz Kafka", ano=1915)
    ]
    
    for livro in livros_exemplo:
        livros_db.append(livro)
    
    if livros_db:
        proximo_id = max(livro.id for livro in livros_db) + 1
    
    print(f"✅ {len(livros_db)} livros carregados no banco de dados")
    print(f"🔢 Próximo ID disponível: {proximo_id}")
    
    print("\n" + "=" * 60)
    print("📖 API PRONTA PARA USO!")
    print("📚 Documentação: http://localhost:8000/docs")
    print("\n📌 ENDPOINTS DISPONÍVEIS:")
    print("   📚 Livros:")
    print("      GET    /listar-livros-com-cache")
    print("      GET    /listar-livros-sem-cache")
    print("      POST   /adicionar-livro")
    print("      PUT    /atualizar-livro/{id}")
    print("      DELETE /deletar-livro/{id}")
    print("   🔍 Cache:")
    print("      GET    /status-cache")
    print("      GET    /ver-cache")
    print("      DELETE /limpar-cache")
    print("   🧮 Tarefas:")
    print("      POST   /disparar-soma")
    print("      POST   /disparar-fatorial")
    print("      GET    /status-tarefa/{task_id}")
    print("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Fecha conexões ao desligar"""
    global redis_client
    print("\n" + "=" * 60)
    print("🔌 ENCERRANDO API...")
    
    if redis_client:
        await redis_client.close()
        print("✅ Conexão Redis fechada")
    
    print("👋 API encerrada")
    print("=" * 60)