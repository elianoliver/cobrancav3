from datetime import datetime

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

# Dados do exemplo
data_prevista = "15/07/2024"
data_efetiva = "06/08/2024"

# Calcular dias de atraso
dias_atraso = calculate_days_difference(data_prevista, data_efetiva)

print(f"Data Prevista: {data_prevista}")
print(f"Data de Devolução Efetiva: {data_efetiva}")
print(f"Dias de Atraso: {dias_atraso}")

# Teste adicional com formato de data diferente
data_prevista2 = "2024-07-15"
data_efetiva2 = "2024-08-06"

dias_atraso2 = calculate_days_difference(data_prevista2, data_efetiva2)

print(f"\nTeste com formato alternativo:")
print(f"Data Prevista: {data_prevista2}")
print(f"Data de Devolução Efetiva: {data_efetiva2}")
print(f"Dias de Atraso: {dias_atraso2}")