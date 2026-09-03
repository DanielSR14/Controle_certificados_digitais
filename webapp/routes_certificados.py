"""Cadastro, edição, renovação e exclusão de certificados digitais."""
import os

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, send_file, url_for

from src import db
from src.crypto_utils import decrypt, encrypt
from src.domain import (
    CANCELADO, VALIDO, VENCE_EM_BREVE, VENCIDO,
    anotar_situacao, badge_class, formatar_data_br,
)
from src.pfx_utils import PfxError, extrair_info_pfx
from webapp import pending
from webapp.htmx_utils import with_toast

bp = Blueprint("certificados", "certificados", url_prefix="/certificados")

SITUACOES_PADRAO = [VALIDO, VENCE_EM_BREVE, VENCIDO]
PAGE_SIZE = 30


def _dias_aviso() -> int:
    return int(db.get_config("dias_aviso", 30))


def _filtrar(args):
    df = anotar_situacao(db.listar_certificados(), _dias_aviso())
    situacoes = args.getlist("situacao") or SITUACOES_PADRAO
    filtrado = df[df["situacao"].isin(situacoes)]
    busca = (args.get("busca") or "").strip().lower()
    if busca:
        filtrado = filtrado[
            filtrado["empresa"].str.lower().str.contains(busca, na=False)
            | filtrado["nome_socio"].str.lower().str.contains(busca, na=False)
            | filtrado["cnpj"].str.lower().str.contains(busca, na=False)
        ]
    return filtrado


def _url_pagina(args, offset):
    kwargs = {"offset": offset}
    if args.get("busca"):
        kwargs["busca"] = args.get("busca")
    situacoes = args.getlist("situacao")
    if situacoes:
        kwargs["situacao"] = situacoes
    return url_for("certificados.tabela_mais", **kwargs)


def _paginar(filtrado, args):
    total = len(filtrado)
    pagina = filtrado.iloc[:PAGE_SIZE]
    tem_mais = total > PAGE_SIZE
    proxima_url = _url_pagina(args, PAGE_SIZE) if tem_mais else None
    return pagina, total, tem_mais, proxima_url


def _render_tabela(args, oob=False):
    filtrado = _filtrar(args)
    pagina, total, tem_mais, proxima_url = _paginar(filtrado, args)
    return render_template(
        "partials/_tabela_certificados.html",
        certificados=pagina.to_dict("records"), total=total,
        tem_mais=tem_mais, proxima_url=proxima_url, oob=oob,
    )


def _render_painel(cert_id, extra=None):
    cert = db.obter_certificado(cert_id)
    if not cert:
        return ""
    dias_aviso = _dias_aviso()
    df = anotar_situacao(db.listar_certificados().query("id == @cert_id"), dias_aviso)
    linha = df.to_dict("records")[0]
    return render_template(
        "partials/_painel_certificado.html",
        cert=cert, linha=linha, extra=extra or {},
    )


@bp.route("/")
def lista():
    situacoes_selecionadas = request.args.getlist("situacao") or SITUACOES_PADRAO
    filtrado = _filtrar(request.args)
    pagina, total, tem_mais, proxima_url = _paginar(filtrado, request.args)
    return render_template(
        "certificados.html",
        certificados=pagina.to_dict("records"),
        total=total, tem_mais=tem_mais, proxima_url=proxima_url,
        situacoes_selecionadas=situacoes_selecionadas,
        busca=request.args.get("busca", ""),
        abrir_id=request.args.get("abrir", type=int),
    )


@bp.route("/tabela")
def tabela():
    return _render_tabela(request.args)


@bp.route("/tabela/mais")
def tabela_mais():
    filtrado = _filtrar(request.args)
    offset = request.args.get("offset", default=0, type=int)
    pagina = filtrado.iloc[offset: offset + PAGE_SIZE]
    tem_mais = offset + PAGE_SIZE < len(filtrado)
    proxima_url = _url_pagina(request.args, offset + PAGE_SIZE) if tem_mais else None
    return render_template(
        "partials/_linhas_mais.html",
        certificados=pagina.to_dict("records"), tem_mais=tem_mais, proxima_url=proxima_url,
    )


