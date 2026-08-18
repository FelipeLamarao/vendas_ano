import streamlit as st
import pandas as pd
import plotly.express as px
import re
import os

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Painel de Vendas Intelgentes",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeção de CSS personalizado para estética premium e moderna
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    /* Fontes globais */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Outfit', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700 !important;
    }

    /* Título principal e subtítulo */
    .main-header {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }
    
    .sub-header {
        color: #94a3b8;
        font-size: 1.15rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    /* Seções e Títulos */
    .section-title {
        font-size: 1.6rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1.2rem;
        border-left: 5px solid #3b82f6;
        padding-left: 12px;
        color: #f1f5f9;
        letter-spacing: -0.01em;
    }

    /* Cards com Glassmorfismo */
    .kpi-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 1.5rem;
    }
    
    .kpi-card:hover {
        transform: translateY(-6px);
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 0 20px 30px -10px rgba(59, 130, 246, 0.2), 0 10px 15px -5px rgba(59, 130, 246, 0.1);
    }

    .kpi-label {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 10px;
    }

    .kpi-value {
        color: #ffffff;
        font-size: 2.25rem;
        font-weight: 700;
        line-height: 1.2;
    }
    
    .kpi-sub {
        color: #3b82f6;
        font-size: 0.85rem;
        margin-top: 8px;
        font-weight: 500;
    }

    /* Badge para a Cor Mais Vendida */
    .color-badge-container {
        display: flex;
        align-items: center;
        margin-top: 15px;
        gap: 15px;
    }

    .color-circle {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        border: 2px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }

    /* Rodapé */
    .footer {
        text-align: center;
        padding: 3rem 0 1rem 0;
        color: #64748b;
        font-size: 0.85rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        margin-top: 4rem;
    }
