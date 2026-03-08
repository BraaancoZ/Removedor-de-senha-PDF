import io
import zipfile
from pathlib import Path
from typing import Dict, List

import fitz
import pandas as pd
import streamlit as st
from PIL import Image
from docx import Document
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from streamlit_sortables import sort_items


st.set_page_config(
    page_title="PDF Fácil",
    page_icon="📄",
    layout="wide",
)

# =====================================================
# CONFIG
# =====================================================

FEATURES = [
    "Sem instalação",
    "Funciona no celular",
    "Processamento rápido",
    "Gratuito"
]

MAIN_TOOLS = {
    "unlock": "🔓 Remover senha",
    "merge": "📎 Juntar PDFs",
    "split": "✂️ Dividir PDF",
    "reorganize": "🗂️ Reorganizar PDF",
    "compress": "🗜️ Comprimir PDF",
}

CONVERSION_TOOLS = {
    "imgpdf": "🖼️ JPG para PDF",
    "pdfjpg": "🖼️ PDF para JPG",
    "pdfword": "📄 PDF para Word",
    "wordpdf": "📄 Word para PDF",
}

if "tool" not in st.session_state:
    st.session_state.tool = None


# =====================================================
# HELPERS
# =====================================================

def base_name(filename: str):
    return Path(filename).stem


def with_ext(filename: str, ext: str):
    return f"{base_name(filename)}{ext}"


def unlock_pdf(pdf_bytes: bytes, password: str):
    reader = PdfReader(io.BytesIO(pdf_bytes))

    if reader.is_encrypted:
        reader.decrypt(password)

    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)

    return out.getvalue()


def merge_pdfs(files):
    writer = PdfWriter()

    for f in files:
        reader = PdfReader(io.BytesIO(f.getvalue()))
        for page in reader.pages:
            writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)

    return out.getvalue()


def split_pdf(file_bytes, split_page):
    reader = PdfReader(io.BytesIO(file_bytes))

    writer1 = PdfWriter()
    writer2 = PdfWriter()

    for i in range(split_page):
        writer1.add_page(reader.pages[i])

    for i in range(split_page, len(reader.pages)):
        writer2.add_page(reader.pages[i])

    out1 = io.BytesIO()
    out2 = io.BytesIO()

    writer1.write(out1)
    writer2.write(out2)

    return out1.getvalue(), out2.getvalue()


def compress_pdf_bytes(pdf_bytes):

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    out = io.BytesIO()

    doc.save(
        out,
        garbage=4,
        deflate=True,
        clean=True
    )

    doc.close()

    return out.getvalue()


def images_to_pdf(images):

    imgs = [Image.open(i).convert("RGB") for i in images]

    out = io.BytesIO()

    imgs[0].save(
        out,
        save_all=True,
        append_images=imgs[1:],
        format="PDF"
    )

    return out.getvalue()


def pdf_to_jpg_zip(pdf_bytes):

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:

        for i in range(len(doc)):
            page = doc.load_page(i)

            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

            img = Image.open(io.BytesIO(pix.tobytes("png")))

            img_bytes = io.BytesIO()

            img.save(img_bytes, format="JPEG", quality=90)

            zip_file.writestr(f"pagina_{i+1}.jpg", img_bytes.getvalue())

    return zip_buffer.getvalue()


def pdf_to_word(pdf_bytes):

    reader = PdfReader(io.BytesIO(pdf_bytes))

    doc = Document()

    for page in reader.pages:

        text = page.extract_text()

        if text:
            doc.add_paragraph(text)

    out = io.BytesIO()

    doc.save(out)

    return out.getvalue()


def docx_to_pdf(docx_bytes):

    doc = Document(io.BytesIO(docx_bytes))

    out = io.BytesIO()

    c = canvas.Canvas(out, pagesize=A4)

    y = 800

    for p in doc.paragraphs:

        c.drawString(50, y, p.text)

        y -= 20

        if y < 50:
            c.showPage()
            y = 800

    c.save()

    return out.getvalue()


# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>

body {
background:#f5f5f7;
}

.hero-card{
background:white;
padding:40px;
border-radius:20px;
text-align:center;
box-shadow:0 10px 25px rgba(0,0,0,0.05);
margin-bottom:30px;
}

.feature-chip{
display:inline-block;
padding:6px 12px;
background:#f2f2f2;
border-radius:20px;
margin:5px;
font-size:14px;
}

.tool-card{
background:white;
padding:25px;
border-radius:16px;
box-shadow:0 10px 25px rgba(0,0,0,0.05);
min-height:170px;
margin-bottom:20px;
}

.stButton>button{
background:#e5322d;
color:white;
border-radius:10px;
font-weight:700;
}

