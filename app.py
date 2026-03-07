import streamlit as st
from pypdf import PdfReader, PdfWriter
import tempfile

st.set_page_config(
    page_title="Remover senha de PDF",
    page_icon="🔓"
)

st.title("🔓 Removedor de senha de PDF")

st.write("Envie um PDF protegido e remova a senha rapidamente.")

arquivo = st.file_uploader("Escolha o PDF", type="pdf")
senha = st.text_input("Digite a senha do PDF", type="password")

if st.button("Remover senha"):

    if arquivo and senha:

        reader = PdfReader(arquivo)

        if reader.is_encrypted:

            reader.decrypt(senha)

            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

            with open(temp.name, "wb") as f:
                writer.write(f)

            with open(temp.name, "rb") as f:
                st.download_button(
                    "📥 Baixar PDF sem senha",
                    f,
                    file_name="pdf_sem_senha.pdf"
                )

        else:

            st.error("Esse PDF não possui senha.")
