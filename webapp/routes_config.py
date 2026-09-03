"""Configurações gerais, importação em lote, exportação e backup."""
import io
from datetime import datetime
from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for

from src import db
from src.crypto_utils import encrypt
from src.domain import PLACEHOLDERS, montar_contexto_mensagem, montar_mensagem
from src.pfx_utils import PfxError, extrair_info_pfx, parse_nome_arquivo
from webapp import pending

bp = Blueprint("config", "config", url_prefix="/configuracoes")

SENHA_PADRAO = "123456"


@bp.route("/")
def geral():
    config = db.get_all_config()
    exemplo_cert = {
        "nome_socio": "João da Silva", "empresa": "Empresa Exemplo LTDA",
        "cnpj": "12345678000199", "data_validade": datetime.now().date().isoformat(),
    }
    contexto_exemplo = montar_contexto_mensagem(exemplo_cert, config)
    preview = montar_mensagem(config.get("template_mensagem", ""), contexto_exemplo)
    tem_dados = not db.listar_certificados().empty
    return render_template(
        "configuracoes.html", config=config, placeholders=PLACEHOLDERS,
        preview=preview, tem_dados=tem_dados, pasta_padrao=str(Path.cwd()),
    )


@bp.route("/salvar", methods=["POST"])
def salvar():
    db.set_config("nome_escritorio", request.form.get("nome_escritorio", "").strip())
    db.set_config("assinatura", request.form.get("assinatura", "").strip())
    db.set_config("dias_aviso", str(request.form.get("dias_aviso", 30)))
    db.set_config("template_mensagem", request.form.get("template_mensagem", ""))
    flash("Configurações salvas.", "success")
    return redirect(url_for("config.geral"))


@bp.route("/importar/escanear", methods=["POST"])
def importar_escanear():
    pasta = request.form.get("pasta", "").strip()
    caminho_pasta = Path(pasta)
    if not caminho_pasta.is_dir():
        return render_template("partials/_import_lista.html", erro="Pasta não encontrada.")

    arquivos = sorted({p for p in caminho_pasta.glob("*") if p.suffix.lower() in (".pfx", ".p12")})
    existentes = set(db.listar_certificados()["arquivo_nome"]) if not db.listar_certificados().empty else set()

    itens = []
    for p in arquivos:
        sugestao = parse_nome_arquivo(p.name) or {}
        itens.append({
            "path": str(p), "nome": p.name,
            "senha": sugestao.get("senha") or SENHA_PADRAO,
            "empresa_sugerida": sugestao.get("empresa", ""),
            "status": "pendente", "info": None, "erro": "",
            "duplicata": p.name in existentes,
        })

    if not itens:
        return render_template("partials/_import_lista.html", erro="Nenhum arquivo .pfx/.p12 encontrado nessa pasta.")

    token = pending.guardar({"itens": itens})
    return render_template("partials/_import_lista.html", itens=itens, token=token)


@bp.route("/importar/validar", methods=["POST"])
def importar_validar():
    token = request.form.get("token", "")
    dados = pending.obter(token)
    if not dados:
        return render_template("partials/_import_lista.html", erro="Sessão de importação expirada. Escaneie a pasta novamente.")

    for i, item in enumerate(dados["itens"]):
        senha = request.form.get(f"senha_{i}", item["senha"])
        item["senha"] = senha
        try:
            conteudo = Path(item["path"]).read_bytes()
            item["info"] = extrair_info_pfx(conteudo, senha)
            item["status"] = "ok"
            item["erro"] = ""
        except PfxError as e:
            item["status"] = "erro"
            item["erro"] = str(e)

    return render_template("partials/_import_lista.html", itens=dados["itens"], token=token)


@bp.route("/importar/confirmar", methods=["POST"])
def importar_confirmar():
    token = request.form.get("token", "")
    dados = pending.obter(token)
    if not dados:
        flash("Sessão de importação expirada.", "error")
        return redirect(url_for("config.geral"))

    importados = 0
    for item in dados["itens"]:
        if item["status"] != "ok":
            continue
        info = item["info"]
        conteudo = Path(item["path"]).read_bytes()
        nome_salvo, caminho_salvo = db.salvar_arquivo_certificado(conteudo, item["nome"])
        db.inserir_certificado(dict(
            empresa=info.get("empresa_sugerida") or item["empresa_sugerida"] or item["nome"],
            cnpj=info.get("cnpj_sugerido", ""),
            nome_socio="", telefone="",
            arquivo_nome=nome_salvo, arquivo_path=caminho_salvo,
            senha_cifrada=encrypt(item["senha"]),
            data_emissao=info["data_emissao"], data_validade=info["data_validade"],
            subject_cn=info["subject_cn"], issuer_cn=info["issuer_cn"], numero_serie=info["numero_serie"],
        ))
        importados += 1

    pending.remover(token)
    flash(f"{importados} certificado(s) importado(s). Complete sócio/telefone em Certificados.", "success")
    resp = redirect(url_for("certificados.lista"))
    resp.headers["HX-Redirect"] = url_for("certificados.lista")
    return resp


@bp.route("/exportar.csv")
def exportar_csv():
    df = db.listar_certificados().drop(columns=["senha_cifrada"], errors="ignore")
    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    return send_file(
        io.BytesIO(csv_bytes), mimetype="text/csv", as_attachment=True,
        download_name=f"certificados_{datetime.now():%Y%m%d}.csv",
    )


@bp.route("/exportar.xlsx")
def exportar_xlsx():
    df = db.listar_certificados().drop(columns=["senha_cifrada"], errors="ignore")
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    return send_file(
        buffer, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True, download_name=f"certificados_{datetime.now():%Y%m%d}.xlsx",
    )


@bp.route("/backup.db")
def backup_db():
    if not db.DB_PATH.exists():
        flash("Banco de dados ainda não foi criado.", "error")
        return redirect(url_for("config.geral"))
    return send_file(
        db.DB_PATH, mimetype="application/octet-stream", as_attachment=True,
        download_name=f"certificados_backup_{datetime.now():%Y%m%d_%H%M}.db",
    )
