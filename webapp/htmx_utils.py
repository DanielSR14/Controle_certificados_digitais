"""Helpers para respostas htmx (fragmentos + evento de toast via cabeçalho HX-Trigger)."""
import json

from flask import make_response


def with_toast(html: str, mensagem: str, categoria: str = "success", **extra_triggers):
    resp = make_response(html)
    triggers = {"appToast": {"mensagem": mensagem, "categoria": categoria}}
    triggers.update(extra_triggers)
    resp.headers["HX-Trigger"] = json.dumps(triggers)
    return resp
