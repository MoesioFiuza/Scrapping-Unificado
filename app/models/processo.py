from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class Processo:
    id: int
    numero_processo: str
    tribunal: Optional[str]
    status: str = 'pendente'
    dados: Optional[Dict[str, Any]] = None
    erro: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'numero_processo': self.numero_processo,
            'tribunal': self.tribunal,
            'status': self.status,
            'dados': self.dados,
            'erro': self.erro
        }