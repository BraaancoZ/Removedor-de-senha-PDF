import streamlit as st
from pypdf import PdfReader, PdfWriter
import io

st.set_page_config(
    page_title="Ferramentas PDF",
    page_icon="📄",
    layout="centered"
)

st.title("📄 Ferramentas PDF Online")
st.markdown("Ferramentas gratuitas para **remover senha, juntar e dividir PDFs**.")

st.markdown("---")

menu = st.sidebar.selectbox(
    "Escolha a ferramenta",
    [
        "🔓 Remover senha do PDF",
        "📎 Juntar PDFs",
        "✂️ Dividir PDF"
    ]
)

# ===============================
# REMOVER SENHA
# ===============================

if menu == "🔓 Remover senha do PDF":

    st.header("🔓 Remover senha de PDF")

    arquivos = st.file_uploader(
        "Arraste ou selecione PDFs protegidos",
        type="pdf",
        accept_multiple_files=True
    )

    senha = st.text_input("Digite a senha do PDF", type="password")

    if st.button("Remover senha"):

        if not arquivos:
            st.warning("Envie pelo menos um PDF.")

        elif senha == "":
            st.warning("Digite a senha.")

        else:

            for arquivo in arquivos:

                try:

                    with st.spinner(f"Processando {arquivo.name}..."):

                        reader = PdfReader(arquivo)

                        if reader.is_encrypted:
                            reader.decrypt(senha)

                        writer = PdfWriter()

                        for page in reader.pages:
                            writer.add_page(page)

                        buffer = io.BytesIO()
                        writer.write(buffer)

                        st.success(f"{arquivo.name} desbloqueado!")

                        st.download_button(
                            label=f"Baixar {arquivo.name}",
                            data=buffer.getvalue(),
                            file_name=f"sem_senha_{arquivo.name}",
                            mime="application/pdf"
                        )

                except:
                    st.error(f"Erro ao processar {arquivo.name}. Senha incorreta.")

# ===============================
# JUNTAR PDFs
# ===============================

elif menu == "📎 Juntar PDFs":

    st.header("📎 Juntar PDFs")

    arquivos = st.file_uploader(
        "Selecione os PDFs para juntar",
        type="pdf",
        accept_multiple_files=True
    )

    if st.button("Juntar PDFs"):

        if not arquivos:
            st.warning("Envie os arquivos.")

        else:

            writer = PdfWriter()

            with st.spinner("Juntando PDFs..."):

                for arquivo in arquivos:
                    reader = PdfReader(arquivo)

                    for page in reader.pages:
                        writer.add_page(page)

                buffer = io.BytesIO()
                writer.write(buffer)

            st.success("PDFs unidos com sucesso!")

            st.download_button(
                "Baixar PDF unido",
                buffer.getvalue(),
                "pdf_unido.pdf",
                mime="application/pdf"
            )

# ===============================
# DIVIDIR PDF
# ===============================

elif menu == "✂️ Dividir PDF":

    st.header("✂️ Dividir PDF")

    arquivo = st.file_uploader(
        "Selecione um PDF",
        type="pdf"
    )

    if arquivo:

        reader = PdfReader(arquivo)

        paginas = len(reader.pages)

        st.write(f"O PDF possui **{paginas} páginas**.")

        pagina = st.number_input(
            "Dividir após a página:",
            min_value=1,
            max_value=paginas-1,
            value=1
        )

        if st.button("Dividir PDF"):

            writer1 = PdfWriter()
            writer2 = PdfWriter()

            with st.spinner("Dividindo PDF..."):

                for i in range(pagina):
                    writer1.add_page(reader.pages[i])

                for i in range(pagina, paginas):
                    writer2.add_page(reader.pages[i])

                buffer1 = io.BytesIO()
                buffer2 = io.BytesIO()

                writer1.write(buffer1)
                writer2.write(buffer2)

            st.success("PDF dividido!")

            st.download_button(
                "Baixar primeira parte",
                buffer1.getvalue(),
                "parte1.pdf",
                mime="application/pdf"
            )

            st.download_button(
                "Baixar segunda parte",
                buffer2.getvalue(),
                "parte2.pdf",
                mime="application/pdf"
            )

st.markdown("---")
st.caption("Ferramentas PDF gratuitas online.")
