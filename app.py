import streamlit as st
from pypdf import PdfReader, PdfWriter
import io

st.set_page_config(page_title="Removedor de senha PDF", page_icon="🔓")

st.title("🔓 Removedor de senha de PDF")
st.write("Envie um PDF protegido e remova a senha rapidamente.")

arquivo = st.file_uploader("Selecione o PDF", type="pdf")
senha = st.text_input("Digite a senha do PDF", type="password")

if st.button("Remover senha"):

    if arquivo is None:
        st.warning("Envie um arquivo PDF.")
    
    elif senha == "":
        st.warning("Digite a senha do PDF.")

    else:
        try:
            reader = PdfReader(arquivo)

            if reader.is_encrypted:
                reader.decrypt(senha)

                writer = PdfWriter()

                for page in reader.pages:
                    writer.add_page(page)

                buffer = io.BytesIO()
                writer.write(buffer)

                st.success("Senha removida com sucesso!")

                st.download_button(
                    label="📥 Baixar PDF sem senha",
                    data=buffer.getvalue(),
                    file_name="pdf_sem_senha.pdf",
                    mime="application/pdf"
                )

            else:
                st.info("Esse PDF não possui senha.")

        except Exception:
            st.error("Senha incorreta ou erro ao processar o PDF.")
