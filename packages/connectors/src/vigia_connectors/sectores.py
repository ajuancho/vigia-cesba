"""Etiquetado barato de sector por keywords (compartido por todos los conectores)."""
from __future__ import annotations

_RULES: list[tuple[str, list[str]]] = [
    ("Energía", ["VACA MUERTA", "PETRÓLEO", "PETROLEO", " GAS ", "GNL", "HIDROCARBURO", "ENERGIA", "ENERGÍA", "ENARGAS", "ENREGE", "ENRE)", "REGULADOR DE LA ELECTRICIDAD", "CAMMESA", "RENOVABLE", "ELÉCTRIC", "ELECTRIC"]),
    ("Minería", ["LITIO", "MINERIA", "MINERÍA", "MINERA ", "ORO", "COBRE", "SEGEMAR"]),
    ("Agro", ["AGROPECUAR", "GRANOS", "SENASA", "BIOECONOMIA", "BIOECONOMÍA", "GANADER"]),
    ("Tecnología", ["SOFTWARE", "ECONOMIA DEL CONOCIMIENTO", "ECONOMÍA DEL CONOCIMIENTO", "CIBERSEGURIDAD", "INTELIGENCIA ARTIFICIAL", "DATA CENTER"]),
    ("Economía", ["BCRA", "BANCO CENTRAL", "AFIP", "ARCA", "IMPOSITIV", "TRIBUTARI", "ADUANA", "FINANCIER", "SUPERINTENDENCIA DE SEGUROS", "UNIDAD DE INFORMACION FINANCIERA", "UNIDAD DE INFORMACIÓN FINANCIERA"]),
    ("Salud", ["SALUD", "HOSPITAL", "MEDICAMENTO", "ANMAT", "SANITARI"]),
    ("Educación", ["EDUCACION", "EDUCACIÓN", "UNIVERSIDAD", "ESCUELA", "DOCENTE"]),
    ("Trabajo", ["TRABAJO", "SALARIO", "SMVM", "LABORAL", "EMPLEO", "ANSES", "ANSeS", "JUBILA"]),
    ("Transporte", ["TRANSPORTE", "AUTOMOTOR", "AERONAUT", "FERROVIAR", "VIAL"]),
    ("Ambiente", ["AMBIENTE", "AMBIENTAL", "CLIMATIC", "BOSQUE", "GLACIAR"]),
    ("Justicia", ["CODIGO PENAL", "CÓDIGO PENAL", "JUDICIAL", "MAGISTRAT", "FISCALIA", "FISCALÍA"]),
    ("Seguridad", ["SEGURIDAD", "POLICIA", "POLICÍA", "DEFENSA NACIONAL"]),
]


def detect_sector(*parts: str | None) -> str | None:
    """Devuelve el primer sector cuyos keywords aparezcan en el texto combinado."""
    haystack = " ".join(p for p in parts if p).upper()
    if not haystack:
        return None
    for sector, keywords in _RULES:
        for kw in keywords:
            if kw in haystack:
                return sector
    return None
