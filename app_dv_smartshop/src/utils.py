# filepath: c:\Tempd\app_dv_smartshop\src\utils.py
def formatar_numero(valor):
    """
    Formata um número inteiro ou float para usar o ponto como separador de milhar.
    
    Args:
        valor (int ou float): O número a ser formatado.
    
    Returns:
        str: O número formatado como string.
    """
    try:
        if isinstance(valor, (int, float)):
            return f"{valor:,}".replace(",", ".")  # Substitui vírgula por ponto
        else:
            return str(valor)  # Retorna como string se não for numérico
    except Exception:
        return str(valor)  # Fallback para qualquer erro    

def validar_email(email):
    """
    Valida se um endereço de e-mail é válido.
    
    Args:
        email (str): O endereço de e-mail a ser validado.
    
    Returns:
        bool: True se o e-mail for válido, False caso contrário.
    """
    import re
    padrao_email = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(padrao_email, email) is not None

def gerar_id_unico():
    """
    Gera um ID único usando o UUID.
    
    Returns:
        str: Um ID único.
    """
    import uuid
    return str(uuid.uuid4())