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
html, body, [data-testid="stAppViewContainer"]{
    background:#f8fafc;
    color:#0f172a;
}

header{
    background:transparent !important;
}

.center{
    text-align:center;
}

.hero{
    text-align:center;
    margin-top:10px;
    margin-bottom:30px;
}

.hero h1{
    font-size:2.5rem;
    margin-bottom:6px;
    color:#0f172a;
}

.hero p{
    color:#475569;
    font-size:1rem;
}

/* Área central dos balões */
.cards-wrapper{
    max-width:980px;
    margin:0 auto 30px auto;
}

/* Balões */
.tool-card{
    background:#ffffff;
    border:1px solid #dbe4ee;
    border-radius:18px;
    padding:22px 18px;
    text-align:center;
    box-shadow:0 10px 26px rgba(148, 163, 184, 0.14);
    min-height:180px;
    display:flex;
    flex-direction:column;
    justify-content:space-between;
}

.tool-title{
    font-size:1.05rem;
    font-weight:700;
    color:#0f172a;
    margin-bottom:8px;
}

.tool-desc{
    font-size:0.92rem;
    color:#64748b;
    line-height:1.4;
    margin-bottom:18px;
}

/* Centralizar botões */
.stButton{
    text-align:center;
}

.stButton > button{
    background:#ef4444;
    color:white;
    border:none;
    border-radius:10px;
    padding:10px 18px;
    font-weight:600;
    box-shadow:0 8px 20px rgba(239, 68, 68, 0.18);
}

.stButton > button:hover{
    background:#dc2626;
    color:white;
}

/* Botões dentro das ferramentas */
.tool-action{
    display:flex;
    justify-content:center;
    margin-top:18px;
    margin-bottom:4px;
}

/* Menu superior */
.top-buttons{
    max-width:1100px;
    margin:0 auto 20px auto;
}

/* Uploader em português */
[data-testid="stFileUploaderDropzoneInstructions"] div{
    visibility:hidden;
    position:relative;
}

[data-testid="stFileUploaderDropzoneInstructions"] div::before{
    content:"Arraste e solte os arquivos aqui";
    visibility:visible;
    position:absolute;
    width:100%;
    left:0;
    text-align:center;
    color:#0f172a;
    font-weight:500;
}

[data-testid="stFileUploader"] section button{
    font-size:0 !important;
}

[data-testid="stFileUploader"] section button::after{
    content:"Selecionar arquivos";
    font-size:14px !important;
    color:#0f172a;
}

/* Inputs mais centralizados */
[data-testid="stFileUploader"],
.stTextInput,
.stNumberInput{
    max-width:620px;
    margin-left:auto;
    margin-right:auto;
}

label{
    text-align:center !important;
    display:block;
    width:100%;
    color:#0f172a !important;
}

/* Área da ferramenta */
.tool-panel{
    max-width:900px;
    margin:0 auto;
    background:#ffffff;
    border:1px solid #dbe4ee;
    border-radius:18px;
    padding:24px;
    box-shadow:0 10px 26px rgba(148, 163, 184, 0.14);
}

.tool-panel h2{
    text-align:center;
    color:#0f172a;
    margin-bottom:18px;
}

.footer-note{
    text-align:center;
    color:#64748b;
    margin-top:30px;
    margin-bottom:10px;
}

/* Melhor aparência dos campos */
input, textarea{
    background:#ffffff !important;
    color:#0f172a !important;
}

[data-baseweb="input"]{
    background:#ffffff !important;
    border-radius:12px !important;
}

[data-testid="stFileUploaderDropzone"]{
    background:#fefefe !important;
    border:2px dashed #cbd5e1 !important;
    border-radius:16px !important;
}

