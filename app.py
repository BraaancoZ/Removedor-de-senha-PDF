import io
import zipfile
import streamlit as st
from pypdf import PdfReader, PdfWriter
from PIL import Image

st.set_page_config(page_title="PDF Fácil", page_icon="📄", layout="wide")

# ============================
# ESTILO CLARO
# ============================

st.markdown("""
<style>

html, body, [data-testid="stAppViewContainer"]{
background:#f9fafb;
color:#111827;
}

header{
background:transparent !important;
}

.hero{
text-align:center;
margin-top:20px;
margin-bottom:30px;
}

.hero h1{
font-size:2.6rem;
color:#111827;
}

.hero p{
color:#6b7280;
}

.tool-card{
background:white;
border-radius:18px;
border:1px solid #e5e7eb;
padding:22px;
text-align:center;
box-shadow:0 6px 20px rgba(0,0,0,0.06);
}

.tool-title{
font-weight:700;
margin-bottom:8px;
}

.tool-desc{
font-size:14px;
color:#6b7280;
margin-bottom:16px;
}

/* CENTRALIZA BOTÕES */

.stButton{
display:flex;
justify-content:center;
}

.stButton button{
background:#ef4444;
color:white;
border:none;
padding:10px 22px;
border-radius:10px;
font-weight:600;
}

.stButton button:hover{
background:#dc2626;
}

/* uploader */

[data-testid="stFileUploaderDropzone"]{
border:2px dashed #d1d5db;
background:white;
border-radius:14px;
}

[data-testid="stFileUploaderDropzoneInstructions"] div{
visibility:hidden;
}

[data-testid="stFileUploaderDropzoneInstructions"] div::before{
content:"Arraste e solte os arquivos aqui";
visibility:visible;
display:block;
text-align:center;
color:#374151;
}

/* botão selecionar arquivo */

[data-testid="stFileUploader"] section button{
font-size:0;
}

[data-testid="stFileUploader"] section button::after{
content:"Selecionar arquivos";
font-size:14px;
}

/* inputs centralizados */

[data-testid="stFileUploader"],
.stTextInput{
max-width:600px;
margin-left:auto;
margin-right:auto;
}

label{
text-align:center !important;
display:block;
width:100%;
}

.tool-container{
max-width:850px;
margin:auto;
background:white;
border-radius:18px;
padding:30px;
border:1px solid #e5e7eb;
box-shadow:0 6px 20px rgba(0,0,0,0.06);
}

.footer{
text-align:center;
color:#6b7280;
margin-top:30px;
}

</style>
""", unsafe_allow_html=True)

# ============================
# HEADER
# ============================

st.markdown("""
<div class="hero">
<h1>PDF Fácil</h1>
<p>Ferramentas simples para editar PDFs diretamente no navegador</p>
</div>
""", unsafe_allow_html=True)

# ============================
# ESTADO
# ============================

TOOLS = {
"unlock":"🔓 Remover senha",
"merge":"📎 Juntar PDFs",
"split":"✂️ Dividir PDF",
"compress":"🗜️ Comprimir PDF",
"imgpdf":"🖼️ Imagem para PDF"
}

DESCRIPTIONS = {
"unlock":"Remova a senha de arquivos protegidos",
"merge":"Combine vários PDFs em um único arquivo",
"split":"Separe páginas de um PDF",
"compress":"Reduza o tamanho do arquivo",
"imgpdf":"Crie PDF a partir de imagens"
}

if "tool" not in st.session_state:
    st.session_state.tool = None

# ============================
# MENU TOPO
# ============================

cols = st.columns(len(TOOLS))

for i,(key,name) in enumerate(TOOLS.items()):
    if cols[i].button(name):
        st.session_state.tool = key
        st.rerun()

# ============================
# TELA INICIAL
# ============================

if st.session_state.tool is None:

    col1,col2,col3 = st.columns(3)

    keys = list(TOOLS.keys())

    for col,key in zip([col1,col2,col3],keys[:3]):
        with col:
            st.markdown(f"""
            <div class="tool-card">
            <div class="tool-title">{TOOLS[key]}</div>
            <div class="tool-desc">{DESCRIPTIONS[key]}</div>
            </div>
            """,unsafe_allow_html=True)

            if st.button("Usar agora",key=key):
                st.session_state.tool=key
                st.rerun()

    col4,col5 = st.columns(2)

    for col,key in zip([col4,col5],keys[3:]):
        with col:
            st.markdown(f"""
            <div class="tool-card">
            <div class="tool-title">{TOOLS[key]}</div>
            <div class="tool-desc">{DESCRIPTIONS[key]}</div>
            </div>
            """,unsafe_allow_html=True)

            if st.button("Usar agora",key="tool"+key):
                st.session_state.tool=key
                st.rerun()

# ============================
# FUNÇÕES
# ============================

def unlock_pdf(pdf_bytes,password):

    reader=PdfReader(io.BytesIO(pdf_bytes))

    if reader.is_encrypted:
        reader.decrypt(password)

    writer=PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    buffer=io.BytesIO()
    writer.write(buffer)

    return buffer.getvalue()

# ============================
# FERRAMENTA
# ============================

if st.session_state.tool is not None:

    if st.button("⬅ Voltar para ferramentas"):
        st.session_state.tool=None
        st.rerun()

    st.markdown('<div class="tool-container">',unsafe_allow_html=True)

    # =======================
    # REMOVER SENHA
    # =======================

    if st.session_state.tool=="unlock":

        st.header("🔓 Remover senha de PDF")

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

    st.markdown("</div>",unsafe_allow_html=True)

st.markdown('<div class="footer">Ferramentas PDF gratuitas online</div>',unsafe_allow_html=True)