@bp.route("/busca-global")
def busca_global():
    termo = (request.args.get("q") or "").strip().lower()
    if not termo:
        return jsonify([])
    df = anotar_situacao(db.listar_certificados(), _dias_aviso())
    filtrado = df[
        df["empresa"].str.lower().str.contains(termo, na=False)
        | df["nome_socio"].str.lower().str.contains(termo, na=False)
        | df["cnpj"].str.lower().str.contains(termo, na=False)
    ].head(8)
    resultados = [
        {
            "id": int(r["id"]),
            "empresa": r["empresa"],
            "nome_socio": r["nome_socio"] or "",
            "cnpj": r["cnpj"] or "",
            "situacao": r["situacao"],
            "situacao_classe": badge_class(r["situacao"]),
            "data_validade": formatar_data_br(r["data_validade"]),
        }
        for _, r in filtrado.iterrows()
    ]
    return jsonify(resultados)


@bp.route("/<int:cert_id>/painel")
def painel(cert_id):
    html = _render_painel(cert_id)
    if not html:
        abort(404)
    return html


@bp.route("/<int:cert_id>/senha", methods=["POST"])
def revelar_senha(cert_id):
    cert = db.obter_certificado(cert_id)
    if not cert:
        abort(404)
    senha = decrypt(cert.get("senha_cifrada", ""))
    return render_template("partials/_senha_revelada.html", senha=senha)


@bp.route("/<int:cert_id>/arquivo")
def baixar_arquivo(cert_id):
    cert = db.obter_certificado(cert_id)
    if not cert or not cert.get("arquivo_path"):
        abort(404)
    caminho = cert["arquivo_path"]
    if not os.path.exists(caminho):
        abort(404)
    return send_file(caminho, as_attachment=True, download_name=cert.get("arquivo_nome") or "certificado.pfx")


@bp.route("/<int:cert_id>/editar", methods=["POST"])
def editar(cert_id):
    if not db.obter_certificado(cert_id):
        abort(404)
    db.atualizar_certificado(cert_id, dict(
        empresa=request.form.get("empresa", "").strip(),
        cnpj=request.form.get("cnpj", "").strip(),
        nome_socio=request.form.get("nome_socio", "").strip(),
        telefone=request.form.get("telefone", "").strip(),
    ))
    html = _render_painel(cert_id) + _render_tabela(request.args, oob=True)
    return with_toast(html, "Dados atualizados.", "success")


@bp.route("/<int:cert_id>/renovar/validar", methods=["POST"])
def renovar_validar(cert_id):
    if not db.obter_certificado(cert_id):
        abort(404)
    arquivo = request.files.get("arquivo")
    senha = request.form.get("senha", "")
    if not arquivo or not arquivo.filename or not senha:
        return render_template("partials/_renovar_resultado.html", erro="Selecione o arquivo e informe a senha.")
    conteudo = arquivo.read()
    try:
        info = extrair_info_pfx(conteudo, senha)
    except PfxError as e:
        return render_template("partials/_renovar_resultado.html", erro=str(e))
    token = pending.guardar({
        "cert_id": cert_id, "conteudo": conteudo, "nome_original": arquivo.filename,
        "senha": senha, "info": info,
    })
    confirmar_url = url_for("certificados.renovar_confirmar", cert_id=cert_id)
    return render_template("partials/_renovar_resultado.html", info=info, token=token, confirmar_url=confirmar_url)


