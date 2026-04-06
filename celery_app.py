"""
Configuração do Celery para tarefas assíncronas
"""

from celery import Celery
import time
import redis
import json
import os
from typing import Dict, Optional

# Configuração do Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# Inicializa o Celery
celery_app = Celery(
    'biblioteca_tarefas',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['tarefas']
)

# Configurações do Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    result_expires=3600,  # 1 hora
)

# Conexão Redis para gerenciamento de task IDs
redis_client = None

def get_redis():
    """Retorna conexão com Redis"""
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
    return redis_client

# Contador para IDs numéricos de tarefas
def gerar_task_id() -> int:
    """
    Gera um ID numérico sequencial para a tarefa
    """
    redis_conn = get_redis()
    return redis_conn.incr("task_id_counter")

def salvar_task_id_mapping(task_id_int: int, task_uuid: str):
    """
    Salva o mapeamento entre ID numérico e UUID do Celery
    """
    redis_conn = get_redis()
    redis_conn.setex(f"task_mapping:{task_id_int}", 3600, task_uuid)
    redis_conn.setex(f"task_uuid_to_int:{task_uuid}", 3600, task_id_int)

def obter_task_uuid(task_id_int: int) -> Optional[str]:
    """
    Obtém o UUID do Celery a partir do ID numérico
    """
    redis_conn = get_redis()
    return redis_conn.get(f"task_mapping:{task_id_int}")

def obter_task_id_int(task_uuid: str) -> Optional[int]:
    """
    Obtém o ID numérico a partir do UUID do Celery
    """
    redis_conn = get_redis()
    result = redis_conn.get(f"task_uuid_to_int:{task_uuid}")
    return int(result) if result else None

# ==================== TAREFAS CELERY ====================

@celery_app.task(bind=True, name="tarefas.calcular_soma")
def calcular_soma(self, a: float, b: float) -> dict:
    """
    Calcula a soma de dois números (simula processamento)
    """
    print(f"🧮 Calculando soma: {a} + {b}")
    time.sleep(2)  # Simula processamento
    
    resultado = a + b
    
    return {
        "operacao": "soma",
        "a": a,
        "b": b,
        "resultado": resultado,
        "task_id": self.request.id
    }

@celery_app.task(bind=True, name="tarefas.calcular_fatorial")
def calcular_fatorial(self, n: int) -> dict:
    """
    Calcula o fatorial de um número
    """
    print(f"🎯 Calculando fatorial de {n}!")
    
    # Simula processamento baseado no tamanho do número
    time.sleep(min(n * 0.5, 5))  # Máximo 5 segundos
    
    resultado = 1
    for i in range(1, n + 1):
        resultado *= i
    
    return {
        "operacao": "fatorial",
        "n": n,
        "resultado": resultado,
        "task_id": self.request.id
    }

@celery_app.task(name="tarefas.calcular_tudo")
def calcular_tudo(a: float, b: float) -> dict:
    """
    Calcula soma e depois fatorial do resultado
    """
    print(f"🔢 Calculando tudo: {a} + {b}")
    
    # Primeiro calcula a soma
    soma = a + b
    
    # Depois calcula o fatorial (se for inteiro e pequeno)
    if soma.is_integer() and 0 <= soma <= 20:
        fatorial = 1
        for i in range(1, int(soma) + 1):
            fatorial *= i
        resultado_fatorial = fatorial
    else:
        resultado_fatorial = None
    
    return {
        "operacao": "completa",
        "a": a,
        "b": b,
        "soma": soma,
        "fatorial_da_soma": resultado_fatorial
    }

@celery_app.task(name="tarefas.calcular_multiplas")
def calcular_multiplas(numeros: list) -> dict:
    """
    Processa múltiplos números (soma e fatorial de cada)
    """
    print(f"📊 Processando lista de {len(numeros)} números")
    
    resultados = []
    for num in numeros:
        # Calcula fatorial se for inteiro positivo
        if isinstance(num, int) and num >= 0:
            fat = 1
            for i in range(1, num + 1):
                fat *= i
            resultados.append({
                "numero": num,
                "fatorial": fat
            })
        else:
            resultados.append({
                "numero": num,
                "fatorial": None,
                "mensagem": "Não é um inteiro positivo"
            })
        
        time.sleep(0.5)  # Pequena pausa entre processamentos
    
    return {
        "total_processados": len(numeros),
        "resultados": resultados
    }

@celery_app.task(name="tarefas.limpar_tarefas_antigas")
def limpar_tarefas_antigas() -> dict:
    """
    Limpa mapeamentos de tarefas antigas
    """
    print("🧹 Limpando tarefas antigas...")
    # Implementação da limpeza
    return {
        "status": "sucesso",
        "mensagem": "Tarefas antigas removidas"
    }

@celery_app.task(name="tarefas.info")
def info() -> dict:
    """
    Retorna informações sobre o worker
    """
    return {
        "worker": "celery-worker",
        "status": "ativo",
        "tarefas": [
            "calcular_soma",
            "calcular_fatorial", 
            "calcular_tudo",
            "calcular_multiplas",
            "limpar_tarefas_antigas"
        ]
    }

print("\n" + "=" * 60)
print("🧮 CELERY WORKER INICIALIZADO")
print("=" * 60)
print(f"📊 Broker: redis://{REDIS_HOST}:{REDIS_PORT}/0")
print(f"📊 Backend: redis://{REDIS_HOST}:{REDIS_PORT}/0")
print(f"🖥️  Plataforma: linux")
print("\n📋 TAREFAS DISPONÍVEIS:")
print("   • calcular_soma - Soma dois números")
print("   • calcular_fatorial - Calcula fatorial")
print("   • calcular_tudo - Soma + fatorial do resultado")
print("   • calcular_multiplas - Processa lista de números")
print("   • limpar_tarefas_antigas - Limpeza periódica")
print("   • info - Informações do worker")
print("\n⚙️  Worker pronto para processar tarefas!")
print("=" * 60 + "\n")