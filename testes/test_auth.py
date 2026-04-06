"""
Testes para o sistema de autenticação da API de Livros
"""

from fastapi.testclient import TestClient
import sys
import os

# Adiciona o diretório atual ao path para importar o main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app

# Cria o cliente de teste
client = TestClient(app)

# Credenciais corretas (fixas na aplicação)
CREDENCIAIS_CORRETAS = {
    "email": "admin@exemplo.com",
    "senha": "123456"
}

CREDENCIAIS_INCORRETAS = [
    {"email": "admin@exemplo.com", "senha": "senha_errada"},
    {"email": "usuario@exemplo.com", "senha": "123456"},
    {"email": "errado@exemplo.com", "senha": "senha_incorreta"},
    {"email": "", "senha": "123456"},
    {"email": "admin@exemplo.com", "senha": ""},
]


# ==================== TESTE DE SUCESSO ====================
def test_login_sucesso():
    """
    Testa o login com credenciais corretas.
    Deve retornar status 200 e um token.
    """
    print("\n🔐 Testando login com credenciais corretas...")
    
    response = client.post("/auth/login", json=CREDENCIAIS_CORRETAS)
    
    # Verifica status HTTP
    assert response.status_code == 200, f"Esperado 200, recebido {response.status_code}"
    
    # Verifica estrutura da resposta
    data = response.json()
    assert "sucesso" in data
    assert "mensagem" in data
    assert "token" in data
    
    # Verifica conteúdo
    assert data["sucesso"] == True
    assert data["mensagem"] == "Login realizado com sucesso"
    assert data["token"] is not None
    assert len(data["token"]) > 0
    
    print(f"✅ Teste de sucesso passou! Token recebido: {data['token'][:20]}...")


# ==================== TESTES DE ERRO ====================
def test_login_senha_incorreta():
    """
    Testa login com senha incorreta.
    Deve retornar status 401.
    """
    print("\n🔐 Testando login com senha incorreta...")
    
    response = client.post("/auth/login", json={
        "email": "admin@exemplo.com",
        "senha": "senha_errada_123"
    })
    
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "inválidas" in response.json()["detail"].lower()
    
    print("✅ Teste de senha incorreta passou!")


def test_login_email_incorreto():
    """
    Testa login com email incorreto.
    Deve retornar status 401.
    """
    print("\n🔐 Testando login com email incorreto...")
    
    response = client.post("/auth/login", json={
        "email": "usuario_inexistente@exemplo.com",
        "senha": "123456"
    })
    
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "inválidas" in response.json()["detail"].lower()
    
    print("✅ Teste de email incorreto passou!")


def test_login_credenciais_completamente_erradas():
    """
    Testa login com email e senha incorretos.
    Deve retornar status 401.
    """
    print("\n🔐 Testando login com credenciais completamente erradas...")
    
    response = client.post("/auth/login", json={
        "email": "hacker@exemplo.com",
        "senha": "hack123"
    })
    
    assert response.status_code == 401
    assert "detail" in response.json()
    
    print("✅ Teste de credenciais completamente erradas passou!")


# ==================== TESTES PARAMETRIZADOS ====================
import pytest

@pytest.mark.parametrize("email,senha,descricao", [
    ("admin@exemplo.com", "senha_qualquer", "senha incorreta"),
    ("qualquer@email.com", "123456", "email incorreto"),
    ("", "123456", "email vazio"),
    ("admin@exemplo.com", "", "senha vazia"),
    ("", "", "ambos vazios"),
])
def test_login_multiplas_credenciais_invalidas(email, senha, descricao):
    """
    Testa múltiplas combinações de credenciais inválidas usando parametrização.
    """
    print(f"\n🔐 Testando {descricao}: email='{email}', senha='{senha}'")
    
    response = client.post("/auth/login", json={
        "email": email,
        "senha": senha
    })
    
    assert response.status_code == 401
    assert "detail" in response.json()
    
    print(f"✅ Teste de {descricao} passou!")


# ==================== TESTE DE CAMPOS OBRIGATÓRIOS ====================
def test_login_sem_corpo_json():
    """
    Testa requisição sem corpo JSON.
    Deve retornar status 422 (Unprocessable Entity).
    """
    print("\n🔐 Testando requisição sem corpo JSON...")
    
    response = client.post("/auth/login")
    
    assert response.status_code == 422
    print("✅ Teste sem corpo JSON passou!")


def test_login_campos_faltando():
    """
    Testa requisição faltando campos obrigatórios.
    Deve retornar status 422.
    """
    print("\n🔐 Testando requisição com campos faltando...")
    
    # Apenas email
    response1 = client.post("/auth/login", json={"email": "admin@exemplo.com"})
    assert response1.status_code == 422
    
    # Apenas senha
    response2 = client.post("/auth/login", json={"senha": "123456"})
    assert response2.status_code == 422
    
    print("✅ Teste de campos faltando passou!")


# ==================== TESTE DE TIPO DE DADOS INCORRETO ====================
def test_login_tipos_incorretos():
    """
    Testa envio de tipos de dados incorretos.
    Deve retornar status 422.
    """
    print("\n🔐 Testando tipos de dados incorretos...")
    
    # Email como número
    response = client.post("/auth/login", json={
        "email": 12345,
        "senha": "123456"
    })
    assert response.status_code == 422
    
    print("✅ Teste de tipos incorretos passou!")


# ==================== EXECUÇÃO PRINCIPAL ====================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 EXECUTANDO TESTES DE AUTENTICAÇÃO")
    print("="*60)
    
    # Executa todos os testes
    test_login_sucesso()
    test_login_senha_incorreta()
    test_login_email_incorreto()
    test_login_credenciais_completamente_erradas()
    test_login_multiplas_credenciais_invalidas()
    test_login_sem_corpo_json()
    test_login_campos_faltando()
    test_login_tipos_incorretos()
    
    print("\n" + "="*60)
    print("✅ TODOS OS TESTES FORAM EXECUTADOS")
    print("="*60)