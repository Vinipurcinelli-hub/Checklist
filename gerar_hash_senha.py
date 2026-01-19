"""
Script para gerar hash de senha para o config.yaml
Execute: python gerar_hash_senha.py
"""
try:
    import streamlit_authenticator as stauth
    password = 'Pl@n3j@m3nt0'
    
    # A API do streamlit-authenticator mudou
    # Agora usa Hasher().generate() com uma lista de senhas
    hasher = stauth.Hasher()
    hashed_passwords = hasher.generate([password])
    
    print(f"\nHash gerado para a senha '{password}':")
    print(f"{hashed_passwords[0]}")
    print(f"\nCopie este hash para o campo 'password' no config.yaml")
    print(f"\nExemplo de uso no config.yaml:")
    print(f"  password: {hashed_passwords[0]}")
except ImportError:
    print("Instale primeiro: pip install streamlit-authenticator")
    print("Depois execute este script novamente.")
except Exception as e:
    print(f"Erro: {e}")
    print("\nTentando método alternativo com bcrypt...")
    try:
        import bcrypt
        password = 'Pl@n3j@m3nt0'
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"\nHash gerado (bcrypt) para a senha '{password}':")
        print(f"{hashed}")
        print(f"\nCopie este hash para o campo 'password' no config.yaml")
    except ImportError:
        print("Instale: pip install bcrypt")
