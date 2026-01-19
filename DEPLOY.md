# Guia de Deploy no Streamlit Cloud

## Pré-requisitos

1. Conta no GitHub
2. Conta no Streamlit Cloud (gratuita)
3. Repositório GitHub com o código

## Passos para Deploy

### 1. Preparar o Repositório GitHub

1. Crie um repositório no GitHub
2. Faça upload dos seguintes arquivos:
   - `app.py`
   - `requirements.txt`
   - `config.yaml`
   - `.streamlit/config.toml`
   - `base_de_dados.xlsx`
   - `formatacao_colunas.xlsx`
   - `.gitignore`

### 2. Deploy no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Faça login com sua conta GitHub
3. Clique em "New app"
4. Configure:
   - **Repository**: Seu repositório GitHub
   - **Branch**: `main` (ou `master`)
   - **Main file path**: `app.py`
5. Clique em "Deploy!"

### 3. Configurar Secrets (Opcional - para maior segurança)

Se preferir não commitar o `config.yaml` com senhas no repositório:

1. No Streamlit Cloud, vá em "Settings" → "Secrets"
2. Adicione o conteúdo do `config.yaml` como secrets
3. Modifique o código para ler de `st.secrets` em vez de arquivo

### 4. Acessar a Aplicação

Após o deploy, você receberá uma URL como:
`https://seu-app.streamlit.app`

## Segurança

⚠️ **IMPORTANTE**: 
- O arquivo `config.yaml` contém senhas. Considere usar Streamlit Secrets para maior segurança
- Mantenha o `.gitignore` atualizado para não commitar informações sensíveis
- A senha está hasheada com bcrypt, mas ainda assim é recomendado usar secrets

## Adicionar Novos Usuários

Para adicionar novos usuários, edite o arquivo `config.yaml`:

```yaml
credentials:
  usernames:
    admin:
      email: planejamento.visa@suzantur.com.br
      name: Administrador
      password: $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW
    novo_usuario:
      email: usuario@exemplo.com
      name: Novo Usuário
      password: $2b$12$hash_aqui  # Use stauth.Hasher(['senha']).generate() para gerar
```

Para gerar hash de senha:
```python
import streamlit_authenticator as stauth
hashed_passwords = stauth.Hasher(['sua_senha']).generate()
print(hashed_passwords[0])
```
