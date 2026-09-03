"""Testes de fumaça: a aplicação sobe e as telas principais respondem 200.

Cada teste usa um diretório de dados temporário, sem tocar em `data/`.
"""
import importlib
import tempfile
from pathlib import Path

import pytest


@pytest.fixture()
def client(monkeypatch):
    tmp = Path(tempfile.mkdtemp())
    from src import db

    monkeypatch.setattr(db, "DATA_DIR", tmp)
    monkeypatch.setattr(db, "ARQUIVOS_DIR", tmp / "arquivos")
    monkeypatch.setattr(db, "DB_PATH", tmp / "certificados.db")

    import webapp

    importlib.reload(webapp)
    app = webapp.create_app()
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.mark.parametrize(
    "url",
    ["/", "/certificados/", "/certificados/tabela", "/mensagens/", "/configuracoes/"],
)
def test_paginas_respondem(client, url):
    assert client.get(url).status_code == 200


def test_situacao_e_mensagem():
    from datetime import date

    from src.domain import VENCIDO, VALIDO, calcular_situacao, link_whatsapp

    assert calcular_situacao("2000-01-01", "ativo", 30) == VENCIDO
    assert calcular_situacao("2999-01-01", "ativo", 30) == VALIDO
    assert calcular_situacao(date.today().isoformat(), "cancelado", 30) == "Cancelado"
    assert link_whatsapp("(11) 91234-5678", "oi").startswith("https://wa.me/5511912345678")
