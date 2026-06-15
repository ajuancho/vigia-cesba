"""Tests del etiquetado de emisor (organismo canónico) por keywords."""
from __future__ import annotations

from vigia_connectors.emisores import detect_emisor


def test_arca_y_afip_y_regionales():
    assert detect_emisor("ADMINISTRACION FEDERAL DE INGRESOS PUBLICOS") == "ARCA"
    assert detect_emisor("AGENCIA DE RECAUDACION Y CONTROL ADUANERO") == "ARCA"
    assert detect_emisor("DIRECCION REGIONAL COMODORO RIVADAVIA (AFIP-DGI)") == "ARCA"


def test_cnv_con_y_sin_tilde():
    assert detect_emisor("COMISION NACIONAL DE VALORES") == "CNV"
    assert detect_emisor("COMISIÓN NACIONAL DE VALORES") == "CNV"


def test_cndc_y_secretaria_competencia():
    assert detect_emisor("COMISION NACIONAL DE DEFENSA DE LA COMPETENCIA") == "CNDC"
    assert detect_emisor("SECRETARIA DE DEFENSA DE LA COMPETENCIA Y DEL CONSUMIDOR") == "CNDC"


def test_no_confunde_competencias_deportivas():
    # "COMPETENCIAS NACIONALES" (deportes) no debe matchear CNDC.
    assert detect_emisor("SUBSECRETARIA DE INFRAESTRUCTURA DEPORTIVA Y COMPETENCIAS NACIONALES") is None


def test_reguladores_sectoriales():
    assert detect_emisor("BANCO CENTRAL DE LA REPUBLICA ARGENTINA (B.C.R.A.)") == "BCRA"
    assert detect_emisor("ENTE NACIONAL DE COMUNICACIONES") == "ENACOM"
    assert detect_emisor("SUPERINTENDENCIA DE SEGUROS DE LA NACION") == "SSN"
    assert detect_emisor("ADM.NAC.DE MEDICAMENTOS, ALIMENTOS Y TEC. MEDICA") == "ANMAT"


def test_sin_match():
    assert detect_emisor("MINISTERIO DE ECONOMIA") is None
    assert detect_emisor("Honorable Cámara de Diputados de la Nación") is None
    assert detect_emisor() is None
    assert detect_emisor(None, "") is None
