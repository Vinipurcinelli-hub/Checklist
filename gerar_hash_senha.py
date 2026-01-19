"""
Script para gerar hash de senha para o config.yaml

Uso:
    python gerar_hash_senha.py
    
Para gerar hash de outra senha, edite a variável 'password' abaixo.
"""
import sys

# EDITAR AQUI: Coloque a senha que deseja gerar o hash
password = 'Pl@n3j@m3nt0'

print(f"Gerando hash para a senha: '{password}'")
print("-" * 60)

try:
    import streamlit_authenticator as stauth
    
    # A API do streamlit-authenticator mudou
    # Agora usa Hasher().generate() com uma lista de senhas
    hasher = stauth.Hasher()
    hashed_passwords = hasher.generate([password])
    
    print(f"\n✅ Hash gerado com sucesso!")
    print(f"\nHash:")
    print(f"{hashed_passwords[0]}")
    print(f"\n📋 Copie este hash para o campo 'password' no config.yaml")
    print(f"\nExemplo de uso no config.yaml:")
    print(f"  password: {hashed_passwords[0]}")
    
except ImportError:
    print("⚠️ streamlit-authenticator não encontrado.")
    print("Tentando método alternativo com bcrypt...")
    try:
        import bcrypt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"\n✅ Hash gerado (bcrypt) com sucesso!")
        print(f"\nHash:")
        print(f"{hashed}")
        print(f"\n📋 Copie este hash para o campo 'password' no config.yaml")
    except ImportError:
        print("❌ Erro: bcrypt não está instalado.")
        print("Instale com: pip install bcrypt")
        sys.exit(1)
except Exception as e:
    print(f"❌ Erro ao gerar hash com streamlit-authenticator: {e}")
    print("\nTentando método alternativo com bcrypt...")
    try:
        import bcrypt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"\n✅ Hash gerado (bcrypt) com sucesso!")
        print(f"\nHash:")
        print(f"{hashed}")
        print(f"\n📋 Copie este hash para o campo 'password' no config.yaml")
    except ImportError:
        print("❌ Erro: bcrypt não está instalado.")
        print("Instale com: pip install bcrypt")
        sys.exit(1)
