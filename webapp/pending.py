"""Área de estágio em memória para fluxos de dois passos (validar -> confirmar):
upload de novo certificado, renovação e importação em lote. Uso local de
processo único, sem necessidade de um backend externo."""
import time
import uuid

_STORE: dict[str, dict] = {}
_TTL_SEGUNDOS = 1800


def _limpar_expirados():
    agora = time.time()
    for chave in [k for k, v in _STORE.items() if agora - v["_ts"] > _TTL_SEGUNDOS]:
        _STORE.pop(chave, None)


def guardar(dados: dict) -> str:
    _limpar_expirados()
    token = uuid.uuid4().hex
    dados = {**dados, "_ts": time.time()}
    _STORE[token] = dados
    return token


def obter(token: str) -> dict | None:
    _limpar_expirados()
    return _STORE.get(token)


def remover(token: str):
    _STORE.pop(token, None)
