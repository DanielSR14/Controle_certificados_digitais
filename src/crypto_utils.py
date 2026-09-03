"""Criptografia local das senhas dos certificados (.pfx) em repouso.

A chave fica em data/.secret.key (fora do controle de versao). Isso nao
protege contra quem tem acesso ao disco local, mas evita guardar as senhas
em texto puro dentro do banco de dados.
"""
from pathlib import Path

from cryptography.fernet import Fernet

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KEY_PATH = DATA_DIR / ".secret.key"


def _get_key() -> bytes:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not KEY_PATH.exists():
        KEY_PATH.write_bytes(Fernet.generate_key())
    return KEY_PATH.read_bytes()


def _fernet() -> Fernet:
    return Fernet(_get_key())


def encrypt(texto: str) -> str:
    if not texto:
        return ""
    return _fernet().encrypt(texto.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception:
        return ""
