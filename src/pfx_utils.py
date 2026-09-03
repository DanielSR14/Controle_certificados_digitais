"""Leitura de arquivos de certificado digital .pfx/.p12 e parsing de nomes de arquivo."""
import re
from datetime import date
from typing import Optional

from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID


class PfxError(Exception):
    pass


def _nome_atributo(name, oid) -> str:
    attrs = name.get_attributes_for_oid(oid)
    return attrs[0].value if attrs else ""


def extrair_info_pfx(conteudo: bytes, senha: str) -> dict:
    """Abre o .pfx com a senha informada e devolve os dados do certificado.

    Lança PfxError se a senha estiver incorreta ou o arquivo for inválido.
    """
    senha_bytes = senha.encode("utf-8") if senha else None
    try:
        _chave, certificado, _extras = pkcs12.load_key_and_certificates(conteudo, senha_bytes)
    except Exception as exc:
        raise PfxError(
            "Não foi possível abrir o certificado. Verifique se a senha está correta "
            "e se o arquivo é um .pfx/.p12 válido."
        ) from exc

    if certificado is None:
        raise PfxError("O arquivo não contém um certificado válido.")

    subject = certificado.subject
    issuer = certificado.issuer
    subject_cn = _nome_atributo(subject, NameOID.COMMON_NAME)
    issuer_cn = _nome_atributo(issuer, NameOID.COMMON_NAME)

    try:
        not_before = certificado.not_valid_before_utc.date()
        not_after = certificado.not_valid_after_utc.date()
    except AttributeError:  # cryptography < 42
        not_before = certificado.not_valid_before.date()
        not_after = certificado.not_valid_after.date()

    empresa_sugerida, cnpj_sugerido = "", ""
    if ":" in subject_cn:
        partes = subject_cn.split(":", 1)
        empresa_sugerida = partes[0].strip()
        possivel_doc = re.sub(r"\D", "", partes[1])
        if len(possivel_doc) in (11, 14):
            cnpj_sugerido = possivel_doc
    else:
        empresa_sugerida = subject_cn

    return {
        "subject_cn": subject_cn,
        "issuer_cn": issuer_cn,
        "data_emissao": not_before.isoformat(),
        "data_validade": not_after.isoformat(),
        "numero_serie": format(certificado.serial_number, "X"),
        "empresa_sugerida": empresa_sugerida,
        "cnpj_sugerido": cnpj_sugerido,
    }


NOME_ARQUIVO_RE = re.compile(
    r"certificado\s+digital\s+(?P<empresa>.+?)\s+validade\s+"
    r"(?P<dia>\d{1,2})\s+(?P<mes>\d{1,2})\s+(?P<ano>\d{4})\s*-\s*senha\s+(?P<senha>\S+)",
    re.IGNORECASE,
)


def parse_nome_arquivo(nome_arquivo: str) -> Optional[dict]:
    """Extrai empresa, validade e senha de nomes como:

    'Certificado Digital Exemplo Comercio LTDA Validade 18 02 2027 - Senha 123456.pfx'

    Serve apenas como sugestão de preenchimento/importação em lote; a validade
    real sempre deve ser conferida abrindo o arquivo com `extrair_info_pfx`.
    """
    base = re.sub(r"\.(pfx|p12)$", "", nome_arquivo.strip(), flags=re.IGNORECASE)
    m = NOME_ARQUIVO_RE.search(base)
    if not m:
        return None
    dia, mes, ano = int(m.group("dia")), int(m.group("mes")), int(m.group("ano"))
    try:
        validade = date(ano, mes, dia)
    except ValueError:
        return None
    return {
        "empresa": m.group("empresa").strip(),
        "senha": m.group("senha").strip(),
        "data_validade": validade.isoformat(),
    }
