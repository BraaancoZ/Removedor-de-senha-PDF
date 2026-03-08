# PDF Fácil - Ferramentas PDF Online

import io
import os
import time
import zipfile
from typing import List, Tuple

import fitz
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from pypdf import PdfReader, PdfWriter
from streamlit_sortables import sort_items


st.set_page_config(
    page_title="PDF Fácil",
    page_icon="📄",
    layout="wide"
)

# =====================================================
# ESTILO VISUAL CORRIGIDO
# =====================================================

st.markdown("""
<style>

:root{
--primary:#e5322d;
--primary-hover:#c92b27;
--card:#ffffff;
--border:#e5e7eb;
--text:#1f2937;
--muted:#6b7280;
--radius:20px;
}

html,body,[data-testid="stAppViewContainer"]{
background:#f6f8fc;
color:var(--text);
}

header{
background:transparent!important;
}

.block-container{
padding-top:1rem;
}

.center{
text-align:center;
}

.card{
background:var(--card);
border:1px solid var(--border);
border-radius:var(--radius);
padding:1.4rem;
box-shadow:0 10px 25px rgba(0,0,0,.06);
margin-bottom:1rem;
}

.hero{
text-align:center;
margin-bottom:1.4rem;
}

.hero h1{
font-size:2.6rem;
font-weight:800;
}

.hero p{
color:var(--muted);
}

.kpi-grid{
display:grid;
grid-template-columns:repeat(3,1fr);
gap:10px;
margin:1rem auto;
max-width:900px;
}

.kpi{
background:white;
border:1px solid var(--border);
border-radius:14px;
padding:12px;
text-align:center;
}

.tool-grid{
display:grid;
grid-template-columns:repeat(3,1fr);
gap:12px;
max-width:1000px;
margin:auto;
}

.tool-card{
background:white;
border:1px solid var(--border);
border-radius:16px;
padding:14px;
text-align:center;
}

.tool-title{
font-weight:700;
}

.tool-desc{
color:var(--muted);
font-size:0.9rem;
margin-bottom:10px;
}

.stButton{
text-align:center;
}

.stButton button{
background:var(--primary);
color:white;
border:none;
padding:10px 20px;
border-radius:10px;
font-weight:600;
}

.stButton button:hover{
background:var(--primary-hover);
}

[data-testid="stFileUploaderDropzone"]{
background:#f9fafb!important;
border:2px dashed #cbd5e1!important;
}

[data-testid="stFileUploaderDropzoneInstructions"] div{
visibility:hidden;
position:relative;
}

[data-testid="stFileUploaderDropzoneInstructions"] div::before{
content:"Arraste e solte os arquivos aqui";
visibility:visible;
position:absolute;
width:100%;
text-align:center;
}

[data-testid="stFileUploader"] section button{
font-size:0;
}

[data-testid="stFileUploader"] section button::after{
content:"Selecionar arquivos";
font-size:14px;
}

label{
text-align:center!important;
display:block;
width:100%;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# HERO
# =====================================================

st.markdown("""
<div class="hero">
<h1>PDF Fácil</h1>
<p>Ferramentas simples para editar PDFs diretamente no navegador</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="kpi-grid">
<div class="kpi">🔐 Desbloqueie PDFs protegidos</div>
<div class="kpi">⚡ Simples e rápido</div>
<div class="kpi">🖼 Converta arquivos facilmente</div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# FERRAMENTAS
# =====================================================

TOOLS = [
"🔓 Remover senha",
"📎 Juntar PDFs",
"✂️ Dividir PDF",
"🗜️ Comprimir PDF",
"🖼️ PDF para imagem",
"🖼️ Imagem para PDF"
]

if "tool" not in st.session_state:
    st.session_state.tool = TOOLS[0]

menu = st.sidebar.radio("Ferramentas",TOOLS,index=TOOLS.index(st.session_state.tool))
st.session_state.tool = menu

# =====================================================
# CARDS HOME
# =====================================================

st.markdown('<div class="tool-grid">',unsafe_allow_html=True)

tool_desc = {
"🔓 Remover senha":"Remova a senha de arquivos protegidos",
"📎 Juntar PDFs":"Combine vários PDFs em um único arquivo",
"✂️ Dividir PDF":"Separe páginas de um PDF",
"🗜️ Comprimir PDF":"Reduza o tamanho do arquivo",
"🖼️ PDF para imagem":"Transforme páginas em imagens",
"🖼️ Imagem para PDF":"Crie PDF a partir de imagens"
}

for tool in TOOLS:

    st.markdown(f"""
    <div class="tool-card">
    <div class="tool-title">{tool}</div>
    <div class="tool-desc">{tool_desc[tool]}</div>
    </div>
    """,unsafe_allow_html=True)

    if st.button("Usar agora",key=tool):
        st.session_state.tool = tool
        st.rerun()

st.markdown('</div>',unsafe_allow_html=True)

menu = st.session_state.tool

# =====================================================
# FUNÇÕES
# =====================================================

def unlock_pdf(pdf_bytes,password):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    if reader.is_encrypted:
        reader.decrypt(password)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()

# =====================================================
# REMOVER SENHA
# =====================================================

if menu=="🔓 Remover senha":

    st.markdown('<div class="card center">',unsafe_allow_html=True)

    arquivos = st.file_uploader(
        "Envie os PDFs",
        type="pdf",
        accept_multiple_files=True
    )

    senha = st.text_input("Digite a senha",type="password")

    if st.button("Desbloquear PDFs"):

        resultados=[]

        for arquivo in arquivos:

            nome=arquivo.name
            data=unlock_pdf(arquivo.getvalue(),senha)

            resultados.append((nome,data))

        zip_buffer=io.BytesIO()

        with zipfile.ZipFile(zip_buffer,"w") as zip_file:

            for nome,data in resultados:
                zip_file.writestr(nome,data)

        st.download_button(
            "Baixar todos",
            zip_buffer.getvalue(),
            "pdfs_desbloqueados.zip"
        )

    st.markdown('</div>',unsafe_allow_html=True)

# =====================================================
# FOOTER
# =====================================================

st.markdown('<p class="center">Ferramentas PDF gratuitas online</p>',unsafe_allow_html=True)