/* Dark mode suave */
@media (prefers-color-scheme: dark){
    html, body, [data-testid="stAppViewContainer"]{
        background:#0f172a;
        color:#f8fafc;
    }

    .hero h1{
        color:#f8fafc;
    }

    .hero p{
        color:#cbd5e1;
    }

    .tool-card,
    .tool-panel{
        background:#111827;
        border:1px solid #334155;
        box-shadow:0 8px 24px rgba(0,0,0,0.25);
    }

    .tool-title{
        color:#f8fafc;
    }

    .tool-desc{
        color:#cbd5e1;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] div::before{
        color:#f8fafc;
    }

    [data-testid="stFileUploader"] section button::after{
        color:#f8fafc;
    }

    .footer-note{
        color:#cbd5e1;
    }

    label{
        color:#f8fafc !important;
    }

    [data-testid="stFileUploaderDropzone"]{
        background:#1e293b !important;
        border:2px dashed #475569 !important;
    }
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================

st.markdown("""
<div class="hero">
    <h1>PDF Fácil</h1>
    <p>Ferramentas simples para editar PDFs diretamente no navegador</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# ESTADO
# =====================================================

TOOLS = {
    "unlock": "🔓 Remover senha",
    "merge": "📎 Juntar PDFs",
    "split": "✂️ Dividir PDF",
    "compress": "🗜️ Comprimir PDF",
    "pdfimg": "🖼️ PDF para imagem",
    "imgpdf": "🖼️ Imagem para PDF",
}

DESCRIPTIONS = {
    "unlock": "Remova a senha de arquivos protegidos",
    "merge": "Combine vários PDFs em um único arquivo",
    "split": "Separe páginas de um PDF",
    "compress": "Reduza o tamanho do arquivo",
    "pdfimg": "Transforme páginas em imagens",
    "imgpdf": "Crie PDF a partir de imagens",
}

if "tool" not in st.session_state:
    st.session_state.tool = None

# =====================================================
# MENU SUPERIOR
# =====================================================

top_cols = st.columns(6)
for i, (key, name) in enumerate(TOOLS.items()):
    if top_cols[i].button(name, key=f"top_{key}"):
        st.session_state.tool = key
        st.rerun()

# =====================================================
# TELA INICIAL COM BALÕES CENTRALIZADOS
# =====================================================

if st.session_state.tool is None:
    st.markdown('<div class="cards-wrapper">', unsafe_allow_html=True)

    row1 = st.columns(3, gap="medium")
    first_keys = list(TOOLS.keys())[:3]

    for col, key in zip(row1, first_keys):
        with col:
            st.markdown(
                f"""
                <div class="tool-card">
                    <div>
                        <div class="tool-title">{TOOLS[key]}</div>
                        <div class="tool-desc">{DESCRIPTIONS[key]}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Usar agora", key=f"home_{key}"):
                st.session_state.tool = key
                st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    row2 = st.columns(3, gap="medium")
    second_keys = list(TOOLS.keys())[3:]

    for col, key in zip(row2, second_keys):
        with col:
            st.markdown(
                f"""
                <div class="tool-card">
                    <div>
                        <div class="tool-title">{TOOLS[key]}</div>
                        <div class="tool-desc">{DESCRIPTIONS[key]}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Usar agora", key=f"home2_{key}"):
                st.session_state.tool = key
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# FUNÇÕES
# =====================================================

def unlock_pdf(pdf_bytes, password):
    reader = PdfReader(io.BytesIO(pdf_bytes))

    if reader.is_encrypted:
        result = reader.decrypt(password)
        if result == 0:
            raise ValueError("Senha incorreta.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def merge_pdfs(files):
    writer = PdfWriter()
    for arquivo in files:
        reader = PdfReader(arquivo)
        for page in reader.pages:
            writer.add_page(page)

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def split_pdf(file, split_after):
    reader = PdfReader(file)

    writer1 = PdfWriter()
    writer2 = PdfWriter()

    for i in range(split_after):
        writer1.add_page(reader.pages[i])

    for i in range(split_after, len(reader.pages)):
        writer2.add_page(reader.pages[i])

    buffer1 = io.BytesIO()
    buffer2 = io.BytesIO()
    writer1.write(buffer1)
    writer2.write(buffer2)

    return buffer1.getvalue(), buffer2.getvalue()


def images_to_pdf(imagens):
    lista = []
    for img in imagens:
        image = Image.open(img).convert("RGB")
        lista.append(image)

    buffer = io.BytesIO()
    lista[0].save(buffer, save_all=True, append_images=lista[1:], format="PDF")
    return buffer.getvalue()

# =====================================================
# EXIBIR FERRAMENTA SELECIONADA
# =====================================================

if st.session_state.tool is not None:
    if st.button("⬅ Voltar para ferramentas"):
        st.session_state.tool = None
        st.rerun()

    st.markdown('<div class="tool-panel">', unsafe_allow_html=True)

    # REMOVER SENHA
    if st.session_state.tool == "unlock":
        st.markdown("<h2>🔓 Remover senha de PDF</h2>", unsafe_allow_html=True)

        arquivos = st.file_uploader(
            "Envie os PDFs",
            type="pdf",
            accept_multiple_files=True,
            key="unlock_files"
        )

        senha = st.text_input("Digite a senha", type="password")

        st.markdown('<div class="tool-action">', unsafe_allow_html=True)
        desbloquear = st.button("Desbloquear PDFs")
        st.markdown('</div>', unsafe_allow_html=True)

        if desbloquear:
            if not arquivos:
                st.warning("Envie pelo menos um PDF.")
            elif not senha:
                st.warning("Digite a senha.")
            else:
                resultados = []

                try:
                    for arquivo in arquivos:
                        nome = arquivo.name
                        data = unlock_pdf(arquivo.getvalue(), senha)
                        resultados.append((nome, data))

                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                        for nome, data in resultados:
                            zip_file.writestr(nome, data)

                    st.download_button(
                        "Baixar todos",
                        zip_buffer.getvalue(),
                        "pdfs_desbloqueados.zip"
                    )

                except Exception as e:
                    st.error(str(e))

    # JUNTAR PDFs
    elif st.session_state.tool == "merge":
        st.markdown("<h2>📎 Juntar PDFs</h2>", unsafe_allow_html=True)

        arquivos = st.file_uploader(
            "Selecione os PDFs",
            type="pdf",
            accept_multiple_files=True,
            key="merge_files"
        )

        st.markdown('<div class="tool-action">', unsafe_allow_html=True)
        juntar = st.button("Juntar PDFs")
        st.markdown('</div>', unsafe_allow_html=True)

        if juntar:
            if not arquivos:
                st.warning("Envie pelo menos um PDF.")
            else:
                buffer = merge_pdfs(arquivos)
                st.download_button(
                    "Baixar PDF unido",
                    buffer,
                    "pdf_unido.pdf"
                )

    # DIVIDIR PDF
    elif st.session_state.tool == "split":
        st.markdown("<h2>✂️ Dividir PDF</h2>", unsafe_allow_html=True)

        arquivo = st.file_uploader("Selecione o PDF", type="pdf", key="split_file")

        if arquivo:
            reader = PdfReader(arquivo)
            paginas = len(reader.pages)

            if paginas > 1:
                pagina = st.number_input(
                    "Dividir após página",
                    min_value=1,
                    max_value=paginas - 1,
                    value=1
                )

                st.markdown('<div class="tool-action">', unsafe_allow_html=True)
                dividir = st.button("Dividir PDF")
                st.markdown('</div>', unsafe_allow_html=True)

                if dividir:
                    parte1, parte2 = split_pdf(arquivo, pagina)
                    st.download_button("Baixar parte 1", parte1, "parte1.pdf")
                    st.download_button("Baixar parte 2", parte2, "parte2.pdf")
            else:
                st.warning("O PDF precisa ter pelo menos 2 páginas.")

    # COMPRIMIR PDF
    elif st.session_state.tool == "compress":
        st.markdown("<h2>🗜️ Comprimir PDF</h2>", unsafe_allow_html=True)

        arquivo = st.file_uploader("Selecione o PDF", type="pdf", key="compress_file")

        st.markdown('<div class="tool-action">', unsafe_allow_html=True)
        comprimir = st.button("Comprimir PDF")
        st.markdown('</div>', unsafe_allow_html=True)

        if comprimir:
            if not arquivo:
                st.warning("Envie um PDF.")
            else:
                reader = PdfReader(arquivo)
                writer = PdfWriter()

                for page in reader.pages:
                    writer.add_page(page)

                buffer = io.BytesIO()
                writer.write(buffer)

                st.download_button(
                    "Baixar PDF comprimido",
                    buffer.getvalue(),
                    "pdf_comprimido.pdf"
                )

    # PDF PARA IMAGEM
    elif st.session_state.tool == "pdfimg":
        st.markdown("<h2>🖼️ PDF para imagem</h2>", unsafe_allow_html=True)

        arquivo = st.file_uploader("Selecione o PDF", type="pdf", key="pdfimg_file")

        if arquivo:
            reader = PdfReader(arquivo)
            st.info(f"Total de páginas: {len(reader.pages)}")
            st.warning("A conversão completa para imagem ainda pode ser adicionada na próxima versão.")

    # IMAGEM PARA PDF
    elif st.session_state.tool == "imgpdf":
        st.markdown("<h2>🖼️ Imagem para PDF</h2>", unsafe_allow_html=True)

        imagens = st.file_uploader(
            "Envie imagens",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="imgpdf_files"
        )

        st.markdown('<div class="tool-action">', unsafe_allow_html=True)
        converter = st.button("Converter em PDF")
        st.markdown('</div>', unsafe_allow_html=True)

        if converter:
            if not imagens:
                st.warning("Envie pelo menos uma imagem.")
            else:
                pdf_bytes = images_to_pdf(imagens)
                st.download_button(
                    "Baixar PDF",
                    pdf_bytes,
                    "imagens.pdf"
                )

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="footer-note">Ferramentas PDF gratuitas online</div>', unsafe_allow_html=True)