.stButton>button:hover{
background:#cc2420;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# HEADER
# =====================================================

feature_chips_html = "".join(
    [f'<div class="feature-chip">{f}</div>' for f in FEATURES]
)

hero_html = f"""
<div class="hero-card">
<h1>Edite, converta e organize PDFs em segundos</h1>
<p>Remova senha, junte PDFs, divida páginas e faça conversões direto no navegador.</p>
<div>{feature_chips_html}</div>
</div>
"""

st.markdown(hero_html, unsafe_allow_html=True)


# =====================================================
# HOME
# =====================================================

if st.session_state.tool is None:

    tools = list(MAIN_TOOLS.keys()) + list(CONVERSION_TOOLS.keys())

    rows = [tools[i:i+3] for i in range(0, len(tools), 3)]

    for row in rows:

        cols = st.columns(3)

        for col, tool in zip(cols, row):

            with col:

                label = MAIN_TOOLS.get(tool) or CONVERSION_TOOLS.get(tool)

                st.markdown(
                    f"""
                    <div class="tool-card">
                    <h4>{label}</h4>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button("Usar agora", key=tool):

                    st.session_state.tool = tool

                    st.rerun()


# =====================================================
# TOOLS
# =====================================================

tool = st.session_state.tool

if tool:

    if st.button("⬅ Voltar"):
        st.session_state.tool = None
        st.rerun()

    if tool == "unlock":

        files = st.file_uploader(
            "PDFs",
            type="pdf",
            accept_multiple_files=True
        )

        password = st.text_input("Senha", type="password")

        if st.button("Remover senha"):

            if len(files) == 1:

                pdf = unlock_pdf(files[0].getvalue(), password)

                st.download_button(
                    "Baixar PDF",
                    pdf,
                    files[0].name
                )

            else:

                zip_buffer = io.BytesIO()

                with zipfile.ZipFile(zip_buffer, "w") as zipf:

                    for f in files:

                        pdf = unlock_pdf(f.getvalue(), password)

                        zipf.writestr(f.name, pdf)

                st.download_button(
                    "Baixar ZIP",
                    zip_buffer.getvalue(),
                    "pdfs.zip"
                )

    elif tool == "merge":

        files = st.file_uploader(
            "PDFs",
            type="pdf",
            accept_multiple_files=True
        )

        if st.button("Juntar"):

            merged = merge_pdfs(files)

            st.download_button(
                "Baixar PDF",
                merged,
                "pdf_unido.pdf"
            )

    elif tool == "split":

        file = st.file_uploader("PDF", type="pdf")

        if file:

            reader = PdfReader(io.BytesIO(file.getvalue()))

            page = st.number_input(
                "Dividir após página",
                1,
                len(reader.pages)-1
            )

            if st.button("Dividir"):

                p1, p2 = split_pdf(file.getvalue(), page)

                st.download_button("Parte 1", p1, "parte1.pdf")

                st.download_button("Parte 2", p2, "parte2.pdf")

    elif tool == "compress":

        files = st.file_uploader(
            "PDFs",
            type="pdf",
            accept_multiple_files=True
        )

        if st.button("Comprimir"):

            if len(files) == 1:

                c = compress_pdf_bytes(files[0].getvalue())

                st.download_button("Baixar", c, files[0].name)

            else:

                zip_buffer = io.BytesIO()

                with zipfile.ZipFile(zip_buffer, "w") as zipf:

                    for f in files:

                        c = compress_pdf_bytes(f.getvalue())

                        zipf.writestr(f.name, c)

                st.download_button(
                    "Baixar ZIP",
                    zip_buffer.getvalue(),
                    "pdfs.zip"
                )

    elif tool == "imgpdf":

        imgs = st.file_uploader(
            "Imagens",
            type=["jpg","png"],
            accept_multiple_files=True
        )

        if st.button("Converter"):

            pdf = images_to_pdf(imgs)

            st.download_button(
                "Baixar PDF",
                pdf,
                "imagens.pdf"
            )

    elif tool == "pdfjpg":

        file = st.file_uploader("PDF", type="pdf")

        if st.button("Converter"):

            zip_bytes = pdf_to_jpg_zip(file.getvalue())

            st.download_button(
                "Baixar ZIP",
                zip_bytes,
                "imagens.zip"
            )

    elif tool == "pdfword":

        file = st.file_uploader("PDF", type="pdf")

        if st.button("Converter"):

            docx = pdf_to_word(file.getvalue())

            st.download_button(
                "Baixar Word",
                docx,
                "arquivo.docx"
            )

    elif tool == "wordpdf":

        file = st.file_uploader("DOCX", type="docx")

        if st.button("Converter"):

            pdf = docx_to_pdf(file.getvalue())

            st.download_button(
                "Baixar PDF",
                pdf,
                "arquivo.pdf"
            )
