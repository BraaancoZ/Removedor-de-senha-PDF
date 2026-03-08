import io
import zipfile
from pathlib import Path
from typing import Dict, List

import fitz  # PyMuPDF
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
    initial_sidebar_state="expanded",
)

# =====================================================
# HELPERS
# =====================================================

def base_name(filename: str) -> str:
    return Path(filename).stem

def with_ext(filename: str, new_ext: str) -> str:
    return f"{base_name(filename)}{new_ext}"

def with_suffix(filename: str, suffix: str, ext: str = None) -> str:
    stem = base_name(filename)
    if ext is None:
        ext = Path(filename).suffix or ""
    return f"{stem}{suffix}{ext}"

def chunk_list(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]

def unlock_pdf(pdf_bytes: bytes, password: str) -> bytes:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    if reader.is_encrypted:
        result = reader.decrypt(password)
        if result == 0:
            raise ValueError("Senha incorreta.")
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()

def merge_pdfs_from_plan(page_plan: pd.DataFrame, file_bytes_map: Dict[str, bytes]) -> bytes:
    writer = PdfWriter()
    plan = page_plan.sort_values("ordem")
    selected = plan[plan["incluir"] == True]

    for _, row in selected.iterrows():
        reader = PdfReader(io.BytesIO(file_bytes_map[row["arquivo"]]))
        writer.add_page(reader.pages[int(row["pagina_pdf"]) - 1])

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()

def split_pdf(file_bytes: bytes, split_after: int):
    reader = PdfReader(io.BytesIO(file_bytes))
    writer1 = PdfWriter()
    writer2 = PdfWriter()

    for i in range(split_after):
        writer1.add_page(reader.pages[i])

    for i in range(split_after, len(reader.pages)):
        writer2.add_page(reader.pages[i])

    out1 = io.BytesIO()
    out2 = io.BytesIO()
    writer1.write(out1)
    writer2.write(out2)
    return out1.getvalue(), out2.getvalue()

def rebuild_pdf_from_plan(page_plan: pd.DataFrame, file_bytes_map: Dict[str, bytes]) -> bytes:
    return merge_pdfs_from_plan(page_plan, file_bytes_map)

def compress_pdf_bytes(pdf_bytes: bytes) -> bytes:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()

def images_to_pdf(image_files) -> bytes:
    images = []
    for img in image_files:
        image = Image.open(img).convert("RGB")
        images.append(image)

    if not images:
        raise ValueError("Envie pelo menos uma imagem.")

    out = io.BytesIO()
    images[0].save(out, save_all=True, append_images=images[1:], format="PDF")
    return out.getvalue()

def pdf_to_jpg_zip(pdf_bytes: bytes, quality: int = 90) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="JPEG", quality=quality)
            zip_file.writestr(f"pagina_{i+1}.jpg", img_buffer.getvalue())

    doc.close()
    return zip_buffer.getvalue()

def pdf_text_to_docx(pdf_bytes: bytes) -> bytes:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    doc = Document()

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if i > 0:
            doc.add_page_break()
        doc.add_heading(f"Página {i+1}", level=1)
        for bloco in text.split("\n"):
            bloco = bloco.strip()
            if bloco:
                doc.add_paragraph(bloco)

    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()

def wrap_text_for_pdf(text: str, max_chars: int = 95) -> List[str]:
    words = text.split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = current + " " + word
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines

def docx_to_simple_pdf(docx_bytes: bytes) -> bytes:
    document = Document(io.BytesIO(docx_bytes))
    out = io.BytesIO()
    c = canvas.Canvas(out, pagesize=A4)
    width, height = A4
    x = 50
    y = height - 50
    line_height = 16

    for para in document.paragraphs:
        text = para.text.strip()
        if not text:
            y -= line_height
        else:
            chunks = wrap_text_for_pdf(text, max_chars=95)
            for chunk in chunks:
                if y < 50:
                    c.showPage()
                    y = height - 50
                c.drawString(x, y, chunk)
                y -= line_height

    c.save()
    return out.getvalue()

def get_pdf_thumbnail(pdf_bytes: bytes, page_number: int, zoom: float = 0.60):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(page_number)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    doc.close()
    return img

def build_merge_editor(files):
    rows = []
    for f in files:
        reader = PdfReader(io.BytesIO(f.getvalue()))
        for p in range(len(reader.pages)):
            rows.append({
                "id": f"{f.name}__{p+1}",
                "arquivo": f.name,
                "pagina_pdf": p + 1,
                "incluir": True,
                "ordem": len(rows) + 1,
                "rotulo": f"{f.name} - página {p+1}",
            })
    return pd.DataFrame(rows)

def build_single_editor(file_name: str, file_bytes: bytes):
    reader = PdfReader(io.BytesIO(file_bytes))
    rows = []
    for p in range(len(reader.pages)):
        rows.append({
            "id": f"{file_name}__{p+1}",
            "arquivo": file_name,
            "pagina_pdf": p + 1,
            "incluir": True,
            "ordem": p + 1,
            "rotulo": f"Página {p+1}",
        })
    return pd.DataFrame(rows)

def build_reorganize_editor(base_pdf, extra_pdfs):
    rows = []
    all_files = [base_pdf] + extra_pdfs
    for f in all_files:
        reader = PdfReader(io.BytesIO(f.getvalue()))
        for p in range(len(reader.pages)):
            rows.append({
                "id": f"{f.name}__{p+1}",
                "arquivo": f.name,
                "pagina_pdf": p + 1,
                "incluir": True,
                "ordem": len(rows) + 1,
                "rotulo": f"{f.name} - página {p+1}",
            })
    return pd.DataFrame(rows)

def apply_drag_order(df: pd.DataFrame, sorted_labels: List[str]) -> pd.DataFrame:
    label_to_row = {row["rotulo"]: row for _, row in df.iterrows()}
    ordered_rows = []
    for idx, label in enumerate(sorted_labels, start=1):
        row = label_to_row[label].copy()
        row["ordem"] = idx
        ordered_rows.append(row)
    return pd.DataFrame(ordered_rows)

def render_professional_preview(plan_df: pd.DataFrame, file_bytes_map: Dict[str, bytes], title="Preview das páginas"):
    selected = plan_df[plan_df["incluir"] == True].sort_values("ordem")

    st.markdown(f"### {title}")
    if selected.empty:
        st.info("Nenhuma página selecionada.")
        return

    for chunk in chunk_list(selected.to_dict("records"), 4):
        cols = st.columns(4)
        for col, item in zip(cols, chunk):
            with col:
                try:
                    img = get_pdf_thumbnail(
                        file_bytes_map[item["arquivo"]],
                        int(item["pagina_pdf"]) - 1,
                        zoom=0.58
                    )
                    st.markdown(
                        f"""
                        <div class="preview-page-card">
                            <div class="page-order-badge">{int(item['ordem'])}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.image(img, use_container_width=True)
                    st.markdown(
                        f"""
                        <div class="page-meta">
                            <strong>{item['arquivo']}</strong><br>
                            Página {int(item['pagina_pdf'])}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                except Exception:
                    st.markdown(
                        f"""
                        <div class="preview-card-fallback">
                            Prévia indisponível<br>
                            {item['arquivo']} - página {int(item['pagina_pdf'])}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background: #f8fafc !important;
    color: #0f172a !important;
}

header, [data-testid="stHeader"] {
    background: transparent !important;
}

p, label, div, span, h1, h2, h3 {
    color: #0f172a !important;
}

.hero {
    text-align: center;
    margin-top: 16px;
    margin-bottom: 24px;
}

.hero h1 {
    font-size: 2.5rem;
    margin-bottom: 6px;
    color: #0f172a !important;
}

.hero p {
    color: #475569 !important;
    font-size: 1rem;
}

.top-menu-wrap {
    max-width: 1420px;
    margin: 0 auto 18px auto;
}

.cards-wrapper {
    max-width: 1120px;
    margin: 0 auto 28px auto;
}

.tool-card {
    background: rgba(255,255,255,0.98);
    border: 1px solid rgba(147,197,253,0.22);
    border-radius: 18px;
    padding: 22px 18px;
    text-align: center;
    box-shadow: 0 10px 24px rgba(96, 165, 250, 0.03);
    min-height: 178px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: transform .18s ease, box-shadow .18s ease;
}

.tool-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 28px rgba(96, 165, 250, 0.06);
}

.tool-title {
    font-size: 1.06rem;
    font-weight: 700;
    color: #0f172a !important;
    margin-bottom: 8px;
}

.tool-desc {
    font-size: 0.94rem;
    color: #334155 !important;
    line-height: 1.45;
    margin-bottom: 18px;
}

.tool-panel {
    max-width: 1040px;
    margin: 0 auto;
    background: #ffffff;
    border: 1px solid rgba(147,197,253,0.22);
    border-radius: 20px;
    padding: 28px;
    box-shadow: 0 10px 24px rgba(96, 165, 250, 0.03);
}

.tool-banner {
    max-width: 1040px;
    margin: 0 auto 18px auto;
    background: #ffffff;
    border: 1px solid rgba(147,197,253,0.22);
    border-radius: 20px;
    padding: 26px 18px;
    box-shadow: 0 10px 24px rgba(96, 165, 250, 0.03);
    text-align: center;
}

.tool-banner h2 {
    margin: 0;
    font-size: 2rem;
    color: #0f172a !important;
    font-weight: 800;
}

.tool-banner p {
    margin: 8px 0 0 0;
    color: #475569 !important;
    font-size: 0.98rem;
}

.preview-page-card {
    text-align: center;
    margin-bottom: 8px;
}

.page-order-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 54px;
    height: 54px;
    border-radius: 999px;
    background: #dbeafe;
    color: #0c4a6e !important;
    font-size: 1.4rem;
    font-weight: 800;
    box-shadow: 0 6px 14px rgba(96, 165, 250, 0.10);
}

.page-meta {
    text-align: center;
    font-size: 0.88rem;
    color: #334155 !important;
    margin-top: 8px;
    margin-bottom: 16px;
    background: #ffffff;
    border: 1px solid rgba(147,197,253,0.18);
    border-radius: 12px;
    padding: 8px;
}

.preview-card-fallback {
    background: #ffffff;
    border: 1px solid rgba(147,197,253,0.18);
    border-radius: 12px;
    padding: 14px;
    text-align: center;
}

[data-testid="stFileUploader"],
.stTextInput,
.stNumberInput,
.stSelectbox {
    max-width: 640px;
    margin-left: auto !important;
    margin-right: auto !important;
}

label {
    text-align: center !important;
    display: block !important;
    width: 100% !important;
    color: #0f172a !important;
    font-weight: 500 !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: #ffffff !important;
    border: 2px dashed rgba(147,197,253,0.48) !important;
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
    color: #1e293b !important;
    font-weight: 600;
}

[data-testid="stFileUploader"] section button {
    font-size: 0 !important;
    background: #eff6ff !important;
    color: #1e40af !important;
    border: 1px solid rgba(147,197,253,0.45) !important;
    border-radius: 10px !important;
}

[data-testid="stFileUploader"] section button::after {
    content: "Selecionar arquivos";
    font-size: 14px !important;
    color: #1e40af !important;
    font-weight: 700;
}

.stButton {
    text-align: center !important;
}

.stButton > button {
    background: #60a5fa !important;
    color: #082f49 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    font-weight: 700 !important;
    box-shadow: 0 8px 18px rgba(96, 165, 250, 0.10) !important;
}

.stButton > button:hover {
    background: #3b82f6 !important;
    color: #082f49 !important;
}

.top-menu-wrap .stButton > button {
    color: #082f49 !important;
    background: rgba(147,197,253,0.65) !important;
}

.top-menu-wrap .stButton > button:hover {
    color: #082f49 !important;
    background: rgba(96,165,250,0.82) !important;
}

[data-testid="stDownloadButton"] {
    text-align: center !important;
}

[data-testid="stDownloadButton"] > button {
    background: #3b82f6 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    font-weight: 700 !important;
}

input, textarea {
    color: #0f172a !important;
}

[data-baseweb="input"] {
    background: #ffffff !important;
    border-radius: 12px !important;
}

[data-testid="stSidebar"] {
    background: #f0f9ff !important;
    border-right: 1px solid rgba(147,197,253,0.28);
}

[data-testid="stSidebar"] * {
    color: #0f172a !important;
}

.footer-note {
    text-align: center;
    color: #475569 !important;
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
# MENUS
# =====================================================

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

DESCRIPTIONS = {
    "unlock": "Remova a senha de arquivos protegidos",
    "merge": "Combine vários PDFs em um único arquivo",
    "split": "Separe ou reorganize páginas de um PDF",
    "reorganize": "Reordene, exclua ou adicione páginas",
    "compress": "Reduza o tamanho do arquivo",
    "imgpdf": "Converta imagens JPG/PNG em PDF",
    "pdfjpg": "Transforme páginas do PDF em JPG",
    "pdfword": "Converta texto do PDF em Word",
    "wordpdf": "Converta DOCX em PDF simples",
}

BANNERS = {
    "unlock": ("🔓 Remover senha de PDF", "Envie um ou mais PDFs protegidos, digite a senha e baixe o resultado."),
    "merge": ("📎 Juntar PDFs", "Envie vários PDFs, arraste as páginas no menu lateral e acompanhe o preview no centro."),
    "split": ("✂️ Dividir PDF", "Escolha um PDF, reorganize ou exclua páginas pelo menu lateral e use a divisão clássica se quiser."),
    "reorganize": ("🗂️ Reorganizar PDF", "Arraste páginas para reordenar, exclua o que não quer e adicione páginas de PDFs extras."),
    "compress": ("🗜️ Comprimir PDF", "Reduza o tamanho de um ou mais PDFs."),
    "imgpdf": ("🖼️ JPG para PDF", "Envie várias imagens e gere um único PDF."),
    "pdfjpg": ("🖼️ PDF para JPG", "Converta as páginas do PDF em imagens JPG."),
    "pdfword": ("📄 PDF para Word", "Extraia o texto do PDF e gere um arquivo .docx."),
    "wordpdf": ("📄 Word para PDF", "Converta um .docx em PDF simples, com foco em texto."),
}

if "tool" not in st.session_state:
    st.session_state.tool = None

# =====================================================
# TOP MENU
# =====================================================

st.markdown('<div class="top-menu-wrap">', unsafe_allow_html=True)

top_cols = st.columns([1, 1, 1, 1, 1, 1.25])

main_order = ["unlock", "merge", "split", "reorganize", "compress"]
for idx, key in enumerate(main_order):
    with top_cols[idx]:
        if st.button(MAIN_TOOLS[key], key=f"top_{key}"):
            st.session_state.tool = key
            st.rerun()

with top_cols[-1]:
    with st.popover("Converter PDF"):
        for key, label in CONVERSION_TOOLS.items():
            if st.button(label, key=f"popover_{key}"):
                st.session_state.tool = key
                st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# HOME
# =====================================================

if st.session_state.tool is None:
    st.markdown('<div class="cards-wrapper">', unsafe_allow_html=True)

    home_order = [
        "unlock", "merge", "split",
        "reorganize", "compress", "imgpdf",
        "pdfjpg", "pdfword", "wordpdf",
    ]

    rows = list(chunk_list(home_order, 3))
    for row in rows:
        cols = st.columns(3, gap="medium")
        for col, key in zip(cols, row):
            with col:
                label = MAIN_TOOLS.get(key, CONVERSION_TOOLS.get(key, key))
                st.markdown(f"""
                <div class="tool-card">
                    <div>
                        <div class="tool-title">{label}</div>
                        <div class="tool-desc">{DESCRIPTIONS[key]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Usar agora", key=f"home_{key}"):
                    st.session_state.tool = key
                    st.rerun()
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# TOOL PANEL
# =====================================================

if st.session_state.tool is not None:
    back_cols = st.columns([1, 2, 1])
    with back_cols[1]:
        if st.button("⬅ Voltar para ferramentas"):
            st.session_state.tool = None
            st.rerun()

    banner_title, banner_desc = BANNERS[st.session_state.tool]
    st.markdown(f"""
    <div class="tool-banner">
        <h2>{banner_title}</h2>
        <p>{banner_desc}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="tool-panel">', unsafe_allow_html=True)

    if st.session_state.tool == "unlock":
        arquivos = st.file_uploader("Envie os PDFs", type=["pdf"], accept_multiple_files=True, key="unlock_files")
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
                try:
                    if len(arquivos) == 1:
                        unlocked = unlock_pdf(arquivos[0].getvalue(), senha)
                        st.download_button("Baixar PDF", unlocked, arquivos[0].name, key="download_unlock_single")
                    else:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                            for arquivo in arquivos:
                                unlocked = unlock_pdf(arquivo.getvalue(), senha)
                                zip_file.writestr(arquivo.name, unlocked)

                        st.download_button("Baixar todos", zip_buffer.getvalue(), "pdfs_desbloqueados.zip", key="download_unlock_all")
                except Exception as e:
                    st.error(str(e))

    elif st.session_state.tool == "merge":
        arquivos = st.file_uploader("Selecione os PDFs", type=["pdf"], accept_multiple_files=True, key="merge_files")

        file_bytes_map = {}
        if arquivos:
            file_bytes_map = {a.name: a.getvalue() for a in arquivos}

            if "merge_editor_df" not in st.session_state or st.session_state.get("merge_source") != [a.name for a in arquivos]:
                st.session_state.merge_editor_df = build_merge_editor(arquivos)
                st.session_state.merge_source = [a.name for a in arquivos]

            st.sidebar.markdown("## Editor de páginas - Juntar PDFs")
            st.sidebar.write("### Arquivos enviados")
            for a in arquivos:
                st.sidebar.write(f"• {a.name}")

            st.markdown("### Arraste as páginas para reorganizar")
            labels = st.session_state.merge_editor_df.sort_values("ordem")["rotulo"].tolist()
            sorted_labels = sort_items(labels, direction="horizontal", key="merge_sort_center")
            st.session_state.merge_editor_df = apply_drag_order(st.session_state.merge_editor_df, sorted_labels)

            edited_df = st.sidebar.data_editor(
                st.session_state.merge_editor_df,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                column_config={
                    "id": None,
                    "arquivo": st.column_config.TextColumn("Arquivo", disabled=True),
                    "pagina_pdf": st.column_config.NumberColumn("Página", disabled=True),
                    "incluir": st.column_config.CheckboxColumn("Incluir"),
                    "ordem": st.column_config.NumberColumn("Ordem", disabled=True),
                    "rotulo": st.column_config.TextColumn("Rótulo", disabled=True),
                },
                key="merge_editor_grid"
            )
            st.session_state.merge_editor_df = edited_df

            render_professional_preview(st.session_state.merge_editor_df, file_bytes_map, "Preview das páginas selecionadas")

        button_cols = st.columns([1, 1, 1])
        with button_cols[1]:
            juntar = st.button("Juntar PDFs", key="btn_merge")

        if juntar:
            if not arquivos:
                st.warning("Envie pelo menos um PDF.")
            else:
                selected = st.session_state.merge_editor_df
                if selected[selected["incluir"] == True].empty:
                    st.warning("Selecione pelo menos uma página.")
                else:
                    merged = merge_pdfs_from_plan(st.session_state.merge_editor_df, file_bytes_map)
                    st.download_button("Baixar PDF unido", merged, "pdf_unido.pdf", key="download_merge")

    elif st.session_state.tool == "split":
        arquivo = st.file_uploader("Selecione o PDF", type=["pdf"], accept_multiple_files=False, key="split_file")

        if arquivo:
            file_bytes = arquivo.getvalue()
            file_map = {arquivo.name: file_bytes}
            reader = PdfReader(io.BytesIO(file_bytes))
            paginas = len(reader.pages)

            if "split_editor_df" not in st.session_state or st.session_state.get("split_source") != arquivo.name:
                st.session_state.split_editor_df = build_single_editor(arquivo.name, file_bytes)
                st.session_state.split_source = arquivo.name

            st.sidebar.markdown("## Editor de páginas - Dividir PDF")
            st.sidebar.write("### Arquivo enviado")
            st.sidebar.write(f"• {arquivo.name}")

            st.markdown("### Arraste as páginas para reorganizar")
            labels = st.session_state.split_editor_df.sort_values("ordem")["rotulo"].tolist()
            sorted_labels = sort_items(labels, direction="horizontal", key="split_sort_center")
            st.session_state.split_editor_df = apply_drag_order(st.session_state.split_editor_df, sorted_labels)

            edited_df = st.sidebar.data_editor(
                st.session_state.split_editor_df,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                column_config={
                    "id": None,
                    "arquivo": st.column_config.TextColumn("Arquivo", disabled=True),
                    "pagina_pdf": st.column_config.NumberColumn("Página", disabled=True),
                    "incluir": st.column_config.CheckboxColumn("Incluir"),
                    "ordem": st.column_config.NumberColumn("Ordem", disabled=True),
                    "rotulo": st.column_config.TextColumn("Rótulo", disabled=True),
                },
                key="split_editor_grid"
            )
            st.session_state.split_editor_df = edited_df

            render_professional_preview(st.session_state.split_editor_df, file_map, "Preview das páginas")

            st.markdown("### Divisão clássica")
            if paginas > 1:
                pagina = st.number_input("Dividir após página", min_value=1, max_value=paginas - 1, value=1)

                c1, c2 = st.columns(2)
                with c1:
                    dividir = st.button("Dividir PDF", key="btn_split")
                with c2:
                    gerar_reorganizado = st.button("Gerar PDF reorganizado", key="btn_split_rebuild")

                if dividir:
                    parte1, parte2 = split_pdf(file_bytes, pagina)
                    st.download_button("Baixar parte 1", parte1, with_suffix(arquivo.name, "_parte1", ".pdf"), key="download_split_1")
                    st.download_button("Baixar parte 2", parte2, with_suffix(arquivo.name, "_parte2", ".pdf"), key="download_split_2")

                if gerar_reorganizado:
                    selected = st.session_state.split_editor_df
                    if selected[selected["incluir"] == True].empty:
                        st.warning("Selecione pelo menos uma página.")
                    else:
                        rebuilt = rebuild_pdf_from_plan(st.session_state.split_editor_df, file_map)
                        st.download_button("Baixar PDF reorganizado", rebuilt, with_suffix(arquivo.name, "_reorganizado", ".pdf"), key="download_split_rebuild")

    elif st.session_state.tool == "reorganize":
        base_pdf = st.file_uploader("Selecione o PDF principal", type=["pdf"], accept_multiple_files=False, key="reorg_base")
        extra_pdfs = st.file_uploader("Selecione PDFs extras para adicionar páginas", type=["pdf"], accept_multiple_files=True, key="reorg_extra")

        extras = extra_pdfs if extra_pdfs else []

        if base_pdf:
            all_names = [base_pdf.name] + [e.name for e in extras]
            file_bytes_map = {base_pdf.name: base_pdf.getvalue()}
            for e in extras:
                file_bytes_map[e.name] = e.getvalue()

            if "reorg_editor_df" not in st.session_state or st.session_state.get("reorg_source") != all_names:
                st.session_state.reorg_editor_df = build_reorganize_editor(base_pdf, extras)
                st.session_state.reorg_source = all_names

            st.sidebar.markdown("## Editor de páginas - Reorganizar PDF")
            st.sidebar.write("### Arquivos disponíveis")
            for n in all_names:
                st.sidebar.write(f"• {n}")

            st.markdown("### Arraste as páginas para reorganizar")
            labels = st.session_state.reorg_editor_df.sort_values("ordem")["rotulo"].tolist()
            sorted_labels = sort_items(labels, direction="horizontal", key="reorg_sort_center")
            st.session_state.reorg_editor_df = apply_drag_order(st.session_state.reorg_editor_df, sorted_labels)

            edited_df = st.sidebar.data_editor(
                st.session_state.reorg_editor_df,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                column_config={
                    "id": None,
                    "arquivo": st.column_config.TextColumn("Arquivo", disabled=True),
                    "pagina_pdf": st.column_config.NumberColumn("Página", disabled=True),
                    "incluir": st.column_config.CheckboxColumn("Incluir"),
                    "ordem": st.column_config.NumberColumn("Ordem", disabled=True),
                    "rotulo": st.column_config.TextColumn("Rótulo", disabled=True),
                },
                key="reorg_editor_grid"
            )
            st.session_state.reorg_editor_df = edited_df

            render_professional_preview(st.session_state.reorg_editor_df, file_bytes_map, "Preview do PDF reorganizado")

            button_cols = st.columns([1, 1, 1])
            with button_cols[1]:
                gerar_reorg = st.button("Gerar PDF reorganizado", key="btn_reorg")

            if gerar_reorg:
                selected = st.session_state.reorg_editor_df
                if selected[selected["incluir"] == True].empty:
                    st.warning("Selecione pelo menos uma página.")
                else:
                    rebuilt = rebuild_pdf_from_plan(st.session_state.reorg_editor_df, file_bytes_map)
                    st.download_button("Baixar PDF reorganizado", rebuilt, with_suffix(base_pdf.name, "_reorganizado", ".pdf"), key="download_reorg")

    elif st.session_state.tool == "compress":
        arquivos = st.file_uploader("Selecione os PDFs", type=["pdf"], accept_multiple_files=True, key="compress_files")

        button_cols = st.columns([1, 1, 1])
        with button_cols[1]:
            comprimir = st.button("Comprimir PDFs", key="btn_compress")

        if comprimir:
            if not arquivos:
                st.warning("Envie pelo menos um PDF.")
            else:
                if len(arquivos) == 1:
                    compressed = compress_pdf_bytes(arquivos[0].getvalue())
                    st.download_button("Baixar PDF", compressed, arquivos[0].name, key="download_compress_single")
                else:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                        for arquivo in arquivos:
                            compressed = compress_pdf_bytes(arquivo.getvalue())
                            zip_file.writestr(arquivo.name, compressed)

                    st.download_button("Baixar PDFs comprimidos", zip_buffer.getvalue(), "pdfs_comprimidos.zip", key="download_compress")

    elif st.session_state.tool == "imgpdf":
        imagens = st.file_uploader("Envie imagens", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="imgpdf_files")

        button_cols = st.columns([1, 1, 1])
        with button_cols[1]:
            converter = st.button("Converter em PDF", key="btn_imgpdf")

        if converter:
            if not imagens:
                st.warning("Envie pelo menos uma imagem.")
            else:
                pdf_bytes = images_to_pdf(imagens)
                output_name = with_ext(imagens[0].name, ".pdf") if len(imagens) == 1 else "imagens_convertidas.pdf"
                st.download_button("Baixar PDF", pdf_bytes, output_name, key="download_imgpdf")

    elif st.session_state.tool == "pdfjpg":
        arquivo = st.file_uploader("Selecione o PDF", type=["pdf"], accept_multiple_files=False, key="pdfjpg_file")

        button_cols = st.columns([1, 1, 1])
        with button_cols[1]:
            converter_jpg = st.button("Converter para JPG", key="btn_pdfjpg")

        if converter_jpg:
            if not arquivo:
                st.warning("Envie um PDF.")
            else:
                try:
                    zip_bytes = pdf_to_jpg_zip(arquivo.getvalue())
                    st.download_button("Baixar JPGs em ZIP", zip_bytes, with_suffix(arquivo.name, "_jpg", ".zip"), key="download_pdfjpg")
                except Exception as e:
                    st.error(f"Não foi possível converter este PDF: {e}")

    elif st.session_state.tool == "pdfword":
        arquivo = st.file_uploader("Selecione o PDF", type=["pdf"], accept_multiple_files=False, key="pdfword_file")

        button_cols = st.columns([1, 1, 1])
        with button_cols[1]:
            converter_word = st.button("Converter para Word", key="btn_pdfword")

        if converter_word:
            if not arquivo:
                st.warning("Envie um PDF.")
            else:
                try:
                    docx_bytes = pdf_text_to_docx(arquivo.getvalue())
                    st.download_button("Baixar Word (.docx)", docx_bytes, with_ext(arquivo.name, ".docx"), key="download_pdfword")
                except Exception as e:
                    st.error(f"Não foi possível converter este PDF: {e}")

    elif st.session_state.tool == "wordpdf":
        arquivo = st.file_uploader("Selecione o arquivo Word (.docx)", type=["docx"], accept_multiple_files=False, key="wordpdf_file")

        button_cols = st.columns([1, 1, 1])
        with button_cols[1]:
            converter_pdf = st.button("Converter para PDF", key="btn_wordpdf")

        if converter_pdf:
            if not arquivo:
                st.warning("Envie um arquivo .docx.")
            else:
                try:
                    pdf_bytes = docx_to_simple_pdf(arquivo.getvalue())
                    st.download_button("Baixar PDF", pdf_bytes, with_ext(arquivo.name, ".pdf"), key="download_wordpdf")
                except Exception as e:
                    st.error(f"Não foi possível converter este Word: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="footer-note">Ferramentas PDF gratuitas online</div>', unsafe_allow_html=True)
