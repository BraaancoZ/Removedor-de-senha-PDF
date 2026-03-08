import io
import os
import time
import zipfile
from typing import List, Tuple

import fitz  # PyMuPDF
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from pypdf import PdfReader, PdfWriter
from streamlit_sortables import sort_items

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="PDF Fácil",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

TOOLS = [
    "🔓 Remover senha",
    "📎 Juntar PDFs",
    "✂️ Dividir PDF",
    "🗜️ Comprimir PDF",
    "🖼️ PDF para imagem",
    "🖼️ Imagem para PDF",
]

if "selected_tool" not in st.session_state:
    st.session_state.selected_tool = TOOLS[0]

# =========================================================
# ANALYTICS
# =========================================================

def inject_google_analytics():
    ga_id = ""
    try:
        ga_id = st.secrets.get("GOOGLE_ANALYTICS_ID", "")
    except Exception:
        ga_id = os.getenv("GOOGLE_ANALYTICS_ID", "")

    if not ga_id:
        return

    components.html(
        f"""
        <script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          gtag('js', new Date());
          gtag('config', '{ga_id}', {{
            page_path: window.parent.location.pathname
          }});
        </script>
        """,
        height=0,
        width=0,
    )

inject_google_analytics()

# =========================================================
# ESTILO
# =========================================================

