import io
import zipfile
import streamlit as st
from pypdf import PdfReader, PdfWriter
from PIL import Image

st.set_page_config(page_title="PDF Fácil", page_icon="📄", layout="wide")

# =====================================================
# ESTILO
# =====================================================

st.markdown("""
<style>

body{
background:#f3f4f6;
}

.topmenu{
display:flex;
justify-content:center;
gap:15px;
margin-bottom:20px;
flex-wrap:wrap;
}

.topmenu button{
background:#e5322d;
color:white;
border:none;
padding:8px 14px;
border-radius:8px;
cursor:pointer;
font-weight:600;
}

.center{
text-align:center;
}

.tool-grid{
display:grid;
grid-template-columns:repeat(3,1fr);
gap:20px;
max-width:900px;
margin:auto;
margin-top:40px;
}

.tool-card{
background:white;
border-radius:16px;
padding:25px;
border:1px solid #e5e7eb;
box-shadow:0 5px 15px rgba(0,0,0,0.05);
text-align:center;
}

.tool-title{
font-size:18px;
font-weight:700;
margin-bottom:5px;
color:#111827;
}

.tool-desc{
font-size:14px;
color:#6b7280;
margin-bottom:10px;
}

.stButton{
text-align:center;
}

.stButton button{
background:#e5322d;
color:white;
border:none;
padding:10px 18px;
border-radius:8px;
font-weight:600;
}

.stButton button:hover{
background:#c92b27;
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

</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================

st.markdown("""
<div class="center">
<h1>PDF Fácil</h1>
<p>Ferramentas simples para editar PDFs diretamente no navegador</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# ESTADO
# =====================================================

TOOLS = {
"unlock":"🔓 Remover senha",
"merge":"📎 Juntar PDFs",
"split":"✂️ Dividir PDF",
"compress":"🗜️ Comprimir PDF",
"pdfimg":"🖼️ PDF para imagem",
"imgpdf":"🖼️ Imagem para PDF"
}

if "tool" not in st.session_state:
    st.session_state.tool = None

# =====================================================
# MENU TOPO
# =====================================================

cols = st.columns(len(TOOLS))

for i,(key,name) in enumerate(TOOLS.items()):

    if cols[i].button(name):
        st.session_state.tool = key
        st.rerun()

# =====================================================
# BALÕES INICIAIS
# =====================================================

if st.session_state.tool is None:

    st.markdown('<div class="tool-grid">',unsafe_allow_html=True)

    descriptions = {
    "unlock":"Remova a senha de arquivos protegidos",
    "merge":"Combine vários PDFs em um único arquivo",
    "split":"Separe páginas de um PDF",
    "compress":"Reduza o tamanho do arquivo",
    "pdfimg":"Transforme páginas em imagens",
    "imgpdf":"Crie PDF a partir de imagens"
    }

    for key,name in TOOLS.items():

        st.markdown(f"""
        <div class="tool-card">
        <div class="tool-title">{name}</div>
        <div class="tool-desc">{descriptions[key]}</div>
        </div>
        """,unsafe_allow_html=True)

        if st.button("Usar agora",key=key):
            st.session_state.tool = key
            st.rerun()

    st.markdown('</div>',unsafe_allow_html=True)

# =====================================================
# BOTÃO VOLTAR
# =====================================================

else:

    if st.button("⬅ Voltar para ferramentas"):
        st.session_state.tool=None
        st.rerun()

# =====================================================
# FUNÇÃO
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

# =====================================================
# JUNTAR PDF
# =====================================================

elif st.session_state.tool=="merge":

    st.header("📎 Juntar PDFs")

    arquivos = st.file_uploader(
        "Selecione os PDFs",
        type="pdf",
        accept_multiple_files=True
    )

    if st.button("Juntar PDFs"):

        writer = PdfWriter()

        for arquivo in arquivos:

            reader = PdfReader(arquivo)

            for page in reader.pages:
                writer.add_page(page)

        buffer = io.BytesIO()
        writer.write(buffer)

        st.download_button(
            "Baixar PDF unido",
            buffer.getvalue(),
            "pdf_unido.pdf"
        )

# =====================================================
# DIVIDIR PDF
# =====================================================

elif st.session_state.tool=="split":

    st.header("✂️ Dividir PDF")

    arquivo = st.file_uploader("Selecione o PDF", type="pdf")

    if arquivo:

        reader = PdfReader(arquivo)

        paginas = len(reader.pages)

        pagina = st.number_input(
            "Dividir após página",
            min_value=1,
            max_value=paginas-1
        )

        if st.button("Dividir PDF"):

            writer1 = PdfWriter()
            writer2 = PdfWriter()

            for i in range(pagina):
                writer1.add_page(reader.pages[i])

            for i in range(pagina,paginas):
                writer2.add_page(reader.pages[i])

            buffer1 = io.BytesIO()
            buffer2 = io.BytesIO()

            writer1.write(buffer1)
            writer2.write(buffer2)

            st.download_button("Baixar parte 1",buffer1.getvalue(),"parte1.pdf")
            st.download_button("Baixar parte 2",buffer2.getvalue(),"parte2.pdf")

# =====================================================
# IMAGEM PARA PDF
# =====================================================

elif st.session_state.tool=="imgpdf":

    st.header("🖼️ Imagem para PDF")

    imagens = st.file_uploader(
        "Envie imagens",
        type=["png","jpg","jpeg"],
        accept_multiple_files=True
    )

    if st.button("Converter em PDF"):

        lista = []

        for img in imagens:

            image = Image.open(img).convert("RGB")
            lista.append(image)

        buffer = io.BytesIO()

        lista[0].save(buffer,save_all=True,append_images=lista[1:],format="PDF")

        st.download_button(
            "Baixar PDF",
            buffer.getvalue(),
            "imagens.pdf"
        )
