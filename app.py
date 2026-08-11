import streamlit as st
import datetime
import json
import os
import re

# Configuração global da página
st.set_page_config(
    page_title="Diário Acadêmico",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

ARQUIVO_DADOS = "dados_academico.json"
PASTA_UPLOADS = "uploads"

# Criar diretório raiz de uploads se não existir
if not os.path.exists(PASTA_UPLOADS):
    os.makedirs(PASTA_UPLOADS, exist_ok=True)

# --- FUNÇÕES UTILITÁRIAS DE ARQUIVOS E ESTRUTURA ---
def sanitizar_nome(nome):
    """Sanitiza nomes para criação segura de pastas no sistema."""
    return re.sub(r'[^\w\s-]', '', nome).strip().replace(' ', '_')

def obter_pasta_aula(materia, data_str):
    """Gera o caminho organizado da pasta: uploads/Nome_Materia/AAAA-MM-DD/"""
    materia_clean = sanitizar_nome(materia)
    caminho = os.path.join(PASTA_UPLOADS, materia_clean, data_str)
    os.makedirs(caminho, exist_ok=True)
    return caminho

def carregar_dados():
    """Carrega os dados do arquivo JSON em disco."""
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "semestre": "2026.1",
        "materias": [],
        "diario": [],
        "agenda": []
    }

def salvar_dados(dados):
    """Grava as alterações permanentemente no arquivo JSON."""
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

def resolver_caminho_arquivo(item_arq, materia="", data_str=""):
    """
    Localiza o arquivo físico no servidor, garantindo compatibilidade
    com versões anteriores e com a nova estrutura de pastas organizadas.
    """
    if isinstance(item_arq, dict):
        caminho_rel = item_arq.get("caminho_relativo", "")
        nome_orig = item_arq.get("nome_original", os.path.basename(caminho_rel))
        if os.path.exists(caminho_rel):
            return caminho_rel, nome_orig
        
        # Tentativa na pasta estruturada da matéria/data
        pasta_esperada = os.path.join(PASTA_UPLOADS, sanitizar_nome(materia), data_str, nome_orig)
        if os.path.exists(pasta_esperada):
            return pasta_esperada, nome_orig

    elif isinstance(item_arq, str):
        # Tenta no formato legado (pasta raiz uploads)
        caminho_antigo = os.path.join(PASTA_UPLOADS, item_arq)
        if os.path.exists(caminho_antigo):
            return caminho_antigo, item_arq
        # Tenta na pasta estruturada
        pasta_nova = os.path.join(PASTA_UPLOADS, sanitizar_nome(materia), data_str, item_arq)
        if os.path.exists(pasta_nova):
            return pasta_nova, item_arq

    return None, str(item_arq)

# Inicializa os dados do aplicativo
dados = carregar_dados()

# --- MENU LATERAL DE NAVEGAÇÃO ---
st.sidebar.title("📌 Menu Principal")
st.sidebar.info(f"Período Ativo: **{dados.get('semestre', '2026.1')}**")

pagina = st.sidebar.radio(
    "Navegue pelas seções:",
    [
        "🏠 Meu Painel (Dashboard)",
        "📅 Grade Horária",
        "✍️ Diário de Aula",
        "📁 Central de Documentos",
        "🎯 Agenda & Provas",
        "⚙️ Configurações & Matérias"
    ]
)

DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado"]