st.markdown(
    """
<style>
:root {
    --bg: #f6f8fc;
    --bg-2: #eef2ff;
    --card: #ffffff;
    --text: #111827;
    --muted: #6b7280;
    --primary: #e5322d;
    --primary-hover: #c92b27;
    --border: #e5e7eb;
    --shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
    --radius: 22px;
    --upload-bg: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg: #0b1220;
        --bg-2: #111827;
        --card: rgba(17, 24, 39, 0.92);
        --text: #f9fafb;
        --muted: #cbd5e1;
        --primary: #ef4444;
        --primary-hover: #dc2626;
        --border: rgba(148, 163, 184, 0.22);
        --shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
        --upload-bg: linear-gradient(180deg, rgba(30,41,59,.92) 0%, rgba(15,23,42,.96) 100%);
    }
}

html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, var(--bg) 0%, var(--bg-2) 100%);
    color: var(--text);
}

[data-testid="stSidebar"] {
    background: var(--card);
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

.block-container {
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}

.hero {
    max-width: 960px;
    margin: 0 auto 1.4rem auto;
    text-align: center;
    animation: fadeUp .55s ease-out;
}

.logo-badge {
    width: 74px;
    height: 74px;
    margin: 0 auto 14px auto;
    border-radius: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    background: linear-gradient(135deg, #ef4444 0%, #e5322d 100%);
    box-shadow: 0 14px 32px rgba(229, 50, 45, 0.28);
}

.hero h1 {
    font-size: 2.7rem;
    line-height: 1.1;
    margin-bottom: .35rem;
    color: var(--text);
    font-weight: 800;
    letter-spacing: -0.03em;
    text-align: center !important;
}

.hero p {
    margin: 0 auto;
    max-width: 760px;
    color: var(--muted);
    font-size: 1.08rem;
    text-align: center !important;
}

.center-wrap {
    max-width: 820px;
    margin: 0 auto;
    animation: fadeUp .65s ease-out;
}

.card {
    background: var(--card);
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
    border-radius: var(--radius);
    padding: 1.25rem 1.2rem;
    margin-bottom: 1rem;
}

.card h2, .card h3, .card p, .card div {
    color: var(--text);
}

.card h2, .card h3 {
    text-align: center;
    margin-top: .15rem;
}

.helper {
    color: var(--muted);
    text-align: center;
    margin-top: -.25rem;
    margin-bottom: 1rem;
}

.small-center {
    text-align: center;
    color: var(--muted);
    font-size: .95rem;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin: 1rem auto 1.35rem auto;
    max-width: 900px;
}

.kpi {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 18px;
    box-shadow: var(--shadow);
    padding: 1rem;
    text-align: center;
    animation: fadeUp .75s ease-out;
}

.kpi .icon {
    font-size: 1.35rem;
    margin-bottom: .35rem;
}

.kpi .title {
    font-size: .95rem;
    color: var(--muted);
}

.kpi .value {
    font-size: 1.03rem;
    font-weight: 700;
    color: var(--text);
}

.tool-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
    margin: 0 auto 1.4rem auto;
    max-width: 980px;
}

.tool-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 20px;
    box-shadow: var(--shadow);
    padding: 1rem;
    text-align: center;
    animation: fadeUp .85s ease-out;
}

.tool-icon {
    font-size: 1.9rem;
    margin-bottom: .55rem;
}

.tool-title {
    font-weight: 800;
    margin-bottom: .2rem;
    color: var(--text);
}

.tool-desc {
    color: var(--muted);
    font-size: .95rem;
    min-height: 42px;
    margin-bottom: .75rem;
}

.stTextInput, .stNumberInput, .stSelectbox, .stMultiSelect, .stSlider {
    max-width: 560px;
    margin-left: auto;
    margin-right: auto;
}

[data-testid="stFileUploader"] {
    max-width: 560px;
    margin-left: auto;
    margin-right: auto;
}

[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed #cbd5e1 !important;
    border-radius: 18px !important;
    background: var(--upload-bg) !important;
    padding: 1.2rem !important;
    transition: all .25s ease;
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #94a3b8 !important;
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(15, 23, 42, .10);
}

/* Traduz o texto principal do uploader */
[data-testid="stFileUploaderDropzoneInstructions"] div {
    visibility: hidden;
    position: relative;
}

[data-testid="stFileUploaderDropzoneInstructions"] div::before {
    content: "Arraste e solte os arquivos aqui";
    visibility: visible;
    position: absolute;
    inset: 0;
    color: var(--text);
    text-align: center;
    font-weight: 600;
}

/* Traduz o botão Browse files */
[data-testid="stFileUploader"] section button {
    font-size: 0 !important;
}

[data-testid="stFileUploader"] section button::after {
    content: "Selecionar arquivos";
    font-size: 0.96rem !important;
    color: var(--text);
    font-weight: 600;
}

/* Centraliza labels e inputs */
label, .stTextInput label, .stNumberInput label, .stSelectbox label, .stMultiSelect label {
    text-align: center !important;
    width: 100%;
    display: block;
    color: var(--text) !important;
}

.stButton, [data-testid="stDownloadButton"] {
    text-align: center;
}

.stButton > button,
[data-testid="stDownloadButton"] > button {
    background: var(--primary);
    color: white !important;
    border: none;
    border-radius: 14px;
    padding: .82rem 1.2rem;
    font-weight: 700;
    transition: all .2s ease;
    box-shadow: 0 10px 20px rgba(229, 50, 45, .18);
}

.stButton > button:hover,
[data-testid="stDownloadButton"] > button:hover {
    background: var(--primary-hover);
    transform: translateY(-1px);
}

.sort-box {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1rem;
    box-shadow: var(--shadow);
}

.preview-title {
    text-align: center;
    font-weight: 700;
    margin-top: .5rem;
    margin-bottom: .75rem;
    color: var(--text);
}

.footer-note {
    text-align: center;
    color: var(--muted);
    margin-top: 1.2rem;
    font-size: .95rem;
}

hr {
    border-color: var(--border) !important;
}

@keyframes fadeUp {
    from {
        opacity: 0;
        transform: translateY(14px);
    }
    to {
        opacity: 1;
        transform: translateY(0px);
    }
}

@media (max-width: 900px) {
    .tool-grid {
        grid-template-columns: 1fr;
    }
    .kpi-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .hero h1 {
        font-size: 2rem;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# HELPERS
# =========================================================

def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} GB"


def get_pdf_preview_images(pdf_bytes: bytes, max_pages: int = 4, dpi: int = 110) -> List[Image.Image]:
    images = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total = min(len(doc), max_pages)
    for i in range(total):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        images.append(img)
    doc.close()
    return images


def remove_password_from_pdf(pdf_bytes: bytes, password: str) -> bytes:
    reader = PdfReader(io.BytesIO(pdf_bytes))

    if reader.is_encrypted:
        decrypt_result = reader.decrypt(password)
        if decrypt_result == 0:
            raise ValueError("Senha incorreta.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def merge_pdfs(files_ordered: List[Tuple[str, bytes]]) -> bytes:
    writer = PdfWriter()
    for _, file_bytes in files_ordered:
        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def split_pdf(pdf_bytes: bytes, split_after_page: int) -> Tuple[bytes, bytes]:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer1 = PdfWriter()
    writer2 = PdfWriter()

    for i in range(split_after_page):
        writer1.add_page(reader.pages[i])
    for i in range(split_after_page, len(reader.pages)):
        writer2.add_page(reader.pages[i])

    out1 = io.BytesIO()
    out2 = io.BytesIO()
    writer1.write(out1)
    writer2.write(out2)
    return out1.getvalue(), out2.getvalue()


def compress_pdf_bytes(pdf_bytes: bytes) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    output = io.BytesIO()
    doc.save(
        output,
        garbage=4,
        deflate=True,
        clean=True,
        use_objstms=1,
    )
    doc.close()
    return output.getvalue()


def pdf_to_png_zip(pdf_bytes: bytes, dpi: int = 150) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
            img_bytes = pix.tobytes("png")
            zip_file.writestr(f"pagina_{i+1}.png", img_bytes)

    doc.close()
    return zip_buffer.getvalue()


def images_to_pdf(image_files) -> bytes:
    images = []
    for file in image_files:
        image = Image.open(file).convert("RGB")
        images.append(image)

    if not images:
        raise ValueError("Nenhuma imagem enviada.")

    output = io.BytesIO()
    images[0].save(output, save_all=True, append_images=images[1:], format="PDF")
    return output.getvalue()


def animated_progress(task_text: str, seconds: float = 0.8):
    status = st.empty()
    progress = st.progress(0)
    steps = 24
    for i in range(steps):
        status.markdown(f"<div class='small-center'>{task_text}</div>", unsafe_allow_html=True)
        progress.progress((i + 1) / steps)
        time.sleep(seconds / steps)
    status.empty()
    progress.empty()


def select_tool(tool_name: str):
    st.session_state.selected_tool = tool_name
    st.session_state.tool_radio = tool_name


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown("## 📄 PDF Fácil")
selected_tool = st.sidebar.radio(
    "Escolha uma ferramenta",
    TOOLS,
    index=TOOLS.index(st.session_state.selected_tool),
    key="tool_radio",
)
st.session_state.selected_tool = selected_tool

st.sidebar.markdown("---")
st.sidebar.caption("Rápido, bonito e pronto para celular.")

# =========================================================
# HERO
# =========================================================

st.markdown(
    """
<div class="hero">
    <div class="logo-badge">📄</div>
    <h1>PDF Fácil</h1>
    <p>Ferramentas simples para editar PDFs diretamente no navegador</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="kpi-grid">
    <div class="kpi">
        <div class="icon">🔐</div>
        <div class="title">Desbloqueio</div>
        <div class="value">1 ou vários arquivos</div>
    </div>
    <div class="kpi">
        <div class="icon">⚡</div>
        <div class="title">Uso rápido</div>
        <div class="value">Interface centralizada</div>
    </div>
    <div class="kpi">
        <div class="icon">🖼️</div>
        <div class="title">Conversões</div>
        <div class="value">PDF e imagens</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# =========================================================
# CARDS HOME
# =========================================================

tool_info = [
    ("🔓 Remover senha", "Desbloqueie um ou vários PDFs protegidos."),
    ("📎 Juntar PDFs", "Una vários arquivos em um único PDF."),
    ("✂️ Dividir PDF", "Separe um PDF em duas partes."),
    ("🗜️ Comprimir PDF", "Reduza o tamanho do arquivo."),
    ("🖼️ PDF para imagem", "Converta páginas em PNG."),
    ("🖼️ Imagem para PDF", "Transforme imagens em PDF."),
]

st.markdown('<div class="tool-grid">', unsafe_allow_html=True)
cols = st.columns(3)
for idx, (title, desc) in enumerate(tool_info):
    with cols[idx % 3]:
        st.markdown(
            f"""
            <div class="tool-card">
                <div class="tool-icon">{title.split()[0]}</div>
                <div class="tool-title">{title}</div>
                <div class="tool-desc">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Usar agora", key=f"use_{idx}"):
            select_tool(title)
            st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

menu = st.session_state.selected_tool

# =========================================================
# REMOVER SENHA
# =========================================================

if menu == "🔓 Remover senha":
    st.markdown('<div class="center-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2>🔓 Remover senha de PDF</h2>", unsafe_allow_html=True)
    st.markdown(
        '<div class="helper">Envie um ou mais PDFs protegidos, informe a senha e baixe tudo de uma vez.</div>',
        unsafe_allow_html=True,
    )

    arquivos = st.file_uploader(
        "Arraste e solte os arquivos aqui",
        type=["pdf"],
        accept_multiple_files=True,
        help="Você também pode clicar para selecionar os arquivos.",
        key="unlock_files",
    )

    senha = st.text_input("Digite a senha do PDF", type="password")

    if arquivos:
        st.markdown('<div class="preview-title">Preview das primeiras páginas</div>', unsafe_allow_html=True)
        preview_cols = st.columns(min(3, len(arquivos)))
        for idx, arquivo in enumerate(arquivos[:3]):
            pdf_bytes = arquivo.getvalue()
            previews = get_pdf_preview_images(pdf_bytes, max_pages=1)
            with preview_cols[idx % len(preview_cols)]:
                st.image(previews[0], caption=arquivo.name, use_container_width=True)

    if st.button("Desbloquear PDFs"):
        if not arquivos:
            st.warning("Envie pelo menos um PDF.")
        elif not senha:
            st.warning("Digite a senha do PDF.")
        else:
            arquivos_processados = []
            errors = []

            animated_progress("Processando arquivos...", seconds=1.0)

            for arquivo in arquivos:
                try:
                    original_name = os.path.basename(arquivo.name)
                    unlocked_bytes = remove_password_from_pdf(arquivo.getvalue(), senha)
                    arquivos_processados.append((original_name, unlocked_bytes))
                except Exception:
                    errors.append(arquivo.name)

            if arquivos_processados:
                st.success("Processamento concluído.")

                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for nome, data in arquivos_processados:
                        zip_file.writestr(nome, data)

                st.download_button(
                    "📦 Baixar todos os PDFs de uma vez",
                    data=zip_buffer.getvalue(),
                    file_name="pdfs_desbloqueados.zip",
                    mime="application/zip",
                )

                for nome, data in arquivos_processados:
                    st.download_button(
                        f"Baixar {nome}",
                        data=data,
                        file_name=nome,
                        mime="application/pdf",
                        key=f"download_unlock_{nome}",
                    )

            if errors:
                st.error("Não foi possível processar: " + ", ".join(errors))

    st.markdown("</div></div>", unsafe_allow_html=True)

# =========================================================
# JUNTAR PDFs
# =========================================================

elif menu == "📎 Juntar PDFs":
    st.markdown('<div class="center-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2>📎 Juntar PDFs</h2>", unsafe_allow_html=True)
    st.markdown(
        '<div class="helper">Envie os arquivos, arraste para reorganizar a ordem e gere um único PDF.</div>',
        unsafe_allow_html=True,
    )

    arquivos = st.file_uploader(
        "Arraste e solte os arquivos aqui",
        type=["pdf"],
        accept_multiple_files=True,
        key="merge_uploader",
    )

    if arquivos:
        file_map = {arq.name: arq.getvalue() for arq in arquivos}

        st.markdown('<div class="preview-title">Arraste para definir a ordem</div>', unsafe_allow_html=True)
        st.markdown('<div class="sort-box">', unsafe_allow_html=True)
        ordered_names = sort_items(
            [arq.name for arq in arquivos],
            direction="vertical",
            key="sortable_merge",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="preview-title">Preview</div>', unsafe_allow_html=True)
        cols = st.columns(min(3, len(ordered_names)))
        for idx, nome in enumerate(ordered_names[:3]):
            previews = get_pdf_preview_images(file_map[nome], max_pages=1)
            with cols[idx % len(cols)]:
                st.image(previews[0], caption=nome, use_container_width=True)

        if st.button("Juntar PDFs"):
            animated_progress("Unindo arquivos...", seconds=0.9)
            ordered_files = [(nome, file_map[nome]) for nome in ordered_names]
            merged_bytes = merge_pdfs(ordered_files)

            st.success("PDF unido com sucesso.")
            st.download_button(
                "📥 Baixar PDF unido",
                data=merged_bytes,
                file_name="pdf_unido.pdf",
                mime="application/pdf",
            )

    st.markdown("</div></div>", unsafe_allow_html=True)

# =========================================================
# DIVIDIR PDF
# =========================================================

elif menu == "✂️ Dividir PDF":
    st.markdown('<div class="center-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2>✂️ Dividir PDF</h2>", unsafe_allow_html=True)
    st.markdown(
        '<div class="helper">Escolha um ponto de divisão e baixe as duas partes separadamente.</div>',
        unsafe_allow_html=True,
    )

    arquivo = st.file_uploader("Arraste e solte o arquivo aqui", type=["pdf"], key="split_pdf")

    if arquivo:
        pdf_bytes = arquivo.getvalue()
        reader = PdfReader(io.BytesIO(pdf_bytes))
        total_paginas = len(reader.pages)

        previews = get_pdf_preview_images(pdf_bytes, max_pages=3)
        cols = st.columns(len(previews))
        for i, img in enumerate(previews):
            with cols[i]:
                st.image(img, caption=f"Página {i+1}", use_container_width=True)

        pagina = st.number_input(
            "Dividir após a página",
            min_value=1,
            max_value=total_paginas - 1,
            value=1,
            step=1,
        )

        if st.button("Dividir PDF"):
            animated_progress("Dividindo arquivo...", seconds=0.7)
            parte1, parte2 = split_pdf(pdf_bytes, pagina)

            st.success("PDF dividido com sucesso.")
            st.download_button("📥 Baixar parte 1", parte1, "parte_1.pdf", mime="application/pdf")
            st.download_button("📥 Baixar parte 2", parte2, "parte_2.pdf", mime="application/pdf")

    st.markdown("</div></div>", unsafe_allow_html=True)

# =========================================================
# COMPRIMIR PDF
# =========================================================

elif menu == "🗜️ Comprimir PDF":
    st.markdown('<div class="center-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2>🗜️ Comprimir PDF</h2>", unsafe_allow_html=True)
    st.markdown(
        '<div class="helper">Reduza o tamanho do arquivo mantendo o formato PDF.</div>',
        unsafe_allow_html=True,
    )

    arquivo = st.file_uploader("Arraste e solte o arquivo aqui", type=["pdf"], key="compress_pdf")

    if arquivo:
        original_bytes = arquivo.getvalue()
        st.markdown(
            f"<div class='small-center'>Tamanho original: <strong>{human_size(len(original_bytes))}</strong></div>",
            unsafe_allow_html=True,
        )

        previews = get_pdf_preview_images(original_bytes, max_pages=2)
        cols = st.columns(len(previews))
        for i, img in enumerate(previews):
            with cols[i]:
                st.image(img, caption=f"Preview {i+1}", use_container_width=True)

        if st.button("Comprimir PDF"):
            animated_progress("Comprimindo arquivo...", seconds=1.0)
            compressed = compress_pdf_bytes(original_bytes)

            reduction = 0
            if len(original_bytes) > 0:
                reduction = (1 - (len(compressed) / len(original_bytes))) * 100

            st.success("Compressão concluída.")
            st.markdown(
                f"<div class='small-center'>Novo tamanho: <strong>{human_size(len(compressed))}</strong> | Redução aproximada: <strong>{reduction:.1f}%</strong></div>",
                unsafe_allow_html=True,
            )

            st.download_button(
                "📥 Baixar PDF comprimido",
                compressed,
                "pdf_comprimido.pdf",
                mime="application/pdf",
            )

    st.markdown("</div></div>", unsafe_allow_html=True)

# =========================================================
# PDF PARA IMAGEM
# =========================================================

elif menu == "🖼️ PDF para imagem":
    st.markdown('<div class="center-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2>🖼️ PDF para imagem</h2>", unsafe_allow_html=True)
    st.markdown(
        '<div class="helper">Converta as páginas do PDF em imagens PNG e baixe tudo em ZIP.</div>',
        unsafe_allow_html=True,
    )

    arquivo = st.file_uploader("Arraste e solte o arquivo aqui", type=["pdf"], key="pdf_to_img")

    if arquivo:
        pdf_bytes = arquivo.getvalue()
        previews = get_pdf_preview_images(pdf_bytes, max_pages=4)
        cols = st.columns(min(2, len(previews)) if previews else 1)
        for idx, img in enumerate(previews):
            with cols[idx % len(cols)]:
                st.image(img, caption=f"Página {idx+1}", use_container_width=True)

        if st.button("Converter PDF para imagens"):
            animated_progress("Convertendo páginas...", seconds=1.0)
            zip_png = pdf_to_png_zip(pdf_bytes)

            st.success("Conversão concluída.")
            st.download_button(
                "📥 Baixar imagens em ZIP",
                zip_png,
                "pdf_para_imagens.zip",
                mime="application/zip",
            )

    st.markdown("</div></div>", unsafe_allow_html=True)

# =========================================================
# IMAGEM PARA PDF
# =========================================================

elif menu == "🖼️ Imagem para PDF":
    st.markdown('<div class="center-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2>🖼️ Imagem para PDF</h2>", unsafe_allow_html=True)
    st.markdown(
        '<div class="helper">Envie imagens JPG ou PNG e gere um único PDF.</div>',
        unsafe_allow_html=True,
    )

    imagens = st.file_uploader(
        "Arraste e solte os arquivos aqui",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="img_to_pdf",
    )

    if imagens:
        cols = st.columns(min(3, len(imagens)))
        for idx, img_file in enumerate(imagens[:3]):
            with cols[idx % len(cols)]:
                st.image(img_file, caption=img_file.name, use_container_width=True)

        if st.button("Converter imagens para PDF"):
            animated_progress("Montando PDF...", seconds=0.9)
            pdf_bytes = images_to_pdf(imagens)

            st.success("PDF criado com sucesso.")
            st.download_button(
                "📥 Baixar PDF",
                pdf_bytes,
                "imagens_convertidas.pdf",
                mime="application/pdf",
            )

    st.markdown("</div></div>", unsafe_allow_html=True)

st.markdown('<div class="footer-note">Ferramentas PDF gratuitas online</div>', unsafe_allow_html=True)
