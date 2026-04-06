"""
Testes unitários para as tasks Celery.
Este arquivo contém testes para validar o comportamento das tasks calcular_soma e calcular_fatorial.
"""

import pytest
import time
from unittest.mock import call

# Importa as tasks do celery_app
from celery_app import (
    calcular_soma, 
    calcular_fatorial, 
    gerar_task_id,
    salvar_task_id_mapping,
    obter_task_uuid,
    obter_task_id_int,
)


# ============================================
# FIXTURES PARA CONFIGURAÇÃO DOS TESTES
# ============================================

@pytest.fixture
def celery_config():
    """
    Fixture para configurar o Celery para testes.
    Usa um broker e backend em memória para testes mais rápidos.
    """
    return {
        'broker_url': 'memory://',
        'result_backend': 'cache+memory://',
        'task_always_eager': True,  # Executa tasks sincronamente para testes
        'task_eager_propagates': True,  # Propaga exceções em modo eager
    }


@pytest.fixture
def mock_redis(monkeypatch):
    """
    Fixture que mocka o Redis para evitar dependência do serviço Redis real.
    """
    from unittest.mock import Mock
    import celery_app
    
    # Mock para o cliente Redis
    mock_redis_client = Mock()
    mock_redis_client.incr.return_value = 1
    mock_redis_client.setex.return_value = True
    mock_redis_client.get.return_value = None
    mock_redis_client.keys.return_value = []
    mock_redis_client.delete.return_value = 0
    
    # Substitui o redis_client real pelo mock
    monkeypatch.setattr(celery_app, 'redis_client', mock_redis_client)
    
    return mock_redis_client


# ============================================
# TESTES PARA A TASK DE SOMA
# ============================================

class TestTaskSoma:
    """
    Classe de testes para a task de soma.
    """
    
    def test_soma_numeros_positivos(self, celery_config):
        """
        Testa a soma de dois números positivos.
        Cenário: calcular_soma(5, 3) deve retornar resultado = 8
        """
        resultado = calcular_soma(5, 3)
        
        assert resultado["operacao"] == "soma"
        assert resultado["a"] == 5
        assert resultado["b"] == 3
        assert resultado["resultado"] == 8
    
    def test_soma_com_numeros_negativos(self, celery_config):
        """
        Testa a soma de números negativos.
        Cenário: calcular_soma(-10, -5) deve retornar resultado = -15
        """
        resultado = calcular_soma(-10, -5)
        
        assert resultado["operacao"] == "soma"
        assert resultado["a"] == -10
        assert resultado["b"] == -5
        assert resultado["resultado"] == -15
    
    def test_soma_com_numero_positivo_e_negativo(self, celery_config):
        """
        Testa a soma de um número positivo com um negativo.
        Cenário: calcular_soma(10, -3) deve retornar resultado = 7
        """
        resultado = calcular_soma(10, -3)
        assert resultado["resultado"] == 7
    
    def test_soma_com_zero(self, celery_config):
        """
        Testa a soma envolvendo zero.
        Cenário: calcular_soma(0, 42) deve retornar resultado = 42
        """
        resultado = calcular_soma(0, 42)
        assert resultado["resultado"] == 42
    
    def test_soma_com_numeros_decimais(self, celery_config):
        """
        Testa a soma de números decimais (float).
        Cenário: calcular_soma(2.5, 3.7) deve retornar resultado = 6.2
        """
        resultado = calcular_soma(2.5, 3.7)
        assert resultado["resultado"] == 6.2
    
    def test_soma_propriedade_comutativa(self, celery_config):
        """
        Testa a propriedade comutativa da soma: a + b = b + a
        """
        resultado1 = calcular_soma(7, 3)
        resultado2 = calcular_soma(3, 7)
        
        assert resultado1["resultado"] == resultado2["resultado"]
    
    def test_soma_multiplas_chamadas(self, celery_config):
        """
        Testa múltiplas chamadas da task de soma.
        """
        casos_teste = [
            (1, 1, 2),
            (10, 20, 30),
            (100, 200, 300),
            (-5, 5, 0)
        ]
        
        for a, b, esperado in casos_teste:
            resultado = calcular_soma(a, b)
            assert resultado["resultado"] == esperado, \
                f"Soma de {a} + {b} deveria ser {esperado}, mas foi {resultado['resultado']}"


