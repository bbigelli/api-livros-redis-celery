"""
Configuração do Celery com Redis como broker
Tarefas assíncronas para cálculos matemáticos
"""

from celery import Celery
import time
import redis

# Configuração do Celery com Redis
celery_app = Celery(
    'celery_app',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Configurações básicas
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,  # Resultados expiram após 1 hora
)

# Cliente Redis para gerenciar os IDs das tarefas
redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

def gerar_task_id():
    """Gera um ID numérico sequencial para as tarefas"""
    return redis_client.incr('task_id_counter')

def salvar_task_id_mapping(task_id_int, task_uuid):
    """Salva o mapeamento entre ID inteiro e UUID do Celery"""
    redis_client.setex(f'task_mapping:{task_id_int}', 3600, task_uuid)
    redis_client.setex(f'task_uuid_mapping:{task_uuid}', 3600, task_id_int)

def obter_task_uuid(task_id_int):
    """Obtém o UUID do Celery a partir do ID inteiro"""
    return redis_client.get(f'task_mapping:{task_id_int}')

def obter_task_id_int(task_uuid):
    """Obtém o ID inteiro a partir do UUID do Celery"""
    return redis_client.get(f'task_uuid_mapping:{task_uuid}')

# Tarefa para calcular soma
@celery_app.task(name='calcular_soma')
def calcular_soma(a, b):
    """Calcula a soma de dois números com delay de 5 segundos"""
    time.sleep(5)  # Simula operação demorada
    return {
        "operacao": "soma",
        "a": a,
        "b": b,
        "resultado": a + b
    }

# Tarefa para calcular fatorial
@celery_app.task(name='calcular_fatorial')
def calcular_fatorial(n):
    """Calcula o fatorial de um número com delay proporcional"""
    # Simula operação demorada baseada no tamanho do número
    time.sleep(min(n // 10 + 1, 5))
    
    # Calcula fatorial de forma iterativa
    resultado = 1
    for i in range(1, n + 1):
        resultado *= i
    
    return {
        "operacao": "fatorial",
        "numero": n,
        "resultado": resultado
    }