# --- 1. MEU PAINEL (DASHBOARD) ---
if pagina == "🏠 Meu Painel (Dashboard)":
    st.title("🏠 Meu Painel Acadêmico")
    st.caption("Visão geral dos seus compromissos e rotina universitária.")
    
    st.subheader("⚠️ Próximas Obrigações (Agenda)")
    agenda = dados.get("agenda", [])
    
    if not agenda:
        st.info("Nenhuma obrigação ou prova cadastrada no momento.")
    else:
        hoje = datetime.date.today()
        agenda_ordenada = sorted(agenda, key=lambda x: x['data'])
        
        cols = st.columns(2)
        for idx, item in enumerate(agenda_ordenada):
            data_evt = datetime.datetime.strptime(item['data'], "%Y-%m-%d").date()
            dias_restantes = (data_evt - hoje).days
            
            conteudo_card = f"**{item['tipo']}**: {item['titulo']}\n\n📚 *{item['materia']}* | 🗓️ {data_evt.strftime('%d/%m/%Y')}"
            
            col = cols[idx % 2]
            if dias_restantes < 0:
                col.error(f"❌ **Vencido ({abs(dias_restantes)} dias)**\n\n{conteudo_card}")
            elif dias_restantes <= 3:
                col.error(f"🚨 **Urgente ({dias_restantes} dias restantes)**\n\n{conteudo_card}")
            elif dias_restantes <= 7:
                col.warning(f"🔔 **Atenção ({dias_restantes} dias restantes)**\n\n{conteudo_card}")
            else:
                col.info(f"📌 **Em {dias_restantes} dias**\n\n{conteudo_card}")

# --- 2. GRADE HORÁRIA ---
elif pagina == "📅 Grade Horária":
    st.title("📅 Grade Horária Semanal")
    st.caption("Visualização das suas aulas cadastradas no período.")
    
    materias = dados.get("materias", [])
    if not materias:
        st.warning("Nenhuma matéria cadastrada. Vá na aba '⚙️ Configurações & Matérias' para cadastrar sua grade.")
    else:
        grade_por_dia = {dia: [] for dia in DIAS_SEMANA}
        for mat in materias:
            dia = mat.get("dia")
            if dia in grade_por_dia:
                grade_por_dia[dia].append(f"{mat['horario_inicio']} - {mat['horario_fim']}: **{mat['nome']}**")
        
        cols = st.columns(len(DIAS_SEMANA))
        for idx, dia in enumerate(DIAS_SEMANA):
            with cols[idx]:
                st.markdown(f"### {dia[:3]}")
                st.caption(dia)
                aulas = grade_por_dia[dia]
                if aulas:
                    for aula in aulas:
                        st.info(aula)
                else:
                    st.write("- Sem aulas -")

