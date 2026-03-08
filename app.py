import io
import zipfile
import streamlit as st
from pypdf import PdfReader, PdfWriter
from PIL import Image

st.set_page_config(
    page_title="PDF Fácil",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================
# CSS - APENAS MODO LIGHT
# =====================================================

st.markdown("""
<style>
/* Fundo geral */
html, body, [data-testid="stAppViewContainer"] {
    background: #f8fafc !important;
    color: #0f172a !important;
}

/* Remove efeitos escuros e barra superior */
header {
    background: transparent !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

/* Texto padrão */
p, label, div, span {
    color: #0f172a;
}

/* Título */
.hero {
    text-align: center;
    margin-top: 16px;
    margin-bottom: 26px;
}

.hero h1 {
    font-size: 2.5rem;
    margin-bottom: 6px;
    color: #0f172a;
}

.hero p {
    color: #64748b;
    font-size: 1rem;
}

/* Menu superior */
.top-menu-wrap {
    max-width: 1180px;
    margin: 0 auto 22px auto;
}

/* Cards iniciais */
.cards-wrapper {
    max-width: 980px;
    margin: 0 auto 28px auto;
}

.tool-card {
    background: #ffffff;
    border: 1px solid #dbeafe;
    border-radius: 18px;
    padding: 22px 18px;
    text-align: center;
    box-shadow: 0 10px 24px rgba(59, 130, 246, 0.08);
    min-height: 178px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.tool-title {
    font-size: 1.04rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 8px;
}

.tool-desc {
    font-size: 0.93rem;
    color: #64748b;
    line-height: 1.4;
    margin-bottom: 18px;
}

/* Painel da ferramenta */
.tool-panel {
    max-width: 900px;
    margin: 0 auto;
    background: #ffffff;
    border: 1px solid #dbeafe;
    border-radius: 20px;
    padding: 28px;
    box-shadow: 0 10px 24px rgba(59, 130, 246, 0.08);
}

.tool-panel h2 {
    text-align: center;
    color: #0f172a;
    margin-bottom: 20px;
}

/* Centralização dos inputs da ferramenta */
[data-testid="stFileUploader"],
.stTextInput,
.stNumberInput {
    max-width: 620px;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* Labels centralizadas */
label {
    text-align: center !important;
    display: block !important;
    width: 100% !important;
    color: #0f172a !important;
}

/* Upload */
[data-testid="stFileUploaderDropzone"] {
    background: #ffffff !important;
    border: 2px dashed #bfdbfe !important;
    border-radius: 16px !important;
}

[data-testid="stFileUploaderDropzoneInstructions"] div {
    visibility: hidden;
    position: relative;
}

[data-testid="stFileUploaderDropzoneInstructions"] div::before {
    content: "Arraste e solte os arquivos aqui";
    visibility: visible;
    position: absolute;
    inset: 0;
    text-align: center;
    color: #334155;
    font-weight: 500;
}

/* Botão do uploader */
[data-testid="stFileUploader"] section button {
    font-size: 0 !important;
    background: #eff6ff !important;
    color: #1d4ed8 !important;
    border: 1px solid #bfdbfe !important;
    border-radius: 10px !important;
}

[data-testid="stFileUploader"] section button::after {
    content: "Selecionar arquivos";
    font-size: 14px !important;
    color: #1d4ed8 !important;
    font-weight: 600;
}

/* Botões gerais */
.stButton {
    text-align: center !important;
}

.stButton > button {
    background: #3b82f6 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    box-shadow: 0 8px 18px rgba(59, 130, 246, 0.18) !important;
}

.stButton > button:hover {
    background: #2563eb !important;
    color: white !important;
}

/* Botões de download */
[data-testid="stDownloadButton"] {
    text-align: center !important;
}

[data-testid="stDownloadButton"] > button {
    background: #2563eb !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
}

/* Rodapé */
.footer-note {
    text-align: center;
    color: #64748b;
    margin-top: 28px;
    margin-bottom: 8px;
    font-size: 0.96rem;
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
    "imgpdf": "🖼️ Imagem para PDF",
}

DESCRIPTIONS = {
    "unlock": "Remova a senha de arquivos protegidos",
    "merge": "Combine vários PDFs em um único arquivo",
    "split": "Separe páginas de um PDF",
    "compress": "Reduza o tamanho do arquivo",
    "imgpdf": "Crie PDF a partir de imagens",
}

if "tool" not in st.session_state:
    st.session_state.tool = None

# =====================================================
# MENU SUPERIOR
# =====================================================

st.markdown('<div class="top-menu-wrap">', unsafe_allow_html=True)
menu_cols = st.columns(len(TOOLS))

for i, (key, name) in enumerate(TOOLS.items()):
    with menu_cols[i]:
        if st.button(name, key=f"top_{key}"):
            st.session_state.tool = key
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# TELA INICIAL
# =====================================================

if st.session_state.tool is None:
    st.markdown('<div class="cards-wrapper">', unsafe_allow_html=True)

    first_keys = list(TOOLS.keys())[:3]
    second_keys = list(TOOLS.keys())[3:]

    row1 = st.columns(3, gap="medium")
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

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    row2 = st.columns(2, gap="medium")
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

    st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# FUNÇÕES
# =====================================================

def unlock_pdf(pdf_bytes: bytes, password: str) -> bytes:
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


def merge_pdfs(files) -> bytes:
    writer = PdfWriter()
    for arquivo in files:
        reader = PdfReader(arquivo)
        for page in reader.pages:
            writer.add_page(page)

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def split_pdf(file, split_after: int):
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


def images_to_pdf(imagens) -> bytes:
    lista = []
    for img in imagens:
        image = Image.open(img).convert("RGB")
        lista.append(image)

    if not lista:
        raise ValueError("Envie pelo menos uma imagem.")

    buffer = io.BytesIO()
    lista[0].save(buffer, save_all=True, append_images=lista[1:], format="PDF")
    return buffer.getvalue()

# =====================================================
# FERRAMENTA SELECIONADA
# =====================================================

if st.session_state.tool is not None:
    back_cols = st.columns([1, 2, 1])
    with back_cols[1]:
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

        button_cols = st.columns([1, 1, 1])
        with button_cols[1]:
            desbloquear = st.button("Desbloquear PDFs", key="btn_unlock")

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

                    download_cols = st.columns([1, 1, 1])
                    with download_cols[1]:
                        st.download_button(
                            "Baixar todos",
                            zip_buffer.getvalue(),
                            "pdfs_desbloqueados.zip",
                            key="download_unlock_all"
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

        button_cols = st.columns([1, 1, 1])
        with button_cols[1]:
            juntar = st.button("Juntar PDFs", key="btn_merge")

        if juntar:
            if not arquivos:
                st.warning("Envie pelo menos um PDF.")
            else:
                buffer = merge_pdfs(arquivos)
                download_cols = st.columns([1, 1, 1])
                with download_cols[1]:
                    st.download_button(
                        "Baixar PDF unido",
                        buffer,
                        "pdf_unido.pdf",
                        key="download_merge"
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

                button_cols = st.columns([1, 1, 1])
                with button_cols[1]:
                    dividir = st.button("Dividir PDF", key="btn_split")

                if dividir:
                    parte1, parte2 = split_pdf(arquivo, pagina)

                    down1, down2 = st.columns(2)
                    with down1:
                        st.download_button("Baixar parte 1", parte1, "parte1.pdf", key="download_split_1")
                    with down2:
                        st.download_button("Baixar parte 2", parte2, "parte2.pdf", key="download_split_2")
            else:
                st.warning("O PDF precisa ter pelo menos 2 páginas.")

    # COMPRIMIR PDF
    elif st.session_state.tool == "compress":
        st.markdown("<h2>🗜️ Comprimir PDF</h2>", unsafe_allow_html=True)

        arquivo = st.file_uploader("Selecione o PDF", type="pdf", key="compress_file")

        button_cols = st.columns([1, 1, 1])
        with button_cols[1]:
            comprimir = st.button("Comprimir PDF", key="btn_compress")

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

                download_cols = st.columns([1, 1, 1])
                with download_cols[1]:
                    st.download_button(
                        "Baixar PDF comprimido",
                        buffer.getvalue(),
                        "pdf_comprimido.pdf",
                        key="download_compress"
                    )

    # IMAGEM PARA PDF
    elif st.session_state.tool == "imgpdf":
        st.markdown("<h2>🖼️ Imagem para PDF</h2>", unsafe_allow_html=True)

        imagens = st.file_uploader(
            "Envie imagens",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="imgpdf_files"
        )

        button_cols = st.columns([1, 1, 1])
        with button_cols[1]:
            converter = st.button("Converter em PDF", key="btn_imgpdf")

        if converter:
            if not imagens:
                st.warning("Envie pelo menos uma imagem.")
            else:
                pdf_bytes = images_to_pdf(imagens)

                download_cols = st.columns([1, 1, 1])
                with download_cols[1]:
                    st.download_button(
                        "Baixar PDF",
                        pdf_bytes,
                        "imagens.pdf",
                        key="download_imgpdf"
                    )

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="footer-note">Ferramentas PDF gratuitas online</div>', unsafe_allow_html=True)
