"""Painel principal: KPIs, gráficos e avisos de vencimento."""
import json
from datetime import datetime

import pandas as pd
from flask import Blueprint, render_template

from src import db
from src.domain import CANCELADO, VALIDO, VENCE_EM_BREVE, VENCIDO, COR_STATUS, anotar_situacao

bp = Blueprint("dashboard", "dashboard", url_prefix="/")


@bp.route("/")
def index():
    config = db.get_all_config()
    dias_aviso = int(config.get("dias_aviso", 30))
    df = db.listar_certificados()

    if df.empty:
        return render_template("dashboard.html", vazio=True)

    df = anotar_situacao(df, dias_aviso)
    ativos = df[df["situacao"] != CANCELADO]

    kpis = {
        "total": int(len(ativos)),
        "validos": int((ativos["situacao"] == VALIDO).sum()),
        "vence_em_breve": int((ativos["situacao"] == VENCE_EM_BREVE).sum()),
        "vencidos": int((ativos["situacao"] == VENCIDO).sum()),
    }

    contagem = ativos["situacao"].value_counts()
    ordem = [VALIDO, VENCE_EM_BREVE, VENCIDO]
    labels = [o for o in ordem if o in contagem.index]
    situacao_json = json.dumps({
        "labels": labels,
        "valores": [int(contagem[o]) for o in labels],
        "cores": [COR_STATUS[o] for o in labels],
    })

    hoje = pd.Timestamp.today().normalize()
    meses = pd.period_range(hoje, periods=12, freq="M")
    datas_validade = pd.to_datetime(ativos["data_validade"], errors="coerce")
    contagem_mes = datas_validade.dt.to_period("M").value_counts().reindex(meses, fill_value=0)
    meses_json = json.dumps({
        "labels": [m.strftime("%b/%y") for m in contagem_mes.index],
        "valores": [int(v) for v in contagem_mes.values],
    })

    alertas = (
        ativos[ativos["situacao"].isin([VENCIDO, VENCE_EM_BREVE])]
        .sort_values("dias_restantes")
        .to_dict("records")
    )

    hist = db.listar_historico(limite=25)
    if not hist.empty:
        hist["data_hora"] = pd.to_datetime(hist["data_hora"]).dt.strftime("%d/%m/%Y %H:%M")
    historico = hist.to_dict("records")

    return render_template(
        "dashboard.html",
        vazio=False,
        kpis=kpis,
        dias_aviso=dias_aviso,
        situacao_json=situacao_json,
        meses_json=meses_json,
        alertas=alertas,
        historico=historico,
        agora=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )
