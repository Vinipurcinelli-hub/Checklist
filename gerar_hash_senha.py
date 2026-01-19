"""
Script para gerar hash de senha para o config.yaml

Uso:
    python gerar_hash_senha.py
    
Para gerar hash de outra senha, edite a variável 'password' abaixo.
"""
import sys
import os

# Configurar encoding para UTF-8 no Windows
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')

# EDITAR AQUI: Coloque a senha que deseja gerar o hash
password = 'Cl@udin3iIt@p3mirim'

print(f"Gerando hash para a senha: '{password}'")
print("-" * 60)

# Usar bcrypt diretamente (mais confiável)
try:
    import bcrypt
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    print(f"\nHash gerado com sucesso!")
    print(f"\nHash:")
    print(f"{hashed}")
    print(f"\nCopie este hash para o campo 'password' no config.yaml")
    print(f"\nExemplo de uso no config.yaml:")
    print(f"  password: {hashed}")
except ImportError:
    print("Erro: bcrypt nao esta instalado.")
    print("Instale com: pip install bcrypt")
    sys.exit(1)
except Exception as e:
    print(f"Erro ao gerar hash: {e}")
    sys.exit(1)
