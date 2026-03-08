import streamlit as st
from pypdf import PdfReader, PdfWriter
from PIL import Image
import io
import zipfile

st.set_page_config(page_title="Ferramentas PDF", page_icon="📄", layout="wide")

# ==============================
# CSS / ESTILO
# ==============================

st.markdown("""
<style>

body {
background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
}

h1, h2, h3 {
color: white;
}

.stButton>button {
background-color:#00c6ff;
color:white;
border-radius:10px;
padding:10px 20px;
transition:0.3s;
}

.stButton>button:hover {
background-color:#0072ff;
transform:scale(1.05);
}

</style>
""", unsafe_allow_html=True)

# ==============================
# TÍTULO
# ==============================

st.title("📄 Ferramentas PDF Online")
st.write("Ferramentas gratuitas para trabalhar com PDFs.")

# ==============================
# MENU
# ==============================

menu = st.sidebar.radio(
    "Escolha uma ferramenta",
    [
        "🔓 Remover senha",
        "📎 Juntar PDFs",
        "✂️ Dividir PDF",
        "🗜️ Comprimir PDF",
        "🖼️ PDF para Imagem",
        "📄 Imagem para PDF"
    ]
)

# ==============================
# REMOVER SENHA
# ==============================

if menu == "🔓 Remover senha":

    st.header("🔓 Remover senha de PDF")

    arquivos = st.file_uploader(
        "Arraste os PDFs protegidos",
        type="pdf",
        accept_multiple_files=True
    )

    senha = st.text_input("Digite a senha", type="password")

    if st.button("Desbloquear PDFs"):

        arquivos_processados = []

        for arquivo in arquivos:

            reader = PdfReader(arquivo)

            if reader.is_encrypted:
                reader.decrypt(senha)

            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            buffer = io.BytesIO()
            writer.write(buffer)

            arquivos_processados.append((arquivo.name, buffer.getvalue()))

            st.success(f"{arquivo.name} desbloqueado")

        # DOWNLOAD INDIVIDUAL

        for nome, data in arquivos_processados:

            st.download_button(
                f"Baixar {nome}",
                data,
                nome,
                mime="application/pdf"
            )

        # DOWNLOAD ZIP

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:

            for nome, data in arquivos_processados:
                zip_file.writestr(nome, data)

        st.download_button(
            "📦 Baixar TODOS em ZIP",
            zip_buffer.getvalue(),
            "pdfs_desbloqueados.zip"
        )

# ==============================
# JUNTAR PDFs
# ==============================

elif menu == "📎 Juntar PDFs":

    st.header("📎 Juntar PDFs")

    arquivos = st.file_uploader(
        "Selecione os PDFs",
        type="pdf",
        accept_multiple_files=True
    )

    if st.button("Juntar"):

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

# ==============================
# DIVIDIR PDF
# ==============================

elif menu == "✂️ Dividir PDF":

    st.header("✂️ Dividir PDF")

    arquivo = st.file_uploader("Envie o PDF", type="pdf")

    if arquivo:

        reader = PdfReader(arquivo)

        paginas = len(reader.pages)

        pagina = st.number_input(
            "Dividir após página",
            min_value=1,
            max_value=paginas-1
        )

        if st.button("Dividir"):

            writer1 = PdfWriter()
            writer2 = PdfWriter()

            for i in range(pagina):
                writer1.add_page(reader.pages[i])

            for i in range(pagina, paginas):
                writer2.add_page(reader.pages[i])

            buffer1 = io.BytesIO()
            buffer2 = io.BytesIO()

            writer1.write(buffer1)
            writer2.write(buffer2)

            st.download_button("Parte 1", buffer1.getvalue(), "parte1.pdf")
            st.download_button("Parte 2", buffer2.getvalue(), "parte2.pdf")

# ==============================
# COMPRIMIR PDF
# ==============================

elif menu == "🗜️ Comprimir PDF":

    st.header("🗜️ Comprimir PDF")

    arquivo = st.file_uploader("Envie o PDF", type="pdf")

    if st.button("Comprimir"):

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

# ==============================
# PDF PARA IMAGEM
# ==============================

elif menu == "🖼️ PDF para Imagem":

    st.header("PDF para imagem")

    arquivo = st.file_uploader("Envie o PDF", type="pdf")

    if arquivo:

        reader = PdfReader(arquivo)

        st.write("Extração de páginas como imagem.")

        for i, page in enumerate(reader.pages):

            st.write(f"Página {i+1}")

# ==============================
# IMAGEM PARA PDF
# ==============================

elif menu == "📄 Imagem para PDF":

    st.header("Imagem para PDF")

    imagens = st.file_uploader(
        "Envie imagens",
        type=["png","jpg","jpeg"],
        accept_multiple_files=True
    )

    if st.button("Converter"):

        lista = []

        for img in imagens:

            image = Image.open(img).convert("RGB")
            lista.append(image)

        buffer = io.BytesIO()

        lista[0].save(buffer, save_all=True, append_images=lista[1:], format="PDF")

        st.download_button(
            "Baixar PDF",
            buffer.getvalue(),
            "imagens.pdf"
        )

st.markdown("---")
st.caption("Ferramentas PDF online gratuitas")