# --- 3. DIÁRIO DE AULA (COM HISTÓRICO ORGANIZADO POR DATA) ---
elif pagina == "✍️ Diário de Aula":
    st.title("✍️ Diário de Aula e Anotações")
    
    materias = dados.get("materias", [])
    if not materias:
        st.warning("Cadastre matérias nas '⚙️ Configurações' para utilizar o Diário.")
    else:
        nomes_materias = [m["nome"] for m in materias]
        materia_sel = st.selectbox("Selecione a Disciplina:", nomes_materias)
        
        # Histórico de aulas já registradas nesta matéria
        registros_materia = [r for r in dados.get("diario", []) if r.get("materia") == materia_sel]
        
        if registros_materia:
            st.markdown("#### 📜 Aulas anteriores registradas nesta disciplina:")
            opcoes_datas = {}
            for r in sorted(registros_materia, key=lambda x: x["data"], reverse=True):
                qtd_arqs = len(r.get("arquivos", []))
                data_f = datetime.datetime.strptime(r["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
                label = f"🗓️ {data_f} — ({qtd_arqs} anexo(s))"
                opcoes_datas[label] = r["data"]
            
            data_selecionada_hist = st.selectbox(
                "Escolha uma aula cadastrada para consultar/editar ou selecione uma nova data abaixo:",
                ["-- Nova Entrada / Seleção Manual --"] + list(opcoes_datas.keys())
            )
            
            if data_selecionada_hist != "-- Nova Entrada / Seleção Manual --":
                data_padrao = datetime.datetime.strptime(opcoes_datas[data_selecionada_hist], "%Y-%m-%d").date()
            else:
                data_padrao = datetime.date.today()
        else:
            data_padrao = datetime.date.today()
            
        data_aula = st.date_input("Data da Aula:", value=data_padrao)
        data_str = data_aula.strftime("%Y-%m-%d")
        
        # Busca registro existente
        registro_existente = None
        for r in dados.get("diario", []):
            if r["materia"] == materia_sel and r["data"] == data_str:
                registro_existente = r
                break
                
        st.markdown("---")
        st.subheader("1. Anotações da Aula")
        texto_inicial = registro_existente["texto"] if registro_existente else ""
        texto_nota = st.text_area("Digite os conteúdos discutidos na aula:", value=texto_inicial, height=180)
        
        st.subheader("2. Anexar Arquivos (Salvos na pasta dedicada da matéria e data)")
        novos_arquivos = st.file_uploader(
            "Selecione imagens (JPG, PNG) ou documentos (PDF) desta aula:",
            accept_multiple_files=True,
            type=['jpg', 'jpeg', 'png', 'pdf']
        )
        
        # Exibição de arquivos do registro
        arquivos_salvos = registro_existente.get("arquivos", []) if registro_existente else []
        if arquivos_salvos:
            st.markdown(f"#### 📂 Arquivos anexados à aula de **{data_aula.strftime('%d/%m/%Y')}**:")
            for idx_arq, item_arq in enumerate(arquivos_salvos):
                caminho_completo, nome_exibicao = resolver_caminho_arquivo(item_arq, materia_sel, data_str)
                
                if caminho_completo and os.path.exists(caminho_completo):
                    col_f1, col_f2 = st.columns([4, 1])
                    with col_f1:
                        st.write(f"📄 **{nome_exibicao}**")
                        if nome_exibicao.lower().endswith(('.png', '.jpg', '.jpeg')):
                            st.image(caminho_completo, width=320)
                        
                        with open(caminho_completo, "rb") as file_data:
                            st.download_button(
                                label=f"⬇️ Baixar {nome_exibicao}",
                                data=file_data,
                                file_name=nome_exibicao,
                                key=f"dl_{materia_sel}_{data_str}_{idx_arq}"
                            )
                    with col_f2:
                        if st.button("🗑️ Remover", key=f"del_{materia_sel}_{data_str}_{idx_arq}"):
                            arquivos_salvos.pop(idx_arq)
                            registro_existente["arquivos"] = arquivos_salvos
                            if os.path.exists(caminho_completo):
                                os.remove(caminho_completo)
                            salvar_dados(dados)
                            st.success("Arquivo removido!")
                            st.rerun()

        st.info(f"📁 Os arquivos serão armazenados em: `uploads/{sanitizar_nome(materia_sel)}/{data_str}/`")
        
        if st.button("💾 Salvar Anotações e Anexos", type="primary"):
            lista_arquivos_atualizada = list(arquivos_salvos)
            
            if novos_arquivos:
                pasta_destino = obter_pasta_aula(materia_sel, data_str)
                for arq in novos_arquivos:
                    caminho_arquivo_fisico = os.path.join(pasta_destino, arq.name)
                    
                    with open(caminho_arquivo_fisico, "wb") as f:
                        f.write(arq.getbuffer())
                    
                    item_obj = {
                        "nome_original": arq.name,
                        "caminho_relativo": caminho_arquivo_fisico
                    }
                    
                    # Evita duplicatas pelo nome original
                    ja_existe = any(
                        (isinstance(x, dict) and x.get("nome_original") == arq.name) or
                        (isinstance(x, str) and x == arq.name)
                        for x in lista_arquivos_atualizada
                    )
                    if not ja_existe:
                        lista_arquivos_atualizada.append(item_obj)

            if registro_existente:
                registro_existente["texto"] = texto_nota
                registro_existente["arquivos"] = lista_arquivos_atualizada
            else:
                dados.setdefault("diario", []).append({
                    "materia": materia_sel,
                    "data": data_str,
                    "texto": texto_nota,
                    "arquivos": lista_arquivos_atualizada
                })
                
            salvar_dados(dados)
            st.success("✅ Registro e arquivos salvos permanentemente e organizados por matéria/data!")
            st.rerun()

# --- 4. CENTRAL DE DOCUMENTOS (SELEÇÃO POR CALENDÁRIO PADRÃO) ---
elif pagina == "📁 Central de Documentos":
    st.title("📁 Central de Documentos por Calendário")
    st.caption("Escolha qualquer data no mini calendário abaixo para visualizar todos os documentos e fotos anexados naquele dia.")
    
    # Coleta de todos os arquivos anexados no sistema
    todos_anexos = []
    for entry in dados.get("diario", []):
        mat = entry.get("materia", "Geral")
        data = entry.get("data", "")
        arqs = entry.get("arquivos", [])
        
        for item_arq in arqs:
            caminho, nome = resolver_caminho_arquivo(item_arq, mat, data)
            if caminho and os.path.exists(caminho):
                ext = os.path.splitext(nome)[1].lower()
                tipo = "PDF" if ext == ".pdf" else "Imagem" if ext in ['.jpg', '.jpeg', '.png'] else "Outro"
                tamanho_kb = round(os.path.getsize(caminho) / 1024, 1)
                todos_anexos.append({
                    "materia": mat,
                    "data": data,
                    "nome": nome,
                    "caminho": caminho,
                    "tipo": tipo,
                    "tamanho_kb": tamanho_kb
                })
                
    st.subheader("📅 Selecione a Data no Calendário")
    col_cal, col_info = st.columns([1, 2])
    
    with col_cal:
        data_consulta = st.date_input("Escolha a Data:", value=datetime.date.today(), format="DD/MM/YYYY")
        data_str_consulta = data_consulta.strftime("%Y-%m-%d")
        data_f = data_consulta.strftime("%d/%m/%Y")
        
    with col_info:
        st.write("")
        st.write("")
        st.info(f"📆 **Data selecionada:** {data_f}\n\n*O sistema buscará automaticamente todos os anexos cadastrados nessa data específica.*")
        
    st.markdown("---")
    
    # Filtra os documentos da data escolhida no calendário
    anexos_da_data = [a for a in todos_anexos if a["data"] == data_str_consulta]
    
    if not anexos_da_data:
        st.warning(f"🔍 Nenhum arquivo ou documento foi anexado para a data **{data_f}**.")
    else:
        st.subheader(f"📄 Documentos Encontrados em {data_f}")
        st.caption(f"Total: {len(anexos_da_data)} arquivo(s) registrado(s) nesta data")
        
        # Exibição dos cards com destaque claro para a disciplina
        for idx_doc, doc in enumerate(sorted(anexos_da_data, key=lambda x: x["materia"])):
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### 📘 Disciplina: `{doc['materia']}`")
                    st.write(f"📄 **Arquivo:** {doc['nome']} *({doc['tipo']} - {doc['tamanho_kb']} KB)*")
                    
                    if doc['tipo'] == 'Imagem':
                        st.image(doc['caminho'], width=380)
                
                with col2:
                    st.write("")
                    st.write("")
                    with open(doc['caminho'], "rb") as file_data:
                        st.download_button(
                            label=f"⬇️ Baixar {doc['nome']}",
                            data=file_data,
                            file_name=doc['nome'],
                            key=f"cal_dl_{data_str_consulta}_{idx_doc}"
                        )
                st.divider()

# --- 5. AGENDA & PROVAS ---
elif pagina == "🎯 Agenda & Provas":
    st.title("🎯 Agenda de Obrigações e Responsabilidades")
    
    materias = dados.get("materias", [])
    nomes_materias = [m["nome"] for m in materias] if materias else ["Geral"]
    
    st.subheader("➕ Novo Compromisso")
    with st.form("form_agenda"):
        titulo = st.text_input("Descrição (Ex: Prova 1, Entrega de Trabalho):")
        materia_rel = st.selectbox("Disciplina:", nomes_materias)
        data_evt = st.date_input("Data da Obrigação:", datetime.date.today())
        tipo = st.selectbox("Tipo:", ["Prova", "Trabalho", "Apresentação", "Outro"])
        
        btn_add = st.form_submit_button("Confirmar e Salvar na Agenda")
        if btn_add:
            if titulo.strip() == "":
                st.error("Digite uma descrição para o compromisso.")
            else:
                novo_evt = {
                    "id": len(dados.get("agenda", [])) + 1,
                    "titulo": titulo,
                    "materia": materia_rel,
                    "data": data_evt.strftime("%Y-%m-%d"),
                    "tipo": tipo
                }
                dados.setdefault("agenda", []).append(novo_evt)
                salvar_dados(dados)
                st.success("✅ Compromisso gravado permanentemente!")
                st.rerun()

    st.markdown("---")
    st.subheader("📋 Compromissos Cadastrados (Edição / Exclusão)")
    
    agenda = dados.get("agenda", [])
    if not agenda:
        st.info("Nenhum compromisso cadastrado.")
    else:
        for idx, item in enumerate(agenda):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{item['tipo']}**: {item['titulo']} ({item['materia']})")
            with col2:
                st.write(f"🗓️ {item['data']}")
            with col3:
                if st.button("🗑️ Excluir", key=f"del_agenda_{idx}"):
                    dados["agenda"].pop(idx)
                    salvar_dados(dados)
                    st.success("Compromisso removido!")
                    st.rerun()

# --- 6. CONFIGURAÇÕES & MATÉRIAS ---
elif pagina == "⚙️ Configurações & Matérias":
    st.title("⚙️ Configuração do Período e Cadastro de Matérias")
    
    st.subheader("1. Período Acadêmico")
    col_sem1, col_sem2 = st.columns([3, 1])
    with col_sem1:
        novo_semestre = st.text_input("Identificação do Semestre Ativo:", value=dados.get("semestre", "2026.1"))
    with col_sem2:
        st.write("")
        st.write("")
        if st.button("Salvar Período"):
            dados["semestre"] = novo_semestre
            salvar_dados(dados)
            st.success("Período atualizado!")
            st.rerun()
            
    st.markdown("---")
    st.subheader("2. Cadastrar Matérias e Horários da Grade")
    
    with st.form("form_materia"):
        nome_mat = st.text_input("Nome da Matéria / Disciplina:")
        dia_mat = st.selectbox("Dia da Semana:", DIAS_SEMANA)
        
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            h_inicio = st.time_input("Horário de Início:", datetime.time(8, 0))
        with col_h2:
            h_fim = st.time_input("Horário de Término:", datetime.time(10, 0))
            
        confirmar_add = st.form_submit_button("Confirmar e Adicionar Matéria")
        if confirmar_add:
            if nome_mat.strip() == "":
                st.error("Informe o nome da matéria.")
            else:
                nova_materia = {
                    "nome": nome_mat,
                    "dia": dia_mat,
                    "horario_inicio": h_inicio.strftime("%H:%M"),
                    "horario_fim": h_fim.strftime("%H:%M")
                }
                dados.setdefault("materias", []).append(nova_materia)
                salvar_dados(dados)
                st.success(f"✅ Matéria '{nome_mat}' adicionada permanentemente!")
                st.rerun()
                
    st.markdown("---")
    st.subheader("3. Matérias Cadastradas no Período")
    
    materias = dados.get("materias", [])
    if not materias:
        st.info("Nenhuma matéria cadastrada ainda.")
    else:
        for idx, mat in enumerate(materias):
            col_m1, col_m2, col_m3 = st.columns([3, 2, 1])
            with col_m1:
                st.write(f"📖 **{mat['nome']}**")
            with col_m2:
                st.write(f"🗓️ {mat['dia']} ({mat['horario_inicio']} às {mat['horario_fim']})")
            with col_m3:
                if st.button("🗑️ Apagar", key=f"del_mat_{idx}"):
                    dados["materias"].pop(idx)
                    salvar_dados(dados)
                    st.success("Matéria removida!")
                    st.rerun()

    st.markdown("---")
    st.subheader("4. Encerrar Período Acadêmico")
    st.warning("⚠️ Ao encerrar o período, os dados do semestre serão limpos para um novo ciclo.")
    check_encerrar = st.checkbox("Confirmo que desejo apagar e encerrar as matérias deste semestre.")
    if st.button("🔴 Finalizar Período"):
        if check_encerrar:
            dados["materias"] = []
            dados["diario"] = []
            dados["agenda"] = []
            salvar_dados(dados)
            st.success("Período encerrado e limpo com sucesso!")
            st.rerun()
        else:
            st.error("Marque a caixa de confirmação primeiro.")