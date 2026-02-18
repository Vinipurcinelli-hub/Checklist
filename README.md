# Dashboard Gerencial - Checklist de Vistoria

Aplicação Streamlit para visualização e geração de relatórios em PDF de vistorias de veículos.

## Funcionalidades

- **Autenticação**: Sistema de login para acesso restrito
- **Dashboard Gerencial**: Métricas gerais sobre as vistorias realizadas
- **Gerenciador de Registros**: Lista dos últimos registros ordenados do mais novo para o mais antigo
- **Geração de PDF**: Relatórios em PDF responsivos com não conformidades organizadas por área
- **Impressão Direta**: Botão para imprimir relatórios diretamente

## Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure a autenticação:
   - O arquivo `config.yaml` já está configurado com as credenciais
   - Para gerar hash de nova senha, execute: `python gerar_hash_senha.py`
   - Copie o hash gerado para o campo `password` no `config.yaml`

## Fonte dos dados (Google Planilhas ou arquivo local)

O app pode usar dados em **tempo (quase) real** do **Google Planilhas** (planilha vinculada ao formulário) ou o arquivo local `base_de_dados.xlsx`.

- **Sem configurar nada:** o app usa apenas `base_de_dados.xlsx` (comportamento clássico).
- **Com Google configurado:** o app lê a planilha primeiro; se a API falhar, usa automaticamente o xlsx como fallback.

### Configurar Google Planilhas (opcional)

Resumo:
1. **Google Cloud:** crie um projeto, ative a **Google Sheets API** e crie uma **conta de serviço** (Service Account). Baixe o JSON de credenciais.
2. **Planilha:** compartilhe a planilha (que recebe as respostas do Forms) com o e-mail da conta de serviço (ex.: `xxx@projeto.iam.gserviceaccount.com`) como **Visualizador**.
3. **ID da planilha:** na URL da planilha, copie o ID: `https://docs.google.com/spreadsheets/d/<ID_DA_PLANILHA>/edit`.

**Local (desenvolvimento):**
- Variável de ambiente `GOOGLE_SHEETS_ID` = ID da planilha.
- Variável de ambiente `GOOGLE_APPLICATION_CREDENTIALS` = caminho para o arquivo JSON da conta de serviço (ex.: `C:\caminho\credenciais.json`).

**Streamlit Cloud (produção):** em Settings → Secrets, adicione:
```toml
GOOGLE_SHEETS_ID = "id_da_sua_planilha"
GOOGLE_CREDENTIALS = '''{"type": "service_account", "project_id": "...", ...}'''
```
Cole o conteúdo completo do JSON da conta de serviço em `GOOGLE_CREDENTIALS` (como texto ou objeto).

Na sidebar do app aparece **"Dados: Google Planilhas"** ou **"Dados: arquivo local"** indicando qual fonte está em uso.

## Uso Local

1. Certifique-se de que os arquivos necessários estão no diretório:
   - `base_de_dados.xlsx` (obrigatório se não usar Google; recomendado como fallback)
   - `formatacao_colunas.xlsx`
   - `config.yaml`

2. Execute a aplicação:
```bash
streamlit run app.py
```

3. Faça login com as credenciais configuradas no `config.yaml`

4. A aplicação abrirá no navegador. Você verá:
   - Dashboard com métricas gerais no topo
   - Lista de registros de vistoria abaixo
   - Botões "PDF" e "Imprimir" em cada registro

## Deploy no Streamlit Cloud

Consulte o arquivo `DEPLOY.md` para instruções detalhadas de deploy.

### Resumo rápido:
1. Crie um repositório no GitHub
2. Faça upload de todos os arquivos
3. Acesse [share.streamlit.io](https://share.streamlit.io)
4. Conecte seu repositório e faça deploy

### Atualizar o app para usar a nova lógica (upload manual no GitHub)

Se você não usa Git e envia os arquivos manualmente para o GitHub, para o app no Streamlit passar a usar a planilha do Google como base de dados:

1. **No site do GitHub**, abra o repositório do projeto e envie/substitua pela versão atual da sua pasta **todos** os arquivos do projeto, incluindo em especial:
   - **`app.py`** (contém a lógica de leitura do Google Planilhas e fallback para xlsx)
   - **`requirements.txt`** (contém as dependências `gspread` e `google-auth`)
   - **`README.md`**, **`DEPLOY.md`** e **`.gitignore`** (documentação e regras do repositório)

2. **Não envie** o arquivo `google_credentials.json` para o repositório (as credenciais ficam só nos Secrets do Streamlit).

3. No **Streamlit Cloud**, abra seu app → **Settings** (ou menu do app) → use **"Reboot app"** ou **"Redeploy"** (se existir) para o app recarregar o código do repositório. Se o Streamlit redeployar sozinho ao detectar alterações no GitHub, aguarde 1–2 minutos.

4. Confirme que os **Secrets** estão configurados: `GOOGLE_SHEETS_ID` (ID da planilha) e `GOOGLE_CREDENTIALS` (conteúdo do JSON da conta de serviço). E que a **planilha** está compartilhada com o e-mail da conta de serviço como Visualizador.

5. Abra o app; na sidebar deve aparecer **"Dados: Google Planilhas"** quando estiver tudo certo.

## Estrutura do PDF

O PDF gerado contém:
- Informações do veículo (Prefixo, Cidade, Vistoriador, Data)
- Não conformidades organizadas por área:
  - Externa
  - Cabine
  - Salão
  - Sanitário
  - Geladeiras
  - Geral (observações gerais, se houver)

Apenas as áreas com não conformidades são exibidas no PDF, tornando-o responsivo e adaptável ao conteúdo.

## Credenciais Padrão

- **Usuário**: admin
- **Senha**: Pl@n3j@m3nt0
- **Email**: planejamento.visa@suzantur.com.br

⚠️ **IMPORTANTE**: Altere as credenciais padrão antes de fazer deploy em produção!

## Requisitos

- Python 3.8+
- Streamlit
- Pandas
- OpenPyXL
- ReportLab
- Streamlit Authenticator
- PyYAML
- bcrypt
- gspread e google-auth (para integração opcional com Google Planilhas)