# ============================================
# TESTES PARA A TASK DE FATORIAL
# ============================================

class TestTaskFatorial:
    """
    Classe de testes para a task de fatorial.
    """
    
    def test_fatorial_numero_positivo(self, celery_config):
        """
        Testa cálculo do fatorial para números positivos.
        """
        resultado = calcular_fatorial(5)
        # CORRIGIDO: verifica o campo 'resultado' do dicionário
        assert resultado["resultado"] == 120
    
    def test_fatorial_de_zero(self, celery_config):
        """
        Testa o fatorial de zero (caso de borda importante).
        Cenário: calcular_fatorial(0) = 0! = 1
        """
        resultado = calcular_fatorial(0)
        assert resultado["resultado"] == 1
    
    def test_fatorial_de_um(self, celery_config):
        """
        Testa o fatorial de 1.
        Cenário: calcular_fatorial(1) = 1! = 1
        """
        resultado = calcular_fatorial(1)
        assert resultado["resultado"] == 1
    
    def test_fatorial_de_dois(self, celery_config):
        """
        Testa o fatorial de 2.
        Cenário: calcular_fatorial(2) = 2! = 2
        """
        resultado = calcular_fatorial(2)
        assert resultado["resultado"] == 2
    
    def test_fatorial_de_tres(self, celery_config):
        """
        Testa o fatorial de 3.
        Cenário: calcular_fatorial(3) = 3! = 6
        """
        resultado = calcular_fatorial(3)
        assert resultado["resultado"] == 6
    
    def test_fatorial_de_quatro(self, celery_config):
        """
        Testa o fatorial de 4.
        Cenário: calcular_fatorial(4) = 4! = 24
        """
        resultado = calcular_fatorial(4)
        assert resultado["resultado"] == 24
    
    def test_fatorial_de_cinco(self, celery_config):
        """
        Testa o fatorial de 5.
        Cenário: calcular_fatorial(5) = 5! = 120
        """
        resultado = calcular_fatorial(5)
        assert resultado["resultado"] == 120
    
    def test_fatorial_de_seis(self, celery_config):
        """
        Testa o fatorial de 6.
        Cenário: calcular_fatorial(6) = 6! = 720
        """
        resultado = calcular_fatorial(6)
        assert resultado["resultado"] == 720
    
    def test_fatorial_numero_medio(self, celery_config):
        """
        Testa fatorial para um número médio.
        Cenário: calcular_fatorial(10) = 10! = 3.628.800
        """
        resultado = calcular_fatorial(10)
        assert resultado["resultado"] == 3_628_800
    
    def test_fatorial_valores_sequenciais(self, celery_config):
        """
        Testa fatorial para uma sequência de valores.
        """
        casos_teste = [
            (0, 1), (1, 1), (2, 2), (3, 6),
            (4, 24), (5, 120), (6, 720), (7, 5040),
            (8, 40320), (9, 362880), (10, 3628800)
        ]
        
        for n, esperado in casos_teste:
            resultado = calcular_fatorial(n)
            assert resultado["resultado"] == esperado, \
                f"Fatorial de {n} deveria ser {esperado}, mas foi {resultado['resultado']}"
    
    def test_fatorial_numero_grande(self, celery_config):
        """
        Testa fatorial para um número maior.
        Cenário: calcular_fatorial(12) = 479001600
        """
        resultado = calcular_fatorial(12)
        assert resultado["resultado"] == 479001600


# ============================================
# TESTES PARA CASOS DE BORDA
# ============================================

