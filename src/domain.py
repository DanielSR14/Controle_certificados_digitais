"""Regras de negócio: situação do certificado, saudação e montagem de mensagens."""
import re
from datetime import date, datetime
from urllib.parse import quote

import pandas as pd

VENCIDO = "Vencido"
VENCE_EM_BREVE = "Vence em breve"
VALIDO = "Válido"
CANCELADO = "Cancelado"

# Paleta de status validada pela skill de dataviz (fixa, nunca reaproveitada
# para séries categóricas).
COR_STATUS = {
    VALIDO: "#0ca30c",
    VENCE_EM_BREVE: "#fab219",
    VENCIDO: "#d03b3b",
    CANCELADO: "#898781",
}

BADGE_CLASSES = {
    VALIDO: "badge-valido",
    VENCE_EM_BREVE: "badge-vence-em-breve",
    VENCIDO: "badge-vencido",
    CANCELADO: "badge-cancelado",
}


def badge_class(situacao: str) -> str:
    return BADGE_CLASSES.get(situacao, "badge-cancelado")


def dias_restantes(data_validade: str, hoje: date = None) -> int:
    hoje = hoje or date.today()
    validade = datetime.fromisoformat(data_validade).date()
    return (validade - hoje).days


def calcular_situacao(data_validade: str, status: str, dias_aviso: int, hoje: date = None) -> str:
    if status == "cancelado":
        return CANCELADO
    dias = dias_restantes(data_validade, hoje)
    if dias < 0:
        return VENCIDO
    if dias <= dias_aviso:
        return VENCE_EM_BREVE
    return VALIDO


def anotar_situacao(df, dias_aviso: int):
    """Adiciona as colunas dias_restantes/situacao a um DataFrame de certificados."""
    df = df.copy()
    if df.empty:
        df["dias_restantes"] = pd.Series(dtype="int64")
        df["situacao"] = pd.Series(dtype="object")
        return df
    df["dias_restantes"] = df["data_validade"].apply(dias_restantes)
    df["situacao"] = df.apply(
        lambda r: calcular_situacao(r["data_validade"], r["status"], dias_aviso), axis=1
    )
    return df


def saudacao_atual(agora: datetime = None) -> str:
    agora = agora or datetime.now()
    hora = agora.hour
    if hora < 12:
        return "Bom dia"
    if hora < 18:
        return "Boa tarde"
    return "Boa noite"


def formatar_data_br(data_iso: str) -> str:
    try:
        return datetime.fromisoformat(data_iso).strftime("%d/%m/%Y")
    except ValueError:
        return data_iso


def formatar_documento(valor: str) -> str:
    """Formata CPF (11 dígitos) ou CNPJ (14 dígitos) no padrão oficial.
    Valores com outra quantidade de dígitos são devolvidos como vieram."""
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) == 11:
        return f"{digitos[0:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:11]}"
    if len(digitos) == 14:
        return f"{digitos[0:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:14]}"
    return valor or ""


PLACEHOLDERS = [
    ("{SAUDACAO}", "Bom dia / Boa tarde / Boa noite (calculado na hora)"),
    ("{NOME_SOCIO}", "Nome do sócio/responsável pela empresa"),
    ("{EMPRESA}", "Nome da empresa"),
    ("{CNPJ}", "CNPJ da empresa"),
    ("{DIAS}", "Dias restantes até o vencimento (ou dias vencido, sem sinal)"),
    ("{SITUACAO_VENCIMENTO}", "Frase pronta: \"vence em X dia(s)\" ou \"está vencido há X dia(s)\""),
    ("{DATA_VENCIMENTO}", "Data de vencimento (dd/mm/aaaa)"),
    ("{NOME_ESCRITORIO}", "Nome do escritório de contabilidade"),
    ("{ASSINATURA}", "Assinatura usada ao final da mensagem"),
]


def montar_contexto_mensagem(cert: dict, config: dict) -> dict:
    dias_aviso = int(config.get("dias_aviso", 30))
    dias = dias_restantes(cert["data_validade"])
    if dias >= 0:
        situacao_vencimento = "vence em {} dia(s)".format(dias)
    else:
        situacao_vencimento = "está vencido há {} dia(s)".format(-dias)
    return {
        "SAUDACAO": saudacao_atual(),
        "NOME_SOCIO": cert.get("nome_socio") or "responsável",
        "EMPRESA": cert.get("empresa") or "",
        "CNPJ": cert.get("cnpj") or "",
        "DIAS": str(dias) if dias >= 0 else str(-dias),
        "SITUACAO_VENCIMENTO": situacao_vencimento,
        "DATA_VENCIMENTO": formatar_data_br(cert["data_validade"]),
        "NOME_ESCRITORIO": config.get("nome_escritorio", ""),
        "ASSINATURA": config.get("assinatura", ""),
    }


def montar_mensagem(template: str, contexto: dict) -> str:
    texto = template
    for chave, valor in contexto.items():
        texto = texto.replace(f"{{{chave}}}", str(valor))
    return texto


def numero_whatsapp(telefone: str) -> str:
    """Normaliza um telefone brasileiro para o formato aceito pelo wa.me (com DDI)."""
    numero = re.sub(r"\D", "", telefone or "")
    if not numero:
        return ""
    if len(numero) <= 11:
        numero = "55" + numero
    return numero


def link_whatsapp(telefone: str, mensagem: str) -> str:
    numero = numero_whatsapp(telefone)
    if not numero:
        return ""
    return f"https://wa.me/{numero}?text={quote(mensagem)}"
