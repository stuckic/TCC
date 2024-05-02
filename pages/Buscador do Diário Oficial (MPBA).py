import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import fitz  # PyMuPDF
import io
from unidecode import unidecode

# Função para substituir caracteres problemáticos
def substituir_caracteres(texto):
    substituicoes = {"ﬁ ": "fi"}  # Adicione mais substituições conforme necessário
    for antigo, novo in substituicoes.items():
        texto = texto.replace(antigo, novo)
    return unidecode(texto)

# Função para converter a data no formato DD/MM/AAAA para AAAAMMDD
def converter_data(data_input):
    data_obj = datetime.strptime(data_input, "%d/%m/%Y")
    data_formatada = data_obj.strftime("%Y%m%d")
    return data_formatada

# Função principal Streamlit
def main():
    st.title("Buscador do Diário Oficial (MPBA)")

    # Solicitar a data ao usuário
    data_usuario = st.text_input(label="Digite a data do Diário Oficial no formato DD/MM/AAAA: ",
                                 placeholder="Digite a data no formato DD/MM/AAAA")

    # Botão para iniciar a busca
    if st.button("Confirmar data"):
        st.experimental_rerun()  # Encerra a execução do Streamlit

    # Verificar se o usuário pressionou Enter sem digitar um texto de busca
    if not data_usuario:
        st.markdown("<font color='blue'>Por favor, digite uma data válida no formato DD/MM/AAAA.",
                    unsafe_allow_html=True)
        st.stop()  # Encerra a execução do Streamlit se o texto de busca

    try:
        # Converter a data fornecida pelo usuário
        data_convertida = converter_data(data_usuario)

        # Gerar o link com a data convertida
        link = f"https://www.mpba.mp.br/sites/default/files/biblioteca/diariojustica/{data_convertida}.pdf"

        # Obter o conteúdo do PDF diretamente da resposta da solicitação
        response = requests.get(link)

        # Carregar o PDF com PyMuPDF a partir do conteúdo da resposta
        doc = fitz.open("pdf", response.content)

        # Informar o número de páginas do PDF
        st.write(f"\nO Diário Oficial do dia {data_usuario}, referente às publicações do MPBA, possui {doc.page_count} páginas.\n")

        # Inicializar uma lista para armazenar o texto completo
        texto_completo = []

        # Iterar sobre as páginas do PDF
        for page_num in range(doc.page_count):
            # Obter a página
            page = doc[page_num]

            # Extrair o texto da página
            texto_completo.append(page.get_text("text"))

        # Concatenar o texto completo em uma única string
        texto_final = "\n".join(texto_completo)

        # Substituir caracteres problemáticos
        texto_final = substituir_caracteres(texto_final)

        # Converter o texto em um DataFrame (pode precisar de ajustes dependendo do formato do texto)
        df_final = pd.read_csv(io.StringIO(texto_final), delimiter='\t', header=None)

        # Imprimir o DataFrame
        # st.write(df_final)

    except ValueError:
        st.error("Formato de data inválido. Certifique-se de digitar a data no formato correto DD/MM/AAAA.")
        return

    except Exception as e:
        st.error("Erro ao carregar o PDF: A data informada não teve publicação de Diário Oficial.")
        return

    # Solicitar o texto a ser buscado
    texto_busca = st.text_input(label="Digite o texto que deseja buscar no Diário Oficial: ",
                                placeholder="Digite o texto que deseja buscar no Diário Oficial")

    # Botão para iniciar a busca
    if st.button("Buscar"):
        st.experimental_rerun() # Encerra a execução do Streamlit

    # Verificar se o usuário pressionou Enter sem digitar um texto de busca
    if not texto_busca:
        st.markdown("<font color='blue'>Por favor, digite o texto que deseja buscar no Diário Oficial.</font>",
                    unsafe_allow_html=True)
        st.stop()  # Encerra a execução do Streamlit se o texto de busca estiver vazio

    # Substituir caracteres problemáticos
    texto_busca = substituir_caracteres(texto_busca)

    # Contar ocorrências do texto em todo o DataFrame (ignorando maiúsculas e minúsculas)
    ocorrencias = texto_final.lower().count(texto_busca.lower())

    # Imprimir o resultado
    if ocorrencias > 0:
        st.write(
            f"\nO texto '{texto_busca}' foi encontrado {ocorrencias} vez(es) no Diário Oficial do dia {data_usuario}.\n")

    # Contar ocorrências do texto em cada página
    ocorrencias_por_pagina = texto_final.lower().split("\n\n")
    ocorrencias_por_pagina = [ocorrencia.count(texto_busca.lower()) for ocorrencia in ocorrencias_por_pagina]

    # Encontrar índices das páginas onde o texto foi encontrado
    paginas_com_ocorrencias = [i + 1 for i, count in enumerate(ocorrencias_por_pagina) if count > 0]

    # Criar um dicionário para mapear número da página para número da linha
    pagina_para_linha = {}

    # Iterar sobre as páginas do PDF e contar o número de linhas
    linha_atual = 0
    for page_num in range(doc.page_count):
        # Obter a página
        page = doc[page_num]

        # Extrair o texto da página
        texto_pagina = page.get_text("text")

        # Contar o número de linhas nesta página
        num_linhas_pagina = texto_pagina.count('\n') + 1

        # Mapear a página para as linhas correspondentes no DataFrame
        pagina_para_linha[page_num + 1] = (linha_atual + 1, linha_atual + num_linhas_pagina)

        # Atualizar o número da linha atual
        linha_atual += num_linhas_pagina

    # Imprimir o resultado
    if len(paginas_com_ocorrencias) > 0:
        st.write(f"O texto '{texto_busca}' foi encontrado nas seguintes páginas:\n")
        for numero_pagina in paginas_com_ocorrencias:
            # Obter a linha correspondente no DataFrame
            linha_inicial, linha_final = pagina_para_linha.get(numero_pagina, (0, 0))

            # Imprimir o link da página
            link_pagina = f"{link}#page={numero_pagina}"
            st.write(f"-Página {numero_pagina}: {link_pagina}")
            # st.write(f"- Página {numero_pagina} (Linhas {linha_inicial}-{linha_final}): {link_pagina}")

            # Imprimir a contagem de ocorrências na página
            st.write(f"Ocorrências nesta página: {ocorrencias_por_pagina[numero_pagina - 1]}\n")
    else:
        st.write(f"\nO texto '{texto_busca}' não foi encontrado no Diário Oficial.\n")

if st.button("Reiniciar o Aplicativo"):
    st.experimental_rerun()

if __name__ == "__main__":
    main()
