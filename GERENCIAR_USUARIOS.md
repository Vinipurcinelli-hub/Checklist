# Guia de Gerenciamento de Usuários

## Como Alterar Senha ou Criar Novos Usuários

### 1. Editar o arquivo `config.yaml`

O arquivo `config.yaml` contém todas as credenciais de usuários. Abra este arquivo e edite conforme necessário.

### 2. Estrutura do arquivo `config.yaml`

```yaml
credentials:
  usernames:
    admin:  # Este é o USERNAME (não o email!)
      email: planejamento.visa@suzantur.com.br
      name: Administrador
      password: $2b$12$qwsjDSUL8bo7lhg927jYtuGEht.inzukf.TBSeDLmi47K3cvpMFaq
    novo_usuario:  # Adicione novos usuários aqui
      email: usuario@exemplo.com
      name: Nome do Usuário
      password: HASH_AQUI  # Veja como gerar abaixo
cookie:
  expiry_days: 30
  key: checklist_vistoria_key_12345
  name: checklist_vistoria_cookie
preauthorized:
  emails:
    - planejamento.visa@suzantur.com.br
```

### 3. Gerar Hash de Senha

**IMPORTANTE**: As senhas devem estar em formato hash (bcrypt), NÃO em texto plano!

#### Opção 1: Usando o script fornecido

```bash
python gerar_hash_senha.py
```

O script irá gerar o hash da senha `Pl@n3j@m3nt0`. Para gerar hash de outra senha, edite o script `gerar_hash_senha.py` e altere a variável `password`.

#### Opção 2: Usando Python diretamente

```python
import bcrypt

senha = 'sua_senha_aqui'
hashed = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(hashed)
```

#### Opção 3: Usando streamlit-authenticator (se instalado)

```python
import streamlit_authenticator as stauth

hasher = stauth.Hasher()
hashed_passwords = hasher.generate(['sua_senha_aqui'])
print(hashed_passwords[0])
```

### 4. Adicionar Novo Usuário

1. Abra o arquivo `config.yaml`
2. Adicione uma nova entrada em `credentials.usernames`:

```yaml
credentials:
  usernames:
    admin:
      email: planejamento.visa@suzantur.com.br
      name: Administrador
      password: $2b$12$qwsjDSUL8bo7lhg927jYtuGEht.inzukf.TBSeDLmi47K3cvpMFaq
    novo_usuario:  # ← NOVO USUÁRIO
      email: novo.usuario@exemplo.com
      name: Novo Usuário
      password: $2b$12$HASH_GERADO_AQUI  # ← Use o hash gerado
```

3. Gere o hash da senha usando um dos métodos acima
4. Substitua `HASH_GERADO_AQUI` pelo hash gerado
5. Salve o arquivo

### 5. Alterar Senha de Usuário Existente

1. Gere um novo hash para a nova senha
2. Abra o arquivo `config.yaml`
3. Localize o usuário em `credentials.usernames`
4. Substitua o valor do campo `password` pelo novo hash
5. Salve o arquivo

**Exemplo:**
```yaml
admin:
  email: planejamento.visa@suzantur.com.br
  name: Administrador
  password: $2b$12$NOVO_HASH_AQUI  # ← Substitua pelo novo hash
```

### 6. Remover Usuário

Simplesmente remova a entrada do usuário do arquivo `config.yaml`:

```yaml
credentials:
  usernames:
    # admin:  ← Comente ou remova esta seção
    #   email: ...
    #   name: ...
    #   password: ...
    outro_usuario:
      email: outro@exemplo.com
      name: Outro Usuário
      password: $2b$12$...
```

### 7. Aplicar Mudanças

Após editar o `config.yaml`:

1. **Localmente**: Reinicie o Streamlit (`Ctrl+C` e depois `streamlit run app.py`)
2. **No Streamlit Cloud**: Faça commit e push das alterações para o GitHub. O deploy será automático.

### 8. Importante - Segurança

⚠️ **NUNCA** coloque senhas em texto plano no `config.yaml`!

- ✅ Use sempre hash bcrypt
- ✅ Mantenha o `config.yaml` privado (não compartilhe)
- ✅ Considere usar Streamlit Secrets para maior segurança em produção
- ✅ Use senhas fortes

### 9. Usar Streamlit Secrets (Recomendado para Produção)

Para maior segurança, você pode mover as credenciais para Streamlit Secrets:

1. No Streamlit Cloud, vá em "Settings" → "Secrets"
2. Cole o conteúdo do `config.yaml` lá
3. Modifique o código para ler de `st.secrets` em vez de arquivo

**Exemplo de código:**
```python
# Em vez de:
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Use:
config = st.secrets
```

### 10. Testar Login

Após fazer alterações:

1. Use o **username** (não o email) para fazer login
2. Use a senha em texto plano (não o hash)
3. Exemplo: username = `admin`, senha = `Pl@n3j@m3nt0`
