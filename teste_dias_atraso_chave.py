from datetime import datetime
import pandas as pd

def calculate_days_difference(date1, date2):
    """Calcula a diferença em dias entre duas datas."""
    # Converter para objetos datetime
    if isinstance(date1, str):
        try:
            date1 = datetime.strptime(date1, '%d/%m/%Y')
        except ValueError:
            try:
                date1 = datetime.strptime(date1, '%Y-%m-%d')
            except ValueError:
                return 0

    if isinstance(date2, str):
        try:
            date2 = datetime.strptime(date2, '%d/%m/%Y')
        except ValueError:
            try:
                date2 = datetime.strptime(date2, '%Y-%m-%d')
            except ValueError:
                return 0

    # Garantir que são objetos datetime
    if not isinstance(date1, datetime):
        return 0

    if not isinstance(date2, datetime):
        return 0

    # Calcular diferença
    delta = date2 - date1
    return max(0, delta.days)  # Garantir que não seja negativo

def format_date(date_value):
    """Formata uma data para o padrão DD/MM/YYYY."""
    if isinstance(date_value, pd.Timestamp):
        return date_value.strftime('%d/%m/%Y')
    elif isinstance(date_value, datetime):
        return date_value.strftime('%d/%m/%Y')
    elif isinstance(date_value, str):
        # Tentar converter string para data e depois formatar
        try:
            date_obj = datetime.strptime(date_value, '%Y-%m-%d')
            return date_obj.strftime('%d/%m/%Y')
        except ValueError:
            try:
                date_obj = datetime.strptime(date_value, '%d/%m/%Y')
                return date_value  # Já está no formato correto
            except ValueError:
                return date_value  # Retornar como está se não conseguir converter
    return str(date_value)  # Fallback para qualquer outro caso

# Teste para o caso da Clara com a chave
print("=== Teste de cálculo de dias atrasados para chave ===")

# Dados originais do caso
titulo = "Chave: 68"
data_emp = "20/03/2025"
data_prev = "20/03/2025"
data_efet = "26/03/2025"
valor_multa = 6.0

# Método antigo (cálculo com base nas datas)
dias_atraso_data = calculate_days_difference(data_prev, data_efet)
print(f"Dias de atraso calculados pelo método de datas: {dias_atraso_data}")

# Método novo (com base no valor da multa)
dias_atraso_multa = int(valor_multa)
print(f"Dias de atraso calculados pelo valor da multa: {dias_atraso_multa}")

# Simular chave
multa = {
    'titulo': titulo,
    'data_emprestimo': data_emp,
    'data_prevista': data_prev,
    'data_efetivada': data_efet,
    'valor': valor_multa
}

# Teste com lógica modificada
eh_chave = 'Chave:' in multa['titulo']
dias_atraso = ''

if eh_chave:
    # Para chaves, usar o valor da multa como dias de atraso (R$ 1,00 por dia)
    valor = float(multa.get('valor', 0))
    dias_atraso = str(int(valor))
else:
    # Para outros itens, calcular pela data
    dias_atraso = str(calculate_days_difference(multa['data_prevista'], multa['data_efetivada']))

print(f"Resultado final com a lógica corrigida: {dias_atraso}")

print("\n=== Dados do caso ===")
print(f"Título: {titulo}")
print(f"Data de Empréstimo: {data_emp}")
print(f"Data de Devolução Prevista: {data_prev}")
print(f"Data de Devolução Efetiva: {data_efet}")
print(f"Valor da multa: R$ {valor_multa:.2f}")
print(f"Dias de Atraso (correto): {dias_atraso}")