@bp.route("/<int:cert_id>/renovar/confirmar", methods=["POST"])
def renovar_confirmar(cert_id):
    token = request.form.get("token", "")
    dados = pending.obter(token)
    if not dados or dados.get("cert_id") != cert_id:
        return render_template("partials/_renovar_resultado.html", erro="Sessão de renovação expirada. Envie o arquivo novamente.")
    info = dados["info"]
    nome_salvo, caminho_salvo = db.salvar_arquivo_certificado(dados["conteudo"], dados["nome_original"])
    db.renovar_certificado(cert_id, dict(
        arquivo_nome=nome_salvo, arquivo_path=caminho_salvo,
        senha_cifrada=encrypt(dados["senha"]),
        data_emissao=info["data_emissao"], data_validade=info["data_validade"],
        subject_cn=info["subject_cn"], issuer_cn=info["issuer_cn"], numero_serie=info["numero_serie"],
    ))
    pending.remover(token)
    html = _render_painel(cert_id) + _render_tabela(request.args, oob=True)
    return with_toast(html, "Certificado renovado com sucesso!", "success")


@bp.route("/<int:cert_id>/status", methods=["POST"])
def status(cert_id):
    if not db.obter_certificado(cert_id):
        abort(404)
    novo_status = request.form.get("status")
    if novo_status not in ("ativo", "cancelado"):
        abort(400)
    descricao = "Certificado reativado." if novo_status == "ativo" else "Certificado marcado como cancelado."
    db.marcar_status(cert_id, novo_status, descricao)
    html = _render_painel(cert_id) + _render_tabela(request.args, oob=True)
    return with_toast(html, descricao, "success")


@bp.route("/<int:cert_id>/excluir", methods=["POST"])
def excluir(cert_id):
    if not db.obter_certificado(cert_id):
        abort(404)
    db.excluir_certificado(cert_id)
    html = _render_tabela(request.args, oob=True)
    return with_toast(html, "Certificado excluído.", "success", appFecharPainel=True)


@bp.route("/novo/validar", methods=["POST"])
def novo_validar():
    arquivo = request.files.get("arquivo")
    senha = request.form.get("senha", "")
    if not arquivo or not arquivo.filename or not senha:
        return render_template("partials/_novo_resultado.html", erro="Selecione o arquivo e informe a senha.")
    conteudo = arquivo.read()
    try:
        info = extrair_info_pfx(conteudo, senha)
    except PfxError as e:
        return render_template("partials/_novo_resultado.html", erro=str(e))
    token = pending.guardar({"conteudo": conteudo, "nome_original": arquivo.filename, "senha": senha, "info": info})
    confirmar_url = url_for("certificados.novo_confirmar")
    return render_template("partials/_novo_resultado.html", info=info, token=token, confirmar_url=confirmar_url)


@bp.route("/novo/confirmar", methods=["POST"])
def novo_confirmar():
    token = request.form.get("token", "")
    dados = pending.obter(token)
    if not dados:
        return render_template("partials/_novo_resultado.html", erro="Sessão expirada. Envie o arquivo novamente.")
    info = dados["info"]
    nome_salvo, caminho_salvo = db.salvar_arquivo_certificado(dados["conteudo"], dados["nome_original"])
    db.inserir_certificado(dict(
        empresa=request.form.get("empresa", "").strip(),
        cnpj=request.form.get("cnpj", "").strip(),
        nome_socio=request.form.get("nome_socio", "").strip(),
        telefone=request.form.get("telefone", "").strip(),
        arquivo_nome=nome_salvo, arquivo_path=caminho_salvo,
        senha_cifrada=encrypt(dados["senha"]),
        data_emissao=info["data_emissao"], data_validade=info["data_validade"],
        subject_cn=info["subject_cn"], issuer_cn=info["issuer_cn"], numero_serie=info["numero_serie"],
    ))
    pending.remover(token)
    flash(f"Certificado de {request.form.get('empresa', '')} cadastrado com sucesso!", "success")
    resp = redirect(url_for("certificados.lista"))
    resp.headers["HX-Redirect"] = url_for("certificados.lista")
    return resp
