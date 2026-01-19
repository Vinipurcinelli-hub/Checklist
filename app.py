import streamlit as st
import pandas as pd
from datetime import datetime
import io
import base64
import yaml
from yaml.loader import SafeLoader
from streamlit.components.v1 import html
import streamlit_authenticator as stauth
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import re

# Configuração da página
st.set_page_config(
    page_title="Dashboard Gerencial - Checklist Vistoria",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Carregar configuração de autenticação
@st.cache_data
def load_auth_config():
    """Carrega configuração de autenticação"""
    try:
        with open('config.yaml') as file:
            config = yaml.load(file, Loader=SafeLoader)
        return config
    except FileNotFoundError:
        st.error("Arquivo config.yaml não encontrado!")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar configuração: {e}")
        return None

# Verificar autenticação
def check_authentication():
    """Verifica se o usuário está autenticado"""
    config = load_auth_config()
    if config is None:
        return False, None
    
    # Versão mais recente do streamlit-authenticator não aceita preauthorized no construtor
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    
    # Verificar primeiro se já está autenticado no session_state
    # Isso evita chamar login() desnecessariamente
    if 'authentication_status' in st.session_state:
        auth_status = st.session_state.get('authentication_status')
        if auth_status is True:
            # Usuário já autenticado - não precisa chamar login() novamente
            auth_name = st.session_state.get('name', 'Usuário')
            try:
                authenticator.logout(location='sidebar')
            except:
                pass
            st.sidebar.write(f'Bem-vindo, *{auth_name}*')
            return True, authenticator
        elif auth_status is False:
            # Login falhou anteriormente
            st.error('Usuário/senha incorretos')
            st.info('💡 Use o **username** (não o email). Exemplo: username = "admin"')
            return False, None
    
    # Se não estiver autenticado, chamar o método login()
    name = None
    authentication_status = None
    username = None
    
    try:
        # Tentar com parâmetro posicional 'main' (versão mais comum)
        result = authenticator.login('main')
        if result is not None and isinstance(result, (tuple, list)) and len(result) >= 3:
            name, authentication_status, username = result[0], result[1], result[2]
        elif result is not None:
            # Se retornar algo diferente, tentar acessar como atributos
            if hasattr(result, 'name'):
                name = result.name
            if hasattr(result, 'authentication_status'):
                authentication_status = result.authentication_status
            if hasattr(result, 'username'):
                username = result.username
    except TypeError as e1:
        try:
            # Tentar sem parâmetros (algumas versões)
            result = authenticator.login()
            if result is not None and isinstance(result, (tuple, list)) and len(result) >= 3:
                name, authentication_status, username = result[0], result[1], result[2]
        except Exception as e2:
            st.error(f"Erro na autenticação: {str(e2)}")
            return False, None
    except Exception as e:
        st.error(f"Erro ao chamar login(): {str(e)}")
        return False, None
    
    # IMPORTANTE: O authenticator armazena o status no session_state após login
    # Verificar o session_state APÓS chamar login() (ele atualiza lá)
    if 'authentication_status' in st.session_state:
        auth_status = st.session_state.get('authentication_status')
        if auth_status is True:
            # Usuário autenticado!
            auth_name = st.session_state.get('name', name or 'Usuário')
            try:
                authenticator.logout(location='sidebar')
            except:
                pass
            st.sidebar.write(f'Bem-vindo, *{auth_name}*')
            return True, authenticator
        elif auth_status is False:
            st.error('Usuário/senha incorretos')
            return False, None
    
    # Se não estiver no session_state, verificar o retorno direto do método
    if authentication_status == True:
        # Usuário autenticado via retorno do método - forçar rerun para atualizar session_state
        try:
            authenticator.logout(location='sidebar')
        except:
            pass
        st.sidebar.write(f'Bem-vindo, *{name or "Usuário"}*')
        # Forçar rerun para garantir que o session_state seja atualizado
        st.rerun()
        return True, authenticator
    elif authentication_status == False:
        st.error('Usuário/senha incorretos')
        return False, None
    
    # Se authentication_status é None, mostrar formulário de login
    if authentication_status is None:
        # Não mostrar informações de login na tela por segurança
        return False, None
    
    # Fallback
    return False, None

# Carregar mapeamento de colunas
@st.cache_data
def load_column_mapping():
    """Carrega o mapeamento de colunas originais para tratadas e áreas"""
    try:
        df_map = pd.read_excel('formatacao_colunas.xlsx', engine='openpyxl')
        
        # Criar dicionário de mapeamento: coluna_original -> (coluna_tratada, area)
        mapping = {}
        for idx, row in df_map.iterrows():
            col_original = str(row.iloc[0]).strip()
            col_tratada = str(row.iloc[1]).strip()
            area = str(row.iloc[2]).strip()
            
            # Ignorar se área for NaN ou vazia, ou se for IDENTIFICAÇÃO/GERAL
            if pd.notna(row.iloc[2]) and area not in ['nan', 'IDENTIFICAÇÃO', 'GERAL', '']:
                mapping[col_original] = {
                    'nome_tratado': col_tratada if col_tratada != 'nan' else col_original,
                    'area': area
                }
        
        return mapping
    except Exception as e:
        st.warning(f"Erro ao carregar mapeamento de colunas: {e}")
        return {}

# Carregar dados
@st.cache_data
def load_data():
    try:
        # Tentar diferentes encodings
        try:
            df = pd.read_excel('base_de_dados.xlsx', engine='openpyxl')
        except:
            df = pd.read_excel('base_de_dados.xlsx')
        
        # Converter coluna de data/hora se necessário
        for col in df.columns:
            if 'carimbo' in col.lower() and 'data' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
                break
        
        # Ordenar por data/hora mais recente primeiro
        for col in df.columns:
            if 'carimbo' in col.lower() and 'data' in col.lower():
                df = df.sort_values(col, ascending=False).reset_index(drop=True)
                break
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Função para obter informações da coluna do mapeamento
def get_column_info(col_name, column_mapping):
    """Retorna nome tratado e área da coluna baseado no mapeamento"""
    if not column_mapping:
        return None, None
    
    # Tentar match exato primeiro
    if col_name in column_mapping:
        return column_mapping[col_name]['nome_tratado'], column_mapping[col_name]['area']
    
    # Tentar match case-insensitive
    col_name_lower = col_name.lower().strip()
    for orig_col, info in column_mapping.items():
        if orig_col.lower().strip() == col_name_lower:
            return info['nome_tratado'], info['area']
    
    return None, None

# Função para identificar área da coluna (fallback)
def get_area_from_column(col_name):
    col_upper = col_name.upper()
    col_lower = col_name.lower()
    
    # Verificar por ordem de especificidade (mais específico primeiro)
    
    # Geladeiras
    if 'GELADEIRA' in col_upper:
        return 'Geladeiras'
    
    # Sanitário
    if 'SANITÁRIO' in col_upper or 'SANITARIO' in col_upper:
        return 'Sanitário'
    
    # Salão - verificar padrões específicos
    if 'SALÃO' in col_upper or 'SALAO' in col_upper:
        return 'Salão'
    # Poltronas geralmente são do salão
    if 'POLTRONAS' in col_upper or col_upper.startswith('POLTRONAS'):
        return 'Salão'
    # Verificar se contém [POLTRONAS]
    if '[POLTRONAS]' in col_upper:
        return 'Salão'
    
    # Cabine - verificar padrões específicos
    if col_upper.startswith('CABINE') or '[CABINE' in col_upper:
        return 'Cabine'
    if 'CABINE' in col_upper and ('MOTORISTA' in col_upper or 'DO MOTORISTA' in col_upper):
        return 'Cabine'
    
    # Externa - verificar padrões específicos
    if 'AVALIAÇÃO EXTERNA' in col_upper or 'AVALIACAO EXTERNA' in col_upper:
        return 'Externa'
    if 'EXTERNA' in col_upper or 'EXTERNO' in col_upper:
        return 'Externa'
    
    # Verificar por palavras-chave comuns de área externa
    if any(x in col_lower for x in ['avaria', 'higienização', 'estado', 'pintura', 
                                     'adesivo', 'extintor', 'bagageiro', 
                                     'placa', 'pneu', 'retrovisor', 'vidro', 'carroceria',
                                     'porta de entrada']):
        # Verificar se não é de outra área
        if 'CABINE' not in col_upper and 'SANITÁRIO' not in col_upper and 'SANITARIO' not in col_upper:
            if 'POLTRONAS' not in col_upper and 'SALÃO' not in col_upper and 'SALAO' not in col_upper:
                if 'GELADEIRA' not in col_upper:
                    return 'Externa'
    
    return None

# Função para verificar se há não conformidade
def has_non_conformity(value):
    if pd.isna(value):
        return False
    value_str = str(value).upper().strip()
    # Verifica se é "NÃO CONFORME" ou se tem algum valor preenchido (indicando não conformidade)
    if 'NÃO CONFORME' in value_str or 'NAO CONFORME' in value_str:
        return True
    # Se não for NaN e tiver algum conteúdo, considera não conformidade
    if value_str and value_str not in ['NAN', 'NONE', '']:
        return True
    return False

# Função para formatar o nome do item
def format_item_name(col_name):
    # Remove prefixos comuns
    name = col_name
    prefixes = ['Campo para observações pontuais sobre', 'Campo para fotografias pontuais sobre']
    for prefix in prefixes:
        if name.startswith(prefix):
            return name.replace(prefix, '').strip()
    return name

# Função para formatar valores numéricos e datas corretamente
def format_value(value, column_name=None):
    """Formata valores removendo decimais desnecessários e formatando datas"""
    if pd.isna(value):
        return "NÃO CONFORME"
    
    # Verificar se é campo de extintor (validade)
    is_extintor_date = False
    if column_name:
        col_lower = str(column_name).lower()
        if 'extintor' in col_lower and ('validade' in col_lower or 'data' in col_lower):
            is_extintor_date = True
    
    # Tentar detectar e formatar datas primeiro
    try:
        # Se for um Timestamp do pandas
        if isinstance(value, pd.Timestamp):
            if is_extintor_date:
                # Formato MMM-AAAA para extintores
                meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                        'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                return f"{meses[value.month - 1]}-{value.year}"
            return value.strftime('%d-%m-%Y')
        
        # Se for datetime
        if isinstance(value, datetime):
            if is_extintor_date:
                # Formato MMM-AAAA para extintores
                meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                        'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                return f"{meses[value.month - 1]}-{value.year}"
            return value.strftime('%d-%m-%Y')
        
        # Se for string, tentar detectar formato de data
        value_str = str(value).strip()
        
        # Padrões comuns de data: YYYY-MM-DD HH:MM:SS ou YYYY-MM-DD
        import re
        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})\s+\d{2}:\d{2}:\d{2}',  # 2026-12-01 00:00:00
            r'(\d{4})-(\d{2})-(\d{2})',  # 2026-12-01
            r'(\d{2})/(\d{2})/(\d{4})',  # 01/12/2026
            r'(\d{2})-(\d{2})-(\d{4})',  # 01-12-2026
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, value_str)
            if match:
                if len(match.groups()) == 3:
                    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                            'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                    
                    if pattern.startswith(r'(\d{4})'):  # Formato YYYY-MM-DD
                        year, month, day = match.groups()
                        if is_extintor_date:
                            return f"{meses[int(month) - 1]}-{year}"
                        return f"{day}-{month}-{year}"
                    else:  # Formato DD/MM/YYYY ou DD-MM-YYYY
                        day, month, year = match.groups()
                        if is_extintor_date:
                            return f"{meses[int(month) - 1]}-{year}"
                        return f"{day}-{month}-{year}"
        
        # Tentar converter string para datetime
        try:
            date_value = pd.to_datetime(value_str, errors='raise')
            if is_extintor_date:
                # Formato MMM-AAAA para extintores
                meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                        'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                return f"{meses[date_value.month - 1]}-{date_value.year}"
            return date_value.strftime('%d-%m-%Y')
        except (ValueError, TypeError):
            pass  # Não é uma data, continuar com formatação numérica
    except:
        pass  # Continuar com formatação numérica
    
    # Tentar converter para número
    try:
        # Se for um número float que é equivalente a um inteiro
        if isinstance(value, (int, float)):
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            return str(value)
        
        # Se for string, tentar converter
        value_str = str(value).strip()
        
        # Primeiro, substituir números como "48.0" por "48" (mas manter "48.5" como está)
        import re
        pattern = r'\b\d+\.0\b'
        value_str = re.sub(pattern, lambda m: str(int(float(m.group()))), value_str)
        
        # Tentar converter para float
        try:
            num_value = float(value_str)
            if num_value.is_integer():
                return str(int(num_value))
            return value_str
        except ValueError:
            # Se não for número, retornar string já formatada (sem .0)
            return value_str
    except:
        # Se houver qualquer erro, retornar como string
        return str(value)

