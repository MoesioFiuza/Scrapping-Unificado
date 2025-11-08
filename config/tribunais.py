from config.settings import *

TRIBUNAIS_MAP = {
    "8.19": {
        "nome": "TJRJ",
        "url_login": "https://tjrj.pje.jus.br/pje/ConsultaPublica/listView.seam",
        "url_consulta": "https://tjrj.pje.jus.br/pje/ConsultaPublica/listView.seam",
        "modulo_scraper": "scrapers.tjrj.scraper",
        "classe_scraper": "PJeScraperTJRJ",
        "ramo_justica": "8",
        "tribunal_cnj": "19",
    },
    "8.06": {
        "nome": "TJCE",
        "url_login": "https://pje-consulta.tjce.jus.br/pje1grau/ConsultaPublica/listView.seam",
        "url_consulta": "https://pje-consulta.tjce.jus.br/pje1grau/ConsultaPublica/listView.seam",
        "modulo_scraper": "scrapers.tjce.scrapper",
        "classe_scraper": "PJeScraperTJCE",
        "ramo_justica": "8",
        "tribunal_cnj": "06",
    },
    "8.13": {
        "nome": "TJMG",
        "url_login": "https://pjerecursal.tjmg.jus.br/pje/ConsultaPublica/listView.seam",
        "url_consulta": "https://pjerecursal.tjmg.jus.br/pje/ConsultaPublica/listView.seam",
        "modulo_scraper": "scrapers.tjmg.scraper",
        "classe_scraper": "PJeScraperTJMG",
        "ramo_justica": "8",
        "tribunal_cnj": "13",
    },
    "8.17": {
        "nome": "TJPE",
        "url_login": "https://pje.cloud.tjpe.jus.br/1g/ConsultaPublica/listView.seam",
        "url_consulta": "https://pje.cloud.tjpe.jus.br/1g/ConsultaPublica/listView.seam",
        "modulo_scraper": "scrapers.tjpe.scraper",
        "classe_scraper": "PJeScraperTJPE",
        "ramo_justica": "8",
        "tribunal_cnj": "17",
    },
}

def identificar_tribunal_por_processo(numero_processo):
    import re
    match = re.match(r'\d{7}-\d{2}\.\d{4}\.(\d{1})\.(\d{2})\.\d{4}', str(numero_processo))
    if match:
        ramo, tribunal = match.groups()
        chave = f"{ramo}.{tribunal}"
        if chave in TRIBUNAIS_MAP:
            return chave
    return None