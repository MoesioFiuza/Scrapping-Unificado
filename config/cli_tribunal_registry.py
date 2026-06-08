
from __future__ import annotations

CLI_TRIBUNAL_REGISTRY: dict[str, dict] = {
    "8.06": {
        "chrome": {
            "helpers": "scrapers.tjce.cli_helpers",
            "movimentacoes": True,
            "planilhas": True,
            "polos": True,
        },
        "edge": {
            "helpers": "scrapers.tjce.cli_helpers_edge",
            "movimentacoes": True,
            "planilhas": True,
            "polos": True,
        },
    },
    "8.06_esaj": {
        "chrome": {
            "helpers": "scrapers.tjce_esaj.cli_helpers",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
        "edge": {
            "helpers": "scrapers.tjce_esaj.cli_helpers_edge",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
    },
    "8.13": {
        "chrome": {
            "helpers": "scrapers.tjmg.cli_helpers",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
        "edge": {
            "helpers": "scrapers.tjmg.cli_helpers_edge",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
    },
    "8.17": {
        "chrome": {
            "helpers": "scrapers.tjpe.cli_helpers",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
        "edge": {
            "helpers": "scrapers.tjpe.cli_helpers_edge",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
    },
    "8.10": {
        "chrome": {
            "helpers": "scrapers.tjma.cli_helpers",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
        "edge": {
            "helpers": "scrapers.tjma.cli_helpers_edge",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
    },
    "8.07": {
        "chrome": {
            "helpers": "scrapers.tjdft.cli_helpers",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
        "edge": {
            "helpers": "scrapers.tjdft.cli_helpers_edge",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
    },
    "8.02": {
        "chrome": {
            "helpers": "scrapers.tjal.cli_helpers",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
        "edge": {
            "helpers": "scrapers.tjal.cli_helpers_edge",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
    },
    "8.26": {
        "chrome": {
            "helpers": "scrapers.tjsp.cli_helpers",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
        "edge": {
            "helpers": "scrapers.tjsp.cli_helpers_edge",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
    },
    "8.20": {
        "chrome": {
            "helpers": "scrapers.tjrn.cli_helpers",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
        "edge": {
            "helpers": "scrapers.tjrn.cli_helpers_edge",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
    },
    "8.19": {
        "chrome": {
            "helpers": "scrapers.tjrj.cli_helpers",
            "movimentacoes": True,
            "planilhas": True,
            "polos": False,
        },
        "edge": {
            "helpers": "scrapers.tjrj.cli_helpers_edge",
            "movimentacoes": True,
            "planilhas": True,
            "polos": True,
        },
    },
}


def listar_opcoes_por_tribunal() -> dict[str, dict]:
    """Para API: { codigo: { chrome: {movimentacoes, planilhas, polos}, edge: {...} } }"""
    out: dict[str, dict] = {}
    for codigo, browsers in CLI_TRIBUNAL_REGISTRY.items():
        out[codigo] = {}
        for br, caps in browsers.items():
            out[codigo][br] = {
                "movimentacoes": bool(caps.get("movimentacoes")),
                "planilhas": bool(caps.get("planilhas")),
                "polos": bool(caps.get("polos")),
            }
    return out


def obter_helpers(tribunal_key: str, browser: str) -> str | None:
    """browser: 'chrome' | 'edge'"""
    br = (browser or "chrome").lower()
    if br not in ("chrome", "edge"):
        return None
    t = CLI_TRIBUNAL_REGISTRY.get(tribunal_key)
    if not t:
        return None
    entry = t.get(br)
    return entry.get("helpers") if entry else None


def modo_permitido(tribunal_key: str, browser: str, modo: str) -> bool:
    t = CLI_TRIBUNAL_REGISTRY.get(tribunal_key)
    if not t:
        return False
    br = (browser or "chrome").lower()
    entry = t.get(br)
    if not entry:
        return False
    modo = (modo or "").lower()
    if modo == "movimentacoes":
        return bool(entry.get("movimentacoes"))
    if modo == "planilhas":
        return bool(entry.get("planilhas"))
    if modo == "polos":
        return bool(entry.get("polos"))
    return False
