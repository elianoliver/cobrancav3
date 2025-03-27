import pandas as pd
import json
from datetime import datetime

def sort_by_user_code(df):
    """
    Ordena o DataFrame pelo código da pessoa.

    Args:
        df: DataFrame pandas com os dados das multas

    Returns:
        DataFrame ordenado pelo código da pessoa
    """
    if 'Código da pessoa' in df.columns:
        return df.sort_values(by='Código da pessoa')
    else:
        print("Aviso: Coluna 'Código da pessoa' não encontrada.")
        return df

def extract_relevant_columns(df):
    """
    Extrai apenas as colunas relevantes para processamento.

    Args:
        df: DataFrame pandas com os dados completos

    Returns:
        DataFrame com apenas as colunas necessárias
    """
    # Lista das colunas que queremos extrair
    columns_to_extract = [
        "Código da pessoa",
        "Nome da pessoa",
        "Título",
        "Data de empréstimo",
        "Data devolução prevista",
        "Data devolução efetivada",
        "Valor multa",
        "Valor do desconto",
        "Número chave",  # Pode ser "Número da chave" em alguns arquivos
        "Email"
    ]

    # Verificar quais colunas existem no DataFrame
    available_columns = [col for col in columns_to_extract if col in df.columns]

    # Se "Número chave" não estiver disponível, tente "Número da chave"
    if "Número chave" not in available_columns and "Número da chave" in df.columns:
        available_columns.append("Número da chave")

    if not available_columns:
        raise ValueError("Nenhuma das colunas necessárias foi encontrada no arquivo.")

    return df[available_columns]

def format_date(date_str):
    """
    Formata uma data no formato brasileiro para ISO.

    Args:
        date_str: String de data no formato DD/MM/YYYY

    Returns:
        String de data no formato YYYY-MM-DD ou a string original se não for possível converter
    """
    if pd.isna(date_str) or not isinstance(date_str, str):
        return ""

    try:
        # Tenta converter do formato brasileiro para ISO
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        # Se falhar, retorna a string original
        return date_str

def group_fines_by_user(df):
    """
    Agrupa as multas por usuário e cria uma estrutura de dados adequada.

    Args:
        df: DataFrame pandas com os dados das multas

    Returns:
        Dicionário com dados agrupados por usuário
    """
    # Ordenar o DataFrame pelo código da pessoa
    df = sort_by_user_code(df)

    # Extrair colunas relevantes
    df_relevant = extract_relevant_columns(df)

    # Inicializar o dicionário de usuários
    users_data = {}

    # Iterar sobre as linhas do DataFrame
    for _, row in df_relevant.iterrows():
        user_code = str(row['Código da pessoa'])

        # Verificar se o usuário já existe no dicionário
        if user_code not in users_data:
            users_data[user_code] = {
                'codigo': user_code,
                'nome': row['Nome da pessoa'] if 'Nome da pessoa' in row else "",
                'email': row['Email'] if 'Email' in row else "",
                'total_multas': 0.0,  # Adicionar um campo para o total
                'multas': []
            }

        # Calcular o valor com desconto
        valor_multa = float(row['Valor multa']) if 'Valor multa' in row and pd.notna(row['Valor multa']) else 0.0
        valor_desconto = float(row['Valor do desconto']) if 'Valor do desconto' in row and pd.notna(row['Valor do desconto']) else 0.0
        valor_final = max(0, valor_multa - valor_desconto)  # Garantir que nunca seja negativo

        # Criar objeto de multa
        multa = {
            'titulo': row['Título'] if 'Título' in row else "",
            'data_emprestimo': format_date(row.get('Data de empréstimo', "")),
            'data_prevista': format_date(row.get('Data devolução prevista', "")),
            'data_efetivada': format_date(row.get('Data devolução efetivada', "")),
            'valor': valor_multa,
            'desconto': valor_desconto,
            'valor_final': valor_final,
            'numero_chave': row.get('Número chave', row.get('Número da chave', ""))
        }

        # Adicionar multa à lista de multas do usuário
        users_data[user_code]['multas'].append(multa)

        # Atualizar o total de multas do usuário
        users_data[user_code]['total_multas'] += valor_final

    return users_data

def print_users_summary(users_data):
    """
    Imprime um resumo das multas por usuário.

    Args:
        users_data: Dicionário com dados agrupados por usuário
    """
    print("\nResumo de multas por usuário:")
    print("=" * 80)
    print(f"{'Código':<15} {'Nome':<30} {'Total':<10} {'Qtd. Multas':<10}")
    print("-" * 80)

    # Ordenar por valor total (decrescente)
    sorted_users = sorted(users_data.values(), key=lambda x: x['total_multas'], reverse=True)

    for user in sorted_users:
        print(f"{user['codigo']:<15} {user['nome'][:28]:<30} R$ {user['total_multas']:<8.2f} {len(user['multas']):<10}")

    print("=" * 80)

# Modificar a função generate_json_file para incluir totais
def generate_json_file(df, output_path="multas_usuarios.json"):
    """
    Gera um arquivo JSON com as multas agrupadas por usuário.

    Args:
        df: DataFrame pandas com os dados das multas
        output_path: Caminho para salvar o arquivo JSON

    Returns:
        Caminho do arquivo JSON gerado
    """
    # Obter dados agrupados
    users_data = group_fines_by_user(df)

    # Imprimir resumo de usuários
    print_users_summary(users_data)

    # Converter para lista (formato mais comum para JSON)
    users_list = list(users_data.values())

    # Gravar arquivo JSON
    with open(output_path, 'w', encoding='utf-8') as json_file:
        json.dump(users_list, json_file, ensure_ascii=False, indent=2)

    print(f"Arquivo JSON gerado com sucesso: {output_path}")
    return output_path

def get_fines_summary(df):
    """
    Gera um resumo estatístico das multas.

    Args:
        df: DataFrame pandas com os dados das multas

    Returns:
        Dicionário com estatísticas das multas
    """
    users_data = group_fines_by_user(df)

    total_users = len(users_data)
    total_fines = sum(len(user['multas']) for user in users_data.values())
    total_value = sum(sum(multa['valor'] for multa in user['multas']) for user in users_data.values())

    # Identificar usuário com maior número de multas
    if users_data:
        max_fines_user = max(users_data.values(), key=lambda x: len(x['multas']))
        max_fines_count = len(max_fines_user['multas'])
        max_fines_user_name = max_fines_user['nome']
    else:
        max_fines_user_name = "N/A"
        max_fines_count = 0

    return {
        'total_users': total_users,
        'total_fines': total_fines,
        'total_value': total_value,
        'max_fines_user': max_fines_user_name,
        'max_fines_count': max_fines_count
    }

# Função de teste do módulo
if __name__ == "__main__":
    from read_excel import read_excel_file, clean_column_names

    try:
        # Carregar um arquivo de exemplo (substitua pelo caminho real)
        file_path = 'elian.oliveira_2025-03-26-22-56-55.xlsx'

        # Corrigindo: primeiro desativa a verificação de data, depois limpa colunas
        df = read_excel_file(file_path, verificar_data=False)
        df = clean_column_names(df)

        # Testar o processamento
        json_path = generate_json_file(df)

        # Mostrar resumo
        summary = get_fines_summary(df)
        print("\nResumo das multas:")
        print(f"Total de usuários com multas: {summary['total_users']}")
        print(f"Total de multas: {summary['total_fines']}")
        print(f"Valor total: R$ {summary['total_value']:.2f}")
        print(f"Usuário com mais multas: {summary['max_fines_user']} ({summary['max_fines_count']} multas)")

    except Exception as e:
        print(f"Erro: {str(e)}")