# Função para renderizar botões de PDF e Impressão
def _render_buttons(df, row_data, idx, column_mapping, is_mobile=False):
    """Renderiza botões de PDF e Impressão (reutilizável para desktop e mobile)"""
    try:
        pdf_buffer = generate_pdf(df, row_data['Índice'], column_mapping)
        prefixo = row_data['Prefixo'].replace('/', '_').replace('\\', '_').replace('-', '_')
        data_str = row_data['Data'].replace('-', '_').replace(' ', '_')
        filename = f"Relatorio_Vistoria_{prefixo}_{data_str}.pdf"
        
        # Converter PDF para base64 para impressão
        pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
        
        # Criar duas subcolunas para os botões
        btn_col1, btn_col2 = st.columns(2)
        
        # Usar sufixo para diferenciar chaves entre desktop e mobile
        suffix = "_mobile" if is_mobile else "_desktop"
        
        with btn_col1:
            st.download_button(
                label="📄 PDF",
                data=pdf_buffer,
                file_name=filename,
                mime="application/pdf",
                key=f"download_{idx}{suffix}",
                use_container_width=True
            )
        
        with btn_col2:
            # Botão de impressão usando JavaScript
            print_key = f"print_btn_{idx}{suffix}"
            if print_key not in st.session_state:
                st.session_state[print_key] = False
            
            if st.button("🖨️ Imprimir", key=f"print_{idx}{suffix}", use_container_width=True):
                st.session_state[print_key] = True
            
            # Executar JavaScript quando o botão for clicado
            if st.session_state[print_key]:
                # Criar função JavaScript para imprimir
                print_js = f"""
                <script>
                (function() {{
                    var pdfBase64 = '{pdf_base64}';
                    var pdfBlob = atob(pdfBase64);
                    var pdfArray = new Uint8Array(pdfBlob.length);
                    for (var i = 0; i < pdfBlob.length; i++) {{
                        pdfArray[i] = pdfBlob.charCodeAt(i);
                    }}
                    var blob = new Blob([pdfArray], {{type: 'application/pdf'}});
                    var url = URL.createObjectURL(blob);
                    var printWindow = window.open(url, '_blank');
                    if (printWindow) {{
                        printWindow.onload = function() {{
                            setTimeout(function() {{
                                printWindow.print();
                            }}, 500);
                        }};
                    }}
                }})();
                </script>
                """
                html(print_js, height=0)
                st.session_state[print_key] = False
                
    except Exception as e:
        st.error(f"Erro: {str(e)[:30]}")

