import io
import os
import time
import zipfile
from typing import List, Tuple

import fitz  # PyMuPDF
import streamlit as st
from PIL import Image
from pypdf import PdfReader, PdfWriter
from streamlit_sortables import sort_items

st.set_page_config(
    page_title="Ferramentas PDF",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# ESTILO
# =========================================================

st.markdown(
    """
<style>
:root {
    --bg: #f6f8fc;
    --card: #ffffff;
    --text: #1f2937;
    --muted: #6b7280;
    --primary: #e5322d;
    --primary-hover: #c92b27;
    --border: #e5e7eb;
    --shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
    --radius: 20px;
}

html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
    color: var(--text);
}

[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid var(--border);
}

.block-container {
    padding-top: 1.8rem;
    padding-bottom: 3rem;
}

.hero {
    max-width: 860px;
    margin: 0 auto 1.2rem auto;
    text-align: center;
    animation: fadeUp .55s ease-out;
}

.hero h1 {
    font-size: 2.5rem;
    line-height: 1.1;
    margin-bottom: .35rem;
    color: #111827;
    font-weight: 800;
    letter-spacing: -0.02em;
}

.hero p {
    margin: 0 auto;
    max-width: 760px;
    color: var(--muted);
    font-size: 1.08rem;
    text-align: center !important;
}

.center-wrap {
    max-width: 760px;
    margin: 0 auto;
    animation: fadeUp .65s ease-out;
}

.card {
    background: var(--card);
    border: 1px solid rgba(229,231,235,.9);
    box-shadow: var(--shadow);
    border-radius: var(--radius);
    padding: 1.25rem 1.2rem;
    margin-bottom: 1rem;
}

.card h2, .card h3 {
    text-align: center;
    margin-top: .15rem;
    color: #111827;
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

.stTextInput, .stNumberInput, .stSelectbox, .stMultiSelect {
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
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
    padding: 1.2rem !important;
    transition: all .25s ease;
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #94a3b8 !important;
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(15, 23, 42, .08);
}

.stButton {
    text-align: center;
}

.stButton > button {
    background: var(--primary);
    color: white;
    border: none;
    border-radius: 14px;
    padding: .82rem 1.2rem;
    font-weight: 700;
    transition: all .2s ease;
    box-shadow: 0 10px 20px rgba(229, 50, 45, .18);
}

.stButton > button:hover {
    background: var(--primary-hover);
    transform: translateY(-1px);
}

[data-testid="stDownloadButton"] {
    text-align: center;
}

[data-testid="stDownloadButton"] > button {
    border-radius: 12px;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin: 1rem auto 1.25rem auto;
    max-width: 860px;
}

.kpi {
    background: rgba(255,255,255,.75);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(229,231,235,.95);
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
    color: #111827;
}

.sort-box {
    background: #fff;
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
}

.footer-note {
    text-align: center;
    color: var(--muted);
    margin-top: 1.2rem;
    font-size: .95rem;
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

@media (max-width: 768px) {
    .hero h1 {
        font-size: 2rem;
    }
    .kpi-grid {
        grid-template-columns: 1fr;
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
    # Compressão mais forte usando PyMuPDF
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
    steps = 20
    for i in range(steps):
        status.markdown(f"<div class='small-center'>{task_text}</div>", unsafe_allow_html=True)
        progress.progress((i + 1) / steps)
        time.sleep(seconds / steps)
    status.empty()
    progress.empty()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown("## 📄 Ferramentas PDF")
menu = st.sidebar.radio(
    "Escolha uma ferramenta",
    [
        "🔓 Remover senha",
        "📎 Juntar PDFs",
        "✂️ Dividir PDF",
        "🗜️ Comprimir PDF",
        "🖼️ PDF para imagem",
        "🖼️ Imagem para PDF",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption("Rápido, simples e pronto para celular.")

# =========================================================
# HERO
# =========================================================

st.markdown(
    """
<div class="hero">
    <h1>Ferramentas PDF Online</h1>
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
        "Arraste e solte os PDFs aqui",
        type=["pdf"],
        accept_multiple_files=True,
        help="Você também pode clicar para selecionar os arquivos.",
    )

    st.markdown(
        """
        <div class="small-center" style="margin-top:-8px; margin-bottom:14px;">
            Selecionar arquivos PDF
        </div>
        """,
        unsafe_allow_html=True,
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

    if st.button("Desbloquear PDFs", use_container_width=False):
        if not arquivos:
            st.warning("Envie pelo menos um PDF.")
        elif not senha:
            st.warning("Digite a senha do PDF.")
        else:
            arquivos_processados = []
            errors = []

            try:
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
                        )

                if errors:
                    st.error("Não foi possível processar: " + ", ".join(errors))

            except Exception as e:
                st.error(f"Erro ao processar os arquivos: {e}")

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
        "Arraste e solte os PDFs aqui",
        type=["pdf"],
        accept_multiple_files=True,
        key="merge_uploader",
    )

    st.markdown(
        """
        <div class="small-center" style="margin-top:-8px; margin-bottom:14px;">
            Selecionar arquivos PDF
        </div>
        """,
        unsafe_allow_html=True,
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
            try:
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
            except Exception as e:
                st.error(f"Erro ao juntar PDFs: {e}")

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

    arquivo = st.file_uploader("Arraste e solte o PDF aqui", type=["pdf"], key="split_pdf")

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
            try:
                animated_progress("Dividindo arquivo...", seconds=0.7)
                parte1, parte2 = split_pdf(pdf_bytes, pagina)

                st.success("PDF dividido com sucesso.")
                st.download_button("📥 Baixar parte 1", parte1, "parte_1.pdf", mime="application/pdf")
                st.download_button("📥 Baixar parte 2", parte2, "parte_2.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Erro ao dividir PDF: {e}")

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

    arquivo = st.file_uploader("Arraste e solte o PDF aqui", type=["pdf"], key="compress_pdf")

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
            try:
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
            except Exception as e:
                st.error(f"Erro ao comprimir PDF: {e}")

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

    arquivo = st.file_uploader("Arraste e solte o PDF aqui", type=["pdf"], key="pdf_to_img")

    if arquivo:
        pdf_bytes = arquivo.getvalue()
        previews = get_pdf_preview_images(pdf_bytes, max_pages=4)
        cols = st.columns(min(2, len(previews)) if previews else 1)
        for idx, img in enumerate(previews):
            with cols[idx % len(cols)]:
                st.image(img, caption=f"Página {idx+1}", use_container_width=True)

        if st.button("Converter PDF para imagens"):
            try:
                animated_progress("Convertendo páginas...", seconds=1.0)
                zip_png = pdf_to_png_zip(pdf_bytes)

                st.success("Conversão concluída.")
                st.download_button(
                    "📥 Baixar imagens em ZIP",
                    zip_png,
                    "pdf_para_imagens.zip",
                    mime="application/zip",
                )
            except Exception as e:
                st.error(f"Erro ao converter PDF para imagem: {e}")

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
        "Arraste e solte as imagens aqui",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="img_to_pdf",
    )

    st.markdown(
        """
        <div class="small-center" style="margin-top:-8px; margin-bottom:14px;">
            Selecionar arquivos de imagem
        </div>
        """,
        unsafe_allow_html=True,
    )

    if imagens:
        cols = st.columns(min(3, len(imagens)))
        for idx, img_file in enumerate(imagens[:3]):
            with cols[idx % len(cols)]:
                st.image(img_file, caption=img_file.name, use_container_width=True)

        if st.button("Converter imagens para PDF"):
            try:
                animated_progress("Montando PDF...", seconds=0.9)
                pdf_bytes = images_to_pdf(imagens)

                st.success("PDF criado com sucesso.")
                st.download_button(
                    "📥 Baixar PDF",
                    pdf_bytes,
                    "imagens_convertidas.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"Erro ao converter imagens para PDF: {e}")

    st.markdown("</div></div>", unsafe_allow_html=True)

st.markdown('<div class="footer-note">Ferramentas PDF gratuitas online</div>', unsafe_allow_html=True)
