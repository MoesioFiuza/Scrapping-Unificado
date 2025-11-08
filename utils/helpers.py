import re
from typing import Optional

def limpar_numero_processo(numero: str) -> str:
    return re.sub(r'[^\d\.\-]', '', numero)

def validar_numero_processo(numero: str) -> bool:
    pattern = r'\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}'
    return bool(re.match(pattern, numero))