# Função para gerar PDF
def generate_pdf(df, index, column_mapping=None):
    buffer = io.BytesIO()
    # Margens reduzidas para aproveitar melhor o espaço horizontal
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           rightMargin=0.25*inch, leftMargin=0.25*inch,
                           topMargin=0.3*inch, bottomMargin=0.3*inch)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#1f4e79'),
        spaceAfter=8,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#1f4e79'),
        spaceAfter=4,
        spaceBefore=8
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=2,
        leading=10
    )
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=7,
        spaceAfter=6,
        leading=9
    )
    
    # Dados do registro
    row = df.iloc[index]
    
    # Buscar colunas de forma flexível (tratando encoding)
    prefixo = 'N/A'
    cidade = 'N/A'
    vistoriador = 'N/A'
    data_vistoria = 'N/A'
    carimbo = None
    
    for col in df.columns:
        col_lower = col.lower()
        # Buscar especificamente por "ônibus (prefixo)" primeiro
        if 'ônibus' in col_lower and 'prefixo' in col_lower:
            prefixo = str(row.get(col, 'N/A'))
        elif 'prefixo' in col_lower:
            prefixo = str(row.get(col, 'N/A'))
        elif 'cidade' in col_lower:
            cidade = str(row.get(col, 'N/A'))
        elif 'vistoriador' in col_lower:
            vistoriador = str(row.get(col, 'N/A'))
        elif 'data da vistoria' in col_lower:
            data_vistoria = str(row.get(col, 'N/A'))
        elif 'carimbo' in col_lower and 'data' in col_lower:
            carimbo = row.get(col, None)
    # Formatar data_hora no formato brasileiro DD-MM-AAAA
    if pd.notna(carimbo):
        if isinstance(carimbo, pd.Timestamp):
            data_hora_formatada = carimbo.strftime('%d-%m-%Y %H:%M')
        else:
            # Tentar converter se for string
            try:
                data_hora_formatada = pd.to_datetime(carimbo).strftime('%d-%m-%Y %H:%M')
            except:
                data_hora_formatada = str(carimbo).replace('/', '-')
    else:
        data_hora_formatada = 'N/A'
    
    # Conteúdo do PDF
    story = []
    
    # Título
    title = f"<b>RELATÓRIO DE VISTORIA - PREFIXO {prefixo}</b>"
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Informações gerais (em formato mais compacto)
    # Usar data_hora_formatada (do carimbo) como "Data da Vistoria"
    info_text = f"<b>Cidade:</b> {cidade} | <b>Vistoriador:</b> {vistoriador}<br/>"
    info_text += f"<b>Data da Vistoria:</b> {data_hora_formatada}"
    story.append(Paragraph(info_text, info_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Organizar não conformidades por área
    # Ordem das áreas conforme a planilha de formatação
    areas_order = ['EXTERNA', 'CABINE', 'SALÃO', 'SANITÁRIO', 'GELADEIRA']
    non_conformities_by_area = {area: [] for area in areas_order}
    
    # Se não houver mapeamento, usar função antiga como fallback
    if column_mapping is None:
        column_mapping = {}
    
    # Processar cada coluna
    for col in df.columns:
        col_lower = col.lower()
        
        # Ignorar colunas de metadados
        if any(x in col_lower for x in ['carimbo', 'endereço', 'e-mail', 'email', 'prefixo', 
                                         'data da vistoria', 'cidade', 'vistoriador', 'wi-fi', 'wifi']):
            continue
        
        # Ignorar colunas de fotos
        if 'fotografia' in col_lower or 'fotografias' in col_lower:
            continue
        
        # Verificar se é observação geral
        if 'observações gerais' in col_lower or 'observacoes gerais' in col_lower:
            continue
        
        value = row[col]
        if has_non_conformity(value):
            # Usar mapeamento se disponível
            nome_tratado, area = get_column_info(col, column_mapping)
            
            if area and area in areas_order:
                # Usar nome tratado se disponível, senão usar nome original formatado
                item_name = nome_tratado if nome_tratado else format_item_name(col)
                # Armazenar também o nome da coluna original para formatação de datas de extintor
                non_conformities_by_area[area].append((item_name, value, col))
            elif not column_mapping:
                # Fallback para função antiga se não houver mapeamento
                area_antiga = get_area_from_column(col)
                if area_antiga:
                    # Converter nome da área antiga para novo formato
                    area_map = {
                        'Externa': 'EXTERNA',
                        'Cabine': 'CABINE',
                        'Salão': 'SALÃO',
                        'Sanitário': 'SANITÁRIO',
                        'Geladeiras': 'GELADEIRA'
                    }
                    area = area_map.get(area_antiga)
                    if area and area in areas_order:
                        item_name = format_item_name(col)
                        non_conformities_by_area[area].append((item_name, value, col))
    
    # Coletar observações gerais separadamente (serão exibidas na seção GERAL ao final)
    obs_geral = None
    obs_geral_col = None
    for col in df.columns:
        if 'observações gerais' in col.lower() or 'observacoes gerais' in col.lower():
            obs_geral = row.get(col, '')
            obs_geral_col = col
            break
    
    # Calcular altura total estimada e ajustar espaçamentos
    # Incluir observações gerais na contagem se houver
    total_items = sum(len(items) for items in non_conformities_by_area.values())
    if pd.notna(obs_geral) and str(obs_geral).strip():
        total_items += 1
    areas_with_items = sum(1 for items in non_conformities_by_area.values() if items)
    
    # Ajustar espaçamentos baseado na quantidade de conteúdo
    if total_items > 20:
        item_spacing = 1
        area_spacing = 3
        normal_style.spaceAfter = 1
    elif total_items > 10:
        item_spacing = 2
        area_spacing = 4
        normal_style.spaceAfter = 2
    else:
        item_spacing = 3
        area_spacing = 6
        normal_style.spaceAfter = 3
    
    # Mapear nomes das áreas para exibição
    area_display_names = {
        'EXTERNA': 'EXTERNA',
        'CABINE': 'CABINE',
        'SALÃO': 'SALÃO',
        'SANITÁRIO': 'SANITÁRIO',
        'GELADEIRA': 'GELADEIRAS'
    }
    
    # Adicionar conteúdo por área (apenas áreas com não conformidades)
    for area in areas_order:
        if non_conformities_by_area[area]:
            display_name = area_display_names.get(area, area)
            story.append(Paragraph(f"<b>{display_name}</b>", heading_style))
            
            for item_data in non_conformities_by_area[area]:
                # Desempacotar dados: (item_name, item_value, col_name_original)
                if len(item_data) == 3:
                    item_name, item_value, col_name_original = item_data
                else:
                    # Fallback para compatibilidade
                    item_name, item_value = item_data
                    col_name_original = None
                
                # Formatar valor removendo decimais desnecessários
                value_str = format_value(item_value, col_name_original)
                
                # Não limitar o nome do item - deixar quebrar naturalmente
                # O ReportLab vai quebrar automaticamente se necessário
                
                item_text = f"• <b>{item_name}:</b> {value_str}"
                story.append(Paragraph(item_text, normal_style))
                story.append(Spacer(1, item_spacing))
            
            story.append(Spacer(1, area_spacing))
    
    # Adicionar seção GERAL com observações gerais ao final (se houver)
    if pd.notna(obs_geral) and str(obs_geral).strip():
        story.append(Paragraph(f"<b>GERAL</b>", heading_style))
        
        # Buscar nome tratado para observações gerais
        nome_tratado, _ = get_column_info(obs_geral_col, column_mapping) if column_mapping and obs_geral_col else (None, None)
        nome_obs = nome_tratado if nome_tratado else 'Observações Gerais'
        
        # Formatar valor das observações gerais
        value_str = str(obs_geral)
        # Não limitar manualmente - deixar o ReportLab quebrar automaticamente
        
        item_text = f"• <b>{nome_obs}:</b> {value_str}"
        story.append(Paragraph(item_text, normal_style))
        story.append(Spacer(1, item_spacing))
    
    # Se não houver nenhuma não conformidade e nenhuma observação geral
    if not any(non_conformities_by_area.values()) and (pd.isna(obs_geral) or not str(obs_geral).strip()):
        story.append(Paragraph("<b>Nenhuma não conformidade registrada.</b>", normal_style))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# Interface principal
def main():
    # CSS personalizado para melhorar a aparência
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
    }
    /* Estilizar botões de forma uniforme (PDF e Imprimir) */
    .stButton>button,
    .stDownloadButton>button {
        width: 100%;
        min-width: 90px;
        background-color: #1f4e79;
        color: white;
        border-radius: 4px;
        border: none;
        padding: 0.4rem 0.6rem;
        font-size: 0.85rem;
        white-space: nowrap;
        height: 38px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .stButton>button:hover,
    .stDownloadButton>button:hover {
        background-color: #2c6da0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Título principal
    st.markdown('<h1 class="main-header">🚌 DASHBOARDS GERENCIAIS</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Carregar dados e mapeamento
    df = load_data()
    column_mapping = load_column_mapping()
    
    if df.empty:
        st.warning("Nenhum dado encontrado na planilha.")
        return
    
    # Dashboard Gerencial
    st.header("📊 Dashboard Gerencial")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_vistorias = len(df)
        st.metric("Total de Vistorias", total_vistorias)
    
    with col2:
        cidade_col = None
        for col in df.columns:
            if 'cidade' in col.lower():
                cidade_col = col
                break
        if cidade_col:
            cidades_unicas = df[cidade_col].nunique()
            st.metric("Cidades", cidades_unicas)
        else:
            st.metric("Cidades", 0)
    
    with col3:
        vistoriador_col = None
        for col in df.columns:
            if 'vistoriador' in col.lower():
                vistoriador_col = col
                break
        if vistoriador_col:
            vistoriadores_unicos = df[vistoriador_col].nunique()
            st.metric("Vistoriadores", vistoriadores_unicos)
        else:
            st.metric("Vistoriadores", 0)
    
    with col4:
        carimbo_col = None
        for col in df.columns:
            if 'carimbo' in col.lower() and 'data' in col.lower():
                carimbo_col = col
                break
        if carimbo_col:
            ultima_vistoria = df[carimbo_col].max()
            if pd.notna(ultima_vistoria):
                if isinstance(ultima_vistoria, pd.Timestamp):
                    st.metric("Última Vistoria", ultima_vistoria.strftime('%d/%m/%Y'))
                else:
                    st.metric("Última Vistoria", str(ultima_vistoria))
            else:
                st.metric("Última Vistoria", "N/A")
        else:
            st.metric("Última Vistoria", "N/A")
    
    st.markdown("---")
    
    # Gerenciador de Arquivos
    st.header("📁 Registros de Vistoria")
    
    # Tabela de registros
    if len(df) > 0:
        # Preparar dados para exibição
        display_data = []
        for idx in range(len(df)):
            row = df.iloc[idx]
            
            # Buscar colunas de forma flexível
            prefixo = 'N/A'
            cidade = 'N/A'
            vistoriador = 'N/A'
            data_vistoria = 'N/A'
            carimbo = None
            
            for col in df.columns:
                col_lower = col.lower()
                # Buscar especificamente por "ônibus (prefixo)" primeiro
                if 'ônibus' in col_lower and 'prefixo' in col_lower:
                    prefixo = str(row.get(col, 'N/A'))
                elif 'prefixo' in col_lower:
                    prefixo = str(row.get(col, 'N/A'))
                elif 'cidade' in col_lower:
                    cidade = str(row.get(col, 'N/A'))
                elif 'vistoriador' in col_lower:
                    vistoriador = str(row.get(col, 'N/A'))
                elif 'data da vistoria' in col_lower:
                    data_vistoria = str(row.get(col, 'N/A'))
                elif 'carimbo' in col_lower and 'data' in col_lower:
                    carimbo = row.get(col, None)
            
            if pd.notna(carimbo):
                if isinstance(carimbo, pd.Timestamp):
                    data_hora = carimbo.strftime('%d-%m-%Y %H:%M')
                else:
                    # Tentar converter se for string
                    try:
                        data_hora = pd.to_datetime(carimbo).strftime('%d-%m-%Y %H:%M')
                    except:
                        data_hora = str(carimbo).replace('/', '-')
            else:
                data_hora = 'N/A'
            
            # Separar data e hora para exibição
            if ' ' in data_hora:
                data_parte = data_hora.split()[0]  # DD-MM-AAAA
                hora_parte = data_hora.split()[1]  # HH:MM
            else:
                data_parte = data_hora
                hora_parte = 'N/A'
            
            display_data.append({
                'Prefixo': prefixo,
                'Cidade': cidade,
                'Vistoriador': vistoriador,
                'Data': data_parte,
                'Hora': hora_parte,
                'Índice': idx
            })
        
        # CSS para responsividade
        st.markdown("""
        <style>
        .stDataFrame {
            font-size: 14px;
        }
        .registro-row {
            padding: 10px;
            margin: 5px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        
        /* Layout de card para mobile */
        .registro-card {
            background-color: #262730;
            border: 1px solid #3d3d3d;
            border-radius: 8px;
            padding: 1.2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .registro-card-item {
            margin-bottom: 0.8rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #3d3d3d;
        }
        
        .registro-card-item:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        
        .registro-card-label {
            font-weight: 600;
            color: #9ca3af;
            margin-right: 0.5rem;
            font-size: 0.9rem;
        }
        
        .registro-card-value {
            color: #ffffff;
            font-size: 1rem;
        }
        
        /* Por padrão: esconder mobile, mostrar desktop */
        .mobile-cards {
            display: none !important;
        }
        .desktop-table {
            display: block !important;
        }
        
        /* Mobile: esconder desktop, mostrar mobile */
        @media only screen and (max-width: 768px) {
            .desktop-table {
                display: none !important;
            }
            .desktop-table * {
                display: none !important;
            }
            .mobile-cards {
                display: block !important;
            }
        }
        
        /* Desktop: esconder mobile, mostrar desktop */
        @media only screen and (min-width: 769px) {
            .mobile-cards {
                display: none !important;
            }
            .mobile-cards * {
                display: none !important;
            }
            .desktop-table {
                display: block !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # JavaScript para forçar responsividade (executa antes e depois da renderização)
        html("""
        <script>
        (function() {
            function applyLayout() {
                var width = window.innerWidth || document.documentElement.clientWidth || screen.width;
                var isMobile = width <= 768;
                
                var desktopDivs = document.querySelectorAll('.desktop-table');
                var mobileDivs = document.querySelectorAll('.mobile-cards');
                
                desktopDivs.forEach(function(div) {
                    if (div) {
                        if (isMobile) {
                            div.style.cssText = 'display: none !important; visibility: hidden !important;';
                        } else {
                            div.style.cssText = 'display: block !important; visibility: visible !important;';
                        }
                    }
                });
                
                mobileDivs.forEach(function(div) {
                    if (div) {
                        if (isMobile) {
                            div.style.cssText = 'display: block !important; visibility: visible !important;';
                        } else {
                            div.style.cssText = 'display: none !important; visibility: hidden !important;';
                        }
                    }
                });
            }
            
            // Executar imediatamente
            applyLayout();
            
            // Executar quando DOM estiver pronto
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', applyLayout);
            }
            
            // Executar ao redimensionar
            var resizeTimer;
            window.addEventListener('resize', function() {
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(applyLayout, 100);
            });
            
            // Executar múltiplas vezes para garantir (Streamlit renderiza assincronamente)
            setTimeout(applyLayout, 100);
            setTimeout(applyLayout, 300);
            setTimeout(applyLayout, 600);
            setTimeout(applyLayout, 1000);
            setTimeout(applyLayout, 2000);
            
            // Observar mudanças no DOM
            if (window.MutationObserver) {
                var observer = new MutationObserver(function() {
                    applyLayout();
                });
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            }
        })();
        </script>
        """, height=0)
        
        # Layout Desktop (Tabela) - será escondido em mobile via CSS/JS
        st.markdown('<div class="desktop-table" style="display: block;">', unsafe_allow_html=True)
        
        # Cabeçalho da tabela
        header_cols = st.columns([2, 2, 2, 2, 2, 2.5])
        with header_cols[0]:
            st.markdown("**DATA**")
        with header_cols[1]:
            st.markdown("**HORA**")
        with header_cols[2]:
            st.markdown("**PREFIXO**")
        with header_cols[3]:
            st.markdown("**CIDADE**")
        with header_cols[4]:
            st.markdown("**VISTORIADOR**")
        with header_cols[5]:
            st.markdown("**RELATÓRIO**")
        
        st.markdown("---")
        
        # Exibir registros em formato de tabela (desktop)
        for idx, row_data in enumerate(display_data):
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 2.5])
            
            with col1:
                st.write(row_data['Data'])
            
            with col2:
                st.write(row_data['Hora'])
            
            with col3:
                st.write(row_data['Prefixo'])
            
            with col4:
                st.write(row_data['Cidade'])
            
            with col5:
                st.write(row_data['Vistoriador'])
            
            with col6:
                # Função para botões (desktop)
                _render_buttons(df, row_data, idx, column_mapping, is_mobile=False)
            
            if idx < len(display_data) - 1:
                st.markdown("---")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Layout Mobile (Cards) - será escondido em desktop via CSS/JS
        st.markdown('<div class="mobile-cards" style="display: none;">', unsafe_allow_html=True)
        
        for idx, row_data in enumerate(display_data):
            # Card para mobile
            with st.container():
                st.markdown(f"""
                <div class="registro-card">
                    <div class="registro-card-item">
                        <span class="registro-card-label">Data:</span>
                        <span class="registro-card-value">{row_data['Data']}</span>
                    </div>
                    <div class="registro-card-item">
                        <span class="registro-card-label">Hora:</span>
                        <span class="registro-card-value">{row_data['Hora']}</span>
                    </div>
                    <div class="registro-card-item">
                        <span class="registro-card-label">Prefixo:</span>
                        <span class="registro-card-value">{row_data['Prefixo']}</span>
                    </div>
                    <div class="registro-card-item">
                        <span class="registro-card-label">Cidade:</span>
                        <span class="registro-card-value">{row_data['Cidade']}</span>
                    </div>
                    <div class="registro-card-item">
                        <span class="registro-card-label">Vistoriador:</span>
                        <span class="registro-card-value">{row_data['Vistoriador']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Botões para mobile
                _render_buttons(df, row_data, idx, column_mapping, is_mobile=True)
                
                if idx < len(display_data) - 1:
                    st.markdown("<br/>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Nenhum registro encontrado.")

if __name__ == "__main__":
    # Verificar autenticação antes de mostrar o conteúdo
    is_authenticated, authenticator = check_authentication()
    
    if is_authenticated:
        main()
    else:
        # Mostrar apenas a tela de login
        st.stop()