</style>
""", unsafe_allow_html=True)


# Função para buscar e carregar o arquivo de vendas automaticamente
@st.cache_data(show_spinner=False)
def load_data():
    files = os.listdir('.')
    target_file = None
    for f in files:
        if 'vendas' in f.lower() and f.endswith(('.xls', '.xlsx', '.csv')):
            target_file = f
            break
            
    if not target_file:
        return None, None, "Nenhum arquivo 'vendas' (.xls, .xlsx, .csv) encontrado no diretório atual."
        
    try:
        if target_file.endswith('.csv'):
            # Detecta o separador correto
            with open(target_file, 'r', encoding='utf-8', errors='ignore') as file_obj:
                first_line = file_obj.readline()
            sep = ';' if ';' in first_line else ','
            df = pd.read_csv(target_file, sep=sep)
            df['Modelo'] = df['Modelo'].str.replace(r'^(NV|NW|nv|nw)\s+', '', regex=True)
        else:
            # Excel
            df = pd.read_excel(target_file)
            df['Modelo'] = df['Modelo'].str.replace(r'^(NV|NW|nv|nw)\s+', '', regex=True)
    except Exception as e:
        return None, None, f"Erro ao ler o arquivo {target_file}: {str(e)}"
        
    return df, target_file, None


# Função para detectar automaticamente as colunas necessárias
def detect_columns(df):
    detected = {}
    cols = df.columns.tolist()
    cols_lower = [str(c).lower().strip() for c in cols]
    
    # 1. Coluna de Data
    date_patterns = [r'\bdata\b', r'\bdate\b', r'^dt_', r'\bperiodo\b', r'\bperíodo\b']
    for p in date_patterns:
        for idx, cl in enumerate(cols_lower):
            if re.search(p, cl):
                detected['date'] = cols[idx]
                break
        if 'date' in detected:
            break
            
    # 2. Coluna de Modelo
    model_patterns = [r'\bmodelo\b', r'\bmodel\b']
    for p in model_patterns:
        for idx, cl in enumerate(cols_lower):
            if re.search(p, cl):
                if cl == 'modelo' or cl == 'model':
                    detected['model'] = cols[idx]
                    break
                elif 'model' not in detected:
                    detected['model'] = cols[idx]
        if 'model' in detected and (detected['model'].lower().strip() in ['modelo', 'model']):
            break
            
    # 3. Coluna de Cor
    color_patterns = [r'\bcor\b', r'\bcolor\b']
    for p in color_patterns:
        for idx, cl in enumerate(cols_lower):
            if re.search(p, cl):
                detected['color'] = cols[idx]
                break
        if 'color' in detected:
            break
            
    # 4. Coluna de Valor
    value_patterns = [
        r'\bvalor da venda\b', 
        r'\bvalor\b', 
        r'\bvenda\b', 
        r'\bpreco\b', 
        r'\bpreço\b', 
        r'\bprice\b', 
        r'\bval_'
    ]
    for p in value_patterns:
        for idx, cl in enumerate(cols_lower):
            if re.search(p, cl):
                detected['value'] = cols[idx]
                break
        if 'value' in detected:
            break
            
    # Fallbacks inteligentes caso não encontre
    if 'date' not in detected:
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                detected['date'] = c
                break
        else:
            detected['date'] = df.columns[0]
            
    if 'model' not in detected:
        detected['model'] = 'Modelo' if 'Modelo' in df.columns else df.columns[1]
        
    if 'color' not in detected:
        detected['color'] = 'Cor' if 'Cor' in df.columns else df.columns[2]
        
    if 'value' not in detected:
        for c in df.columns:
            if pd.api.types.is_numeric_dtype(df[c]) and c != detected.get('date'):
                detected['value'] = c
                break
        else:
            detected['value'] = df.columns[-1]
            
    return detected


# Função para obter estilo CSS correspondente à cor do veículo
def get_color_style(color_name):
    color_name = str(color_name).upper()
    bg_color = "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)" # Azul moderno padrão
    circle_color = "#3b82f6"
    text_color = "#ffffff"
    border_color = "rgba(255, 255, 255, 0.15)"
    
    if "PRATA" in color_name:
        bg_color = "linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%)"
        circle_color = "#cbd5e1"
        text_color = "#0f172a"
    elif "BRANCO" in color_name:
        bg_color = "linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%)"
        circle_color = "#ffffff"
        text_color = "#0f172a"
        border_color = "#cbd5e1"
    elif "PRETO" in color_name:
        bg_color = "linear-gradient(135deg, #334155 0%, #0f172a 100%)"
        circle_color = "#000000"
        text_color = "#ffffff"
    elif "VERMELHO" in color_name:
        bg_color = "linear-gradient(135deg, #f87171 0%, #dc2626 100%)"
        circle_color = "#ef4444"
        text_color = "#ffffff"
    elif "AZUL" in color_name:
        bg_color = "linear-gradient(135deg, #60a5fa 0%, #2563eb 100%)"
        circle_color = "#3b82f6"
        text_color = "#ffffff"
    elif "CINZA" in color_name:
        bg_color = "linear-gradient(135deg, #94a3b8 0%, #475569 100%)"
        circle_color = "#64748b"
        text_color = "#ffffff"
    elif "VERDE" in color_name:
        bg_color = "linear-gradient(135deg, #34d399 0%, #059669 100%)"
        circle_color = "#10b981"
        text_color = "#ffffff"
    elif "AMARELO" in color_name:
        bg_color = "linear-gradient(135deg, #fbbf24 0%, #d97706 100%)"
        circle_color = "#f59e0b"
        text_color = "#0f172a"
        
    return bg_color, circle_color, text_color, border_color


# Formatação para moeda Real
def format_real(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# Dicionário de tradução de meses
meses_pt = {
    "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
    "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
    "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro"
}


# Carregando dados
with st.spinner("Carregando base de dados..."):
    df_raw, file_name, error_msg = load_data()

if error_msg:
    st.error(error_msg)
    st.info("💡 Por favor, certifique-se de que o arquivo 'vendas.xls' ou 'vendas.csv' está na pasta raiz do projeto.")
else:
    # Cópia para processamento
    df = df_raw.copy()
    
    # Identificar colunas automaticamente
    detected_cols = detect_columns(df)
    
    date_col = detected_cols['date']
    model_col = detected_cols['model']
    color_col = detected_cols['color']
    value_col = detected_cols['value']
    
    # Limpeza e conversão dos dados
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Drop rows sem data válida (como a linha de "Total Geral" no final do vendas.xls)
    df = df.dropna(subset=[date_col])
    
    # Garantir que a coluna de valor é numérica
    if not pd.api.types.is_numeric_dtype(df[value_col]):
        df[value_col] = df[value_col].astype(str).str.replace(r'[^\d.,-]', '', regex=True)
        df[value_col] = df[value_col].apply(lambda x: x.replace('.', '').replace(',', '.') if ',' in x and '.' in x else (x.replace(',', '.') if ',' in x else x))
        df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
    
    # Determinar a data mais recente da base
    max_date = df[date_col].max()
    
    # Filtrar os dados dos últimos 3 meses (usando data mais recente como base)
    start_date = max_date - pd.DateOffset(months=3)
    df_filtered = df[df[date_col] >= start_date].copy()
    
    # Extração dinâmica de meses para o filtro
    df_filtered['MesNum'] = df_filtered[date_col].dt.strftime('%m')
    df_filtered['MesNome'] = df_filtered['MesNum'].map(meses_pt)
    
    df_filtered_sorted = df_filtered.sort_values(by=date_col)
    available_months = [m for m in df_filtered_sorted['MesNome'].unique() if pd.notna(m)]
    
    # Seletor de mês na barra lateral
    with st.sidebar:
        st.markdown("### 🔍 Filtros de Vendas")
        selected_month = st.selectbox(
            "Selecione o Mês:",
            options=["Todos os Meses"] + available_months,
            index=0,
            help="Selecione um mês específico para analisar ou 'Todos os Meses' para ver os últimos 3 meses consolidados."
        )
    
    # Filtragem condicional dos dados
    if selected_month == "Todos os Meses":
        df_active = df_filtered.copy()
        period_label = "últimos 3 meses"
        period_label_kpi = "3 Meses"
    else:
        df_active = df_filtered[df_filtered['MesNome'] == selected_month].copy()
        period_label = f"mês de {selected_month}"
        period_label_kpi = selected_month
        
    # --- Layout da Página ---
    
    # Cabeçalho
    st.markdown('<div class="main-header">Painel Analítico de Vendas</div>', unsafe_allow_html=True)
    if selected_month == "Todos os Meses":
        sub_header_text = f"Análise inteligente baseada no arquivo 📁 <b>{file_name}</b> no período de {start_date.strftime('%d/%m/%Y')} a {max_date.strftime('%d/%m/%Y')} ({period_label})"
    else:
        sub_header_text = f"Análise inteligente baseada no arquivo 📁 <b>{file_name}</b> filtrada para o {period_label}"
    st.markdown(f'<div class="sub-header">{sub_header_text}</div>', unsafe_allow_html=True)
    
    # Métricas Gerais em Destaque
    total_sales = df_active[value_col].sum()
    monthly_average = total_sales / (3.0 if selected_month == "Todos os Meses" else 1.0)
    total_units = len(df_active)
    
    # col1, col2, col3 = st.columns(3)
    # 
    # with col1:
    #     st.markdown(f"""
    #     <div class="kpi-card">
    #         <div class="kpi-label">Faturamento Total (3 Meses)</div>
    #         <div class="kpi-value">{format_real(total_sales)}</div>
    #         <div class="kpi-sub">Soma acumulada do faturamento</div>
    #     </div>
    #     """, unsafe_allow_html=True)
    #     
    # with col2:
    #     st.markdown(f"""
    #     <div class="kpi-card">
    #         <div class="kpi-label">Média Mensal de Vendas</div>
    #         <div class="kpi-value">{format_real(monthly_average)}</div>
    #         <div class="kpi-sub">Faturamento total dividido por 3</div>
    #     </div>
    #     """, unsafe_allow_html=True)
    #     
    # with col3:
    #     st.markdown(f"""
    #     <div class="kpi-card">
    #         <div class="kpi-label">Unidades Vendidas</div>
    #         <div class="kpi-value">{total_units:,}</div>
    #         <div class="kpi-sub">Total de veículos comercializados</div>
    #     </div>
    #     """, unsafe_allow_html=True)
        
    # --- Seção do Modelo Selecionável ---
    st.markdown('<div class="section-title">Análise por Modelo de Veículo</div>', unsafe_allow_html=True)
    
    # Dropdown de modelos
    available_models = sorted(df_active[model_col].dropna().unique())
    
    col_select, col_space = st.columns([2, 2])
    with col_select:
        selected_model = st.selectbox(
            "Selecione um modelo de veículo para detalhar:",
            options=available_models,
            index=0 if len(available_models) > 0 else None,
            help="Escolha o veículo para visualizar a cor mais vendida e sua quantidade."
        )
        
    if selected_model:
        # Filtrar dados para o modelo selecionado
        df_model = df_active[df_active[model_col] == selected_model]
        
        # Obter a cor mais vendida e a quantidade
        color_counts = df_model[color_col].value_counts()
        
        if not color_counts.empty:
            most_sold_color = color_counts.index[0]
            qty_most_sold = color_counts.iloc[0]
            total_model_sold = len(df_model)
            percent_color = (qty_most_sold / total_model_sold) * 100
            
            # Obter estilos de cores para a badge
            bg_grad, circ_col, text_col, border_col = get_color_style(most_sold_color)
            
            # Exibir Métricas do Modelo Selecionado
            col_m1, col_m2 = st.columns(2)
            
            with col_m1:
                text_color_analysis = f"A cor mais vendida nos {period_label} é:" if selected_month == "Todos os Meses" else f"A cor mais vendida no {period_label} é:"
                st.markdown(f"""
                <div class="kpi-card" style="height: 100%;">
                    <div class="kpi-label">Análise de Cor - {selected_model}</div>
                    <div style="font-size: 1.1rem; color: #94a3b8; margin-bottom: 15px;">{text_color_analysis}</div>
                    <div style="background: {bg_grad}; color: {text_col}; border: 1px solid {border_col}; padding: 20px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                        <div class="color-badge-container">
                            <div class="color-circle" style="background-color: {circ_col};"></div>
                            <div>
                                <div style="font-size: 1.4rem; font-weight: 700; text-shadow: 0 1px 2px rgba(0,0,0,0.15);">{most_sold_color}</div>
                                <div style="font-size: 0.95rem; opacity: 0.9; font-weight: 500;">{qty_most_sold} unidades ({percent_color:.1f}% das vendas deste modelo)</div>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with col_m2:
                # Gráfico interativo com Plotly
                df_chart = color_counts.reset_index()
                df_chart.columns = ['Cor', 'Unidades']
                
                fig = px.bar(
                    df_chart.head(8),
                    x='Unidades',
                    y='Cor',
                    orientation='h',
                    title=f"Top Cores Vendidas - {selected_model} ({period_label_kpi})",
                    labels={'Unidades': 'Unidades', 'Cor': 'Cor'},
                    color='Unidades',
                    color_continuous_scale='Blues'
                )
                
                fig.update_layout(
                    paper_bgcolor='rgba(30, 41, 59, 0.4)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#cbd5e1',
                    title_font_family="'Outfit', sans-serif",
                    title_font_size=16,
                    margin=dict(l=10, r=10, t=40, b=10),
                    coloraxis_showscale=False,
                    height=220
                )
                fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
                fig.update_yaxes(showgrid=False, categoryorder='total ascending')
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
            # Detalhes Adicionais
            st.markdown('<div class="section-title">Dados de Distribuição de Vendas por Cor</div>', unsafe_allow_html=True)
            
            # DataFrame formatado para exibição
            df_table = df_chart.copy()
            df_table['Faturamento Cor'] = df_table['Cor'].apply(lambda c: df_model[df_model[color_col] == c][value_col].sum())
            df_table['Média por Unidade'] = df_table['Faturamento Cor'] / df_table['Unidades']
            df_table['Representatividade'] = (df_table['Unidades'] / total_model_sold) * 100
            
            # Formatações para a tabela
            df_table_formatted = df_table.copy()
            df_table_formatted['Faturamento Cor'] = df_table_formatted['Faturamento Cor'].apply(format_real)
            df_table_formatted['Média por Unidade'] = df_table_formatted['Média por Unidade'].apply(format_real)
            df_table_formatted['Representatividade'] = df_table_formatted['Representatividade'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(
                df_table_formatted,
                column_config={
                    "Cor": st.column_config.TextColumn("Cor do Veículo"),
                    "Unidades": st.column_config.NumberColumn("Qtd. Vendida", format="%d"),
                    "Faturamento Cor": st.column_config.TextColumn("Faturamento Total"),
                    "Média por Unidade": st.column_config.TextColumn("Preço Médio Unitário"),
                    "Representatividade": st.column_config.TextColumn("% de Vendas")
                },
                hide_index=True,
                use_container_width=True
            )

            # Novas Métricas de Volume e Vendas Mensais do Modelo
            st.markdown('<div class="section-title">Volume de Vendas e Distribuição Mensal</div>', unsafe_allow_html=True)
            col_v1, col_v2 = st.columns(2)
            
            with col_v1:
                avg_model_monthly = total_model_sold / (3.0 if selected_month == "Todos os Meses" else 1.0)
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Volume Total de Vendas ({period_label_kpi})</div>
                    <div class="kpi-value">{total_model_sold} <span style="font-size: 1.2rem; color: #94a3b8; font-weight: 400;">unidades</span></div>
                    <div class="kpi-sub">Faturamento Total do Modelo: {format_real(df_model[value_col].sum())}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">{"Média Mensal de Vendas" if selected_month == "Todos os Meses" else "Volume Mensal"}</div>
                    <div class="kpi-value">{avg_model_monthly:.1f} <span style="font-size: 1.2rem; color: #94a3b8; font-weight: 400;">unidades{"/mês" if selected_month == "Todos os Meses" else ""}</span></div>
                    <div class="kpi-sub">{"Calculado para o período de 3 meses" if selected_month == "Todos os Meses" else f"Referente a {selected_month}"}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col_v2:
                df_model_monthly = df_model.copy()
                df_model_monthly['AnoMês'] = df_model_monthly[date_col].dt.to_period('M').astype(str)
                
                def format_month_year(row_val):
                    parts = row_val.split('-')
                    if len(parts) == 2:
                        y, m = parts
                        return f"{meses_pt.get(m, m)}/{y}"
                    return row_val

                df_model_monthly['Mês/Ano'] = df_model_monthly['AnoMês'].apply(format_month_year)
                
                monthly_counts = df_model_monthly.groupby(['AnoMês', 'Mês/Ano']).size().reset_index(name='Unidades Vendidas')
                monthly_counts = monthly_counts.sort_values('AnoMês')
                
                chart_data = monthly_counts.set_index('Mês/Ano')[['Unidades Vendidas']]
                
                st.markdown(f'<div class="kpi-label" style="margin-bottom: 15px;">Vendas Mensais (Unidades) - {period_label_kpi}</div>', unsafe_allow_html=True)
                st.bar_chart(chart_data, color="#3b82f6")
        else:
            st.warning(f"Não há dados de cores registrados para o modelo {selected_model}.")
            
    # # Gráficos e Insights Gerais de Faturamento Temporal
    # st.markdown('<div class="section-title">Tendência de Faturamento Mensal</div>', unsafe_allow_html=True)
    # 
    # df_filtered['AnoMês'] = df_filtered[date_col].dt.to_period('M').astype(str)
    # df_monthly = df_filtered.groupby('AnoMês')[value_col].sum().reset_index()
    # df_monthly.columns = ['Mês', 'Faturamento']
    # df_monthly['Faturamento Formatado'] = df_monthly['Faturamento'].apply(format_real)
    # 
    # col_chart, col_details = st.columns([3, 1])
    # 
    # with col_chart:
    #     fig_monthly = px.area(
    #         df_monthly,
    #         x='Mês',
    #         y='Faturamento',
    #         title="Evolução do Faturamento Mensal nos Últimos 3 Meses",
    #         labels={'Faturamento': 'Faturamento (R$)', 'Mês': 'Mês de Faturamento'},
    #         markers=True
    #     )
    #     
    #     # Personalização estética premium do gráfico de área
    #     fig_monthly.update_traces(
    #         line_color='#3b82f6',
    #         fillcolor='rgba(59, 130, 246, 0.1)',
    #         line_width=3
    #     )
    #     
    #     fig_monthly.update_layout(
    #         paper_bgcolor='rgba(30, 41, 59, 0.4)',
    #         plot_bgcolor='rgba(0,0,0,0)',
    #         font_color='#cbd5e1',
    #         title_font_family="'Outfit', sans-serif",
    #         title_font_size=18,
    #         margin=dict(l=20, r=20, t=50, b=20),
    #         height=300
    #     )
    #     fig_monthly.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
    #     fig_monthly.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
    #     
    #     st.plotly_chart(fig_monthly, use_container_width=True, config={'displayModeBar': False})
    #     
    # with col_details:
    #     st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)
    #     for idx, row in df_monthly.iterrows():
    #         st.markdown(f"""
    #         <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 12px 18px; margin-bottom: 10px;">
    #             <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;">MÊS {row['Mês']}</div>
    #             <div style="font-size: 1.15rem; color: #ffffff; font-weight: 700; margin-top: 4px;">{row['Faturamento Formatado']}</div>
    #         </div>
    #         """, unsafe_allow_html=True)

# Rodapé
st.markdown('<div class="footer">Desenvolvido com ❤️ e inteligência de dados • Antigravity 2026</div>', unsafe_allow_html=True)
