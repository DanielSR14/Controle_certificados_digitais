"""Geração de mensagens personalizadas de aviso de vencimento."""
from flask import Blueprint, make_response, redirect, render_template, request, url_for

from src import db
from src.domain import (
    VENCE_EM_BREVE, VENCIDO,
    anotar_situacao, montar_contexto_mensagem, montar_mensagem, numero_whatsapp,
)

bp = Blueprint("mensagens", "mensagens", url_prefix="/mensagens")


def _opcoes_ativos():
    dias_aviso = int(db.get_config("dias_aviso", 30))
    df = anotar_situacao(db.listar_certificados(), dias_aviso)
    ativos = df[df["situacao"].isin([VENCIDO, VENCE_EM_BREVE])].sort_values("dias_restantes")
    return ativos


def _montar_painel(cert_id):
    cert = db.obter_certificado(cert_id)
    if not cert:
        return None
    config = db.get_all_config()
    dias_aviso = int(config.get("dias_aviso", 30))
    df = anotar_situacao(db.listar_certificados().query("id == @cert_id"), dias_aviso)
    linha = df.to_dict("records")[0]
    contexto = montar_contexto_mensagem(cert, config)
    mensagem = montar_mensagem(config.get("template_mensagem", ""), contexto)
    return dict(cert=cert, linha=linha, mensagem=mensagem, numero=numero_whatsapp(cert.get("telefone", "")))


@bp.route("/")
def individual():
    ativos = _opcoes_ativos()
    if ativos.empty:
        return render_template("mensagens.html", vazio=True)

    cert_id = request.args.get("cert_id", type=int) or int(ativos.iloc[0]["id"])
    painel = _montar_painel(cert_id) or _montar_painel(int(ativos.iloc[0]["id"]))

    return render_template(
        "mensagens.html", vazio=False,
        opcoes=ativos.to_dict("records"), cert_id_selecionado=cert_id,
        painel=painel,
    )


@bp.route("/painel")
def painel():
    cert_id = request.args.get("cert_id", type=int)
    if not request.headers.get("HX-Request"):
        return redirect(url_for("mensagens.individual", cert_id=cert_id))
    dados = _montar_painel(cert_id) if cert_id else None
    resp = make_response(render_template("partials/_mensagem_painel.html", painel=dados))
    resp.headers["HX-Push-Url"] = url_for("mensagens.individual", cert_id=cert_id)
    return resp
