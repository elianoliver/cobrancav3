import pandas as pd
import re
from datetime import datetime

def read_excel_file(file_path, verificar_data=True):
    """
    Lê um arquivo Excel e opcionalmente verifica se a data no nome do arquivo é a atual.

    Args:
        file_path: Caminho para o arquivo Excel
        verificar_data: Se True, verifica se o arquivo é do dia atual
    """
    if verificar_data:
        # Extrair a data do nome do arquivo usando regex
        padrao_data = r"_(\d{4}-\d{2}-\d{2})-"
        match = re.search(padrao_data, file_path)

        if match:
            data_arquivo_str = match.group(1)
            data_arquivo = datetime.strptime(data_arquivo_str, "%Y-%m-%d").date()
            hoje = datetime.now().date()

            if data_arquivo != hoje:
                raise ValueError(f"O arquivo não é do dia atual. Data do arquivo: {data_arquivo}, Data atual: {hoje}")
        else:
            print("Aviso: Formato de nome de arquivo inválido. O nome deve conter a data no formato '_YYYY-MM-DD-'.")

    try:
        return pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"Erro: O arquivo {file_path} não foi encontrado.")
        raise
    except Exception as e:
        print(f"Erro ao ler o arquivo Excel: {str(e)}")
        raise

def clean_column_names(df):
    df.columns = df.columns.str.strip()
    return df

def get_users_with_fines(df):
    return df[df['Valor multa'] > 0] if 'Valor multa' in df.columns else pd.DataFrame()

def get_summary(df):
    clean_column_names(df)
    num_rows = len(df)
    num_unique_users = df['Código da pessoa'].nunique() if 'Código da pessoa' in df.columns else "N/A"
    total_fines = df['Valor multa'].sum() if 'Valor multa' in df.columns else "N/A"

    summary = {
        "num_rows": num_rows,
        "num_unique_users": num_unique_users,
        "total_fines": total_fines
    }

    return summary

# TESTANDO O MÓDULO
# if __name__ == "__main__":
#     # Exemplo de uso (pode ser removido ou usado para testes)
#     try:
#         # Use verificar_data=False para testes com arquivos antigos
#         df = read_excel_file('elian.oliveira_2025-02-24-23-42-07.xlsx', verificar_data=True)
#         df = clean_column_names(df)
#         print("Conteúdo do arquivo Excel:")
#         print(df)

#         summary = get_summary(df)
#         print("Resumo do arquivo:")
#         print(f"Linhas: {summary['num_rows']}\nPessoas únicas: {summary['num_unique_users']}\nTotal de multas: R$ {summary['total_fines']:.2f}")
#     except ValueError as e:
#         print(f"Erro de validação: {str(e)}")
#     except Exception as e:
#         print(f"Erro no processamento: {str(e)}")