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

## Uso Local

1. Certifique-se de que os arquivos necessários estão no diretório:
   - `base_de_dados.xlsx`
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