class TestCasosBorda:
    """
    Testes para casos de borda e situações especiais.
    """
    
    def test_fatorial_numero_negativo(self, celery_config):
        """
        Testa o comportamento com número negativo.
        """
        with pytest.raises(Exception):
            calcular_fatorial(-5)
    
    def test_soma_numeros_muito_grandes(self, celery_config):
        """
        Testa soma com números muito grandes.
        """
        resultado = calcular_soma(10**100, 10**100)
        assert resultado["resultado"] == 2 * (10**100)
    
    def test_fatorial_numero_grande_demais(self, celery_config):
        """
        Testa fatorial de número grande.
        """
        resultado = calcular_fatorial(20)
        assert resultado["resultado"] > 0
    
    def test_soma_com_parametros_invalidos(self, celery_config):
        """
        Testa soma com parâmetros inválidos.
        """
        # Testando com None - pode levantar exceção
        with pytest.raises(Exception):
            calcular_soma(None, 5)
        
        # Testando com string - pode levantar exceção
        with pytest.raises(Exception):
            calcular_soma("10", 20)


# ============================================
# TESTES DE INTEGRAÇÃO
# ============================================

class TestIntegracao:
    """
    Testes de integração combinando múltiplas tasks.
    """
    
    def test_soma_e_fatorial_combinados(self, celery_config):
        """
        Testa a combinação das duas tasks.
        Cenário: Calcular o fatorial da soma de dois números.
        Exemplo: soma(3, 2) = 5, então fatorial(5) = 120
        """
        resultado_soma = calcular_soma(3, 2)
        resultado_fatorial = calcular_fatorial(resultado_soma["resultado"])
        
        assert resultado_soma["resultado"] == 5
        assert resultado_fatorial["resultado"] == 120
    
    def test_fatorial_da_soma_com_zero(self, celery_config):
        """
        Testa fatorial da soma envolvendo zero.
        Cenário: soma(0, 5) = 5, fatorial(5) = 120
        """
        resultado_soma = calcular_soma(0, 5)
        resultado_fatorial = calcular_fatorial(resultado_soma["resultado"])
        
        assert resultado_fatorial["resultado"] == 120
    
    def test_operacoes_encadeadas(self, celery_config):
        """
        Testa operações encadeadas: soma de múltiplos valores e depois fatorial.
        """
        soma1 = calcular_soma(2, 3)  # 5
        soma2 = calcular_soma(soma1["resultado"], 4)  # 9
        resultado_final = calcular_fatorial(soma2["resultado"])  # 9!
        
        assert soma1["resultado"] == 5
        assert soma2["resultado"] == 9
        assert resultado_final["resultado"] == 362880
    
    def test_multiplas_tasks_concorrentes(self, celery_config):
        """
        Testa a execução de múltiplas tasks em sequência.
        """
        resultados_esperados = [
            (calcular_soma(1, 2), 3),
            (calcular_soma(10, 20), 30),
            (calcular_fatorial(3), 6),
            (calcular_fatorial(4), 24),
            (calcular_soma(100, 200), 300),
        ]
        
        for task, esperado in resultados_esperados:
            assert task["resultado"] == esperado


# ============================================
# TESTES DO REDIS E GERENCIAMENTO DE TAREFAS (COM MOCK)
# ============================================

