import streamlit as st
from pypdf import PdfReader, PdfWriter
from PIL import Image
from pdf2image import convert_from_bytes
import io
import zipfile
import time

st.set_page_config(page_title="Ferramentas PDF", page_icon="📄", layout="wide")

# =============================
# CSS VISUAL MODERNO
# =============================

st.markdown("""
<style>

body {
background: linear-gradient(135deg,#141E30,#243B55);
}

.main-container{
max-width:700px;
margin:auto;
text-align:center;
}

h1,h2,h3{
text-align:center;
color:white;
}

.stFileUploader{
max-width:600px;
margin:auto;
}

.stTextInput{
max-width:400px;
margin:auto;
}

.stButton>button{
background:#4CAF50;
color:white;
border-radius:8px;
padding:10px 20px;
transition:0.3s;
}

.stButton>button:hover{
transform:scale(1.05);
background:#45a049;
}

</style>
""", unsafe_allow_html=True)

# =============================
# TÍTULO
# =============================

st.title("📄 Ferramentas PDF Online")

st.markdown("Ferramentas simples para **editar PDFs diretamente no navegador**.")

# =============================
# MENU
# =============================

menu = st.sidebar.radio(
    "Ferramentas",
    [
        "🔓 Remover senha",
        "📎 Juntar PDFs",
        "✂️ Dividir PDF",
        "🗜️ Comprimir PDF",
        "🖼️ PDF para imagem",
        "📄 Imagem para PDF"
    ]
)

# =============================
# REMOVER SENHA
# =============================

if menu == "🔓 Remover senha":

    st.header("Remover senha de PDF")

    arquivos = st.file_uploader(
        "Arraste e solte os PDFs aqui",
        type="pdf",
        accept_multiple_files=True,
        label_visibility="visible"
    )

    senha = st.text_input("Digite a senha do PDF", type="password")

    if st.button("Desbloquear PDFs"):

        progress = st.progress(0)

        arquivos_processados = []

        for i,arquivo in enumerate(arquivos):

            reader = PdfReader(arquivo)

            if reader.is_encrypted:
                reader.decrypt(senha)

            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            buffer = io.BytesIO()
            writer.write(buffer)

            arquivos_processados.append((arquivo.name,buffer.getvalue()))

            progress.progress((i+1)/len(arquivos))
            time.sleep(0.2)

        st.success("PDFs desbloqueados com sucesso!")

        # DOWNLOAD INDIVIDUAL

        for nome,data in arquivos_processados:

            st.download_button(
                f"Baixar {nome}",
                data,
                nome
            )

        # ZIP

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer,"w") as zip_file:

            for nome,data in arquivos_processados:
                zip_file.writestr(nome,data)

        st.download_button(
            "Baixar todos em ZIP",
            zip_buffer.getvalue(),
            "pdfs_desbloqueados.zip"
        )

# =============================
# JUNTAR PDF
# =============================

elif menu == "📎 Juntar PDFs":

    st.header("Juntar PDFs")

    arquivos = st.file_uploader(
        "Selecionar arquivos PDF",
        type="pdf",
        accept_multiple_files=True
    )

    if arquivos:

        ordem = st.multiselect(
            "Arraste para definir a ordem",
            [a.name for a in arquivos],
            default=[a.name for a in arquivos]
        )

        if st.button("Juntar PDFs"):

            writer = PdfWriter()

            for nome in ordem:

                for arq in arquivos:

                    if arq.name == nome:

                        reader = PdfReader(arq)

                        for page in reader.pages:
                            writer.add_page(page)

            buffer = io.BytesIO()
            writer.write(buffer)

            st.download_button(
                "Baixar PDF unido",
                buffer.getvalue(),
                "pdf_unido.pdf"
            )

# =============================
# DIVIDIR PDF
# =============================

elif menu == "✂️ Dividir PDF":

    st.header("Dividir PDF")

    arquivo = st.file_uploader("Selecionar PDF", type="pdf")

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

            for i in range(pagina,paginas):
                writer2.add_page(reader.pages[i])

            buffer1 = io.BytesIO()
            buffer2 = io.BytesIO()

            writer1.write(buffer1)
            writer2.write(buffer2)

            st.download_button("Baixar parte 1",buffer1.getvalue(),"parte1.pdf")
            st.download_button("Baixar parte 2",buffer2.getvalue(),"parte2.pdf")

# =============================
# COMPRIMIR PDF
# =============================

elif menu == "🗜️ Comprimir PDF":

    st.header("Comprimir PDF")

    arquivo = st.file_uploader("Selecionar PDF", type="pdf")

    if arquivo:

        reader = PdfReader(arquivo)

        writer = PdfWriter()

        for page in reader.pages:

            page.compress_content_streams()
            writer.add_page(page)

        buffer = io.BytesIO()
        writer.write(buffer)

        st.download_button(
            "Baixar PDF comprimido",
            buffer.getvalue(),
            "pdf_comprimido.pdf"
        )

# =============================
# PDF PARA IMAGEM
# =============================

elif menu == "🖼️ PDF para imagem":

    st.header("Converter PDF para imagem")

    arquivo = st.file_uploader("Selecionar PDF", type="pdf")

    if arquivo:

        imagens = convert_from_bytes(arquivo.read())

        st.write("Preview das páginas")

        for img in imagens:

            st.image(img,width=300)

# =============================
# IMAGEM PARA PDF
# =============================

elif menu == "📄 Imagem para PDF":

    st.header("Converter imagem para PDF")

    imagens = st.file_uploader(
        "Selecionar imagens",
        type=["png","jpg","jpeg"],
        accept_multiple_files=True
    )

    if st.button("Converter"):

        lista = []

        for img in imagens:

            image = Image.open(img).convert("RGB")
            lista.append(image)

        buffer = io.BytesIO()

        lista[0].save(buffer,save_all=True,append_images=lista[1:],format="PDF")

        st.download_button(
            "Baixar PDF",
            buffer.getvalue(),
            "imagens_convertidas.pdf"
        )

st.markdown("---")
st.caption("Ferramentas PDF gratuitas online")