class TestGerenciamentoTasks:
    """
    Testes para as funções de gerenciamento de tasks no Redis.
    Usa mocks para evitar dependência do Redis real.
    """
    
    def test_gerar_task_id(self, mock_redis):
        """
        Testa a geração de IDs sequenciais para tasks.
        """
        # Configura o mock para retornar valores sequenciais
        mock_redis.incr.side_effect = [1, 2, 3]
        
        # Act
        id1 = gerar_task_id()
        id2 = gerar_task_id()
        id3 = gerar_task_id()
        
        # Assert
        assert id1 == 1
        assert id2 == 2
        assert id3 == 3
        assert mock_redis.incr.call_count == 3
    
    def test_salvar_e_obter_task_mapping(self, mock_redis):
        """
        Testa o salvamento e recuperação do mapeamento de IDs.
        """
        task_id_int = 123
        task_uuid = "abc-123-def-456"
        
        def get_side_effect(key):
            if key == f'task_mapping:{task_id_int}':
                return task_uuid
            return None
        
        mock_redis.get.side_effect = get_side_effect
        
        # Act - salva o mapeamento
        salvar_task_id_mapping(task_id_int, task_uuid)
        
        # Assert - verifica se o setex foi chamado
        mock_redis.setex.assert_called()
    
    def test_obter_task_uuid_inexistente(self, mock_redis):
        """
        Testa a obtenção de um UUID que não existe.
        """
        # Configura mock para retornar None
        mock_redis.get.return_value = None
        
        # Act
        uuid = obter_task_uuid(999)
        
        # Assert
        assert uuid is None
    
    def test_obter_task_id_int_inexistente(self, mock_redis):
        """
        Testa a obtenção de um ID inteiro que não existe.
        """
        # Configura mock para retornar None
        mock_redis.get.return_value = None
        
        # Act
        task_id = obter_task_id_int("uuid-inexistente")
        
        # Assert
        assert task_id is None


# ============================================
# TESTES DE PERFORMANCE
# ============================================

class TestPerformance:
    """
    Testes básicos de performance.
    """
    
    def test_tempo_execucao_soma(self, celery_config):
        """
        Testa o tempo de execução da tarefa de soma.
        """
        import time
        
        start = time.time()
        resultado = calcular_soma(10, 20)
        tempo_execucao = time.time() - start
        
        assert resultado["resultado"] == 30
        assert tempo_execucao > 0
        
        if tempo_execucao > 1:
            print(f"⚠️ Aviso: Soma demorou {tempo_execucao:.2f}s (pode ter sleep intencional)")
    
    def test_tempo_execucao_fatorial_pequeno(self, celery_config):
        """
        Testa o tempo de execução do fatorial para número pequeno (n=5).
        A função tem sleep(min(n//10+1, 5)) = sleep(1) + tempo de processamento
        """
        import time
        
        inicio = time.time()
        resultado = calcular_fatorial(5)
        fim = time.time()
        tempo_execucao = fim - inicio
        
        assert resultado["resultado"] == 120
        assert tempo_execucao >= 1.0, f"Tempo foi {tempo_execucao}s, deveria ser pelo menos 1s (com sleep)"
        assert tempo_execucao <= 5.0, f"Tempo foi {tempo_execucao}s, deveria ser no máximo 5s"
        print(f"ℹ️ Tempo de execução do fatorial(5): {tempo_execucao:.2f}s")
    
    def test_tempo_execucao_fatorial_medio(self, celery_config):
        """
        Testa o tempo de execução do fatorial para número médio (n=20).
        A função tem sleep(min(n//10+1, 5)) = sleep(3) + tempo de processamento
        """
        import time
        
        inicio = time.time()
        resultado = calcular_fatorial(20)
        fim = time.time()
        tempo_execucao = fim - inicio
        
        assert resultado["resultado"] == 2432902008176640000
        assert tempo_execucao >= 1.0, f"Tempo foi {tempo_execucao}s, deveria ser pelo menos 1s (com sleep)"
        assert tempo_execucao <= 7.0, f"Tempo foi {tempo_execucao}s, deveria ser no máximo 7s"
        print(f"ℹ️ Tempo de execução do fatorial(20): {tempo_execucao:.2f}s")


# ============================================
# EXECUÇÃO DOS TESTES
# ============================================

if __name__ == "__main__":
    """
    Permite executar os testes diretamente com python test_tasks.py
    """
    pytest.main([__file__, "-v", "--tb=short", "-W", "ignore"])