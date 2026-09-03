"""Camada de acesso ao banco SQLite do Controle de Certificados Digitais."""
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ARQUIVOS_DIR = DATA_DIR / "arquivos"
DB_PATH = DATA_DIR / "certificados.db"

DEFAULT_TEMPLATE = (
    "{SAUDACAO} {NOME_SOCIO}, tudo bem?\n\n"
    "Estamos entrando em contato para avisar que o certificado digital da "
    "empresa {EMPRESA} {SITUACAO_VENCIMENTO}, no dia {DATA_VENCIMENTO}.\n\n"
    "Para evitar interrupções nos processos fiscais e contábeis, pedimos que "
    "entre em contato conosco o quanto antes para providenciarmos a renovação.\n\n"
    "Qualquer dúvida, estamos à disposição.\n\n"
    "Atenciosamente,\n{ASSINATURA}"
)

DEFAULT_CONFIG = {
    "dias_aviso": "30",
    "nome_escritorio": "Meu Escritório Contábil",
    "assinatura": "Equipe do Escritório",
    "template_mensagem": DEFAULT_TEMPLATE,
}

# Texto padrão anterior (com o trecho "vence em {DIAS} dia(s)"), mantido aqui
# só para a migração em init_db() reconhecer e atualizar instalações antigas
# que nunca customizaram o template.
_TEMPLATE_ANTIGO = (
    "{SAUDACAO} {NOME_SOCIO}, tudo bem?\n\n"
    "Estamos entrando em contato para avisar que o certificado digital da "
    "empresa {EMPRESA} vence em {DIAS} dia(s), no dia {DATA_VENCIMENTO}.\n\n"
    "Para evitar interrupções nos processos fiscais e contábeis, pedimos que "
    "entre em contato conosco o quanto antes para providenciarmos a renovação.\n\n"
    "Qualquer dúvida, estamos à disposição.\n\n"
    "Atenciosamente,\n{ASSINATURA}"
)


@contextmanager
def get_conn():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARQUIVOS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS certificados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa TEXT NOT NULL,
                cnpj TEXT,
                nome_socio TEXT,
                telefone TEXT,
                email TEXT,
                arquivo_nome TEXT,
                arquivo_path TEXT,
                senha_cifrada TEXT,
                data_emissao TEXT,
                data_validade TEXT NOT NULL,
                subject_cn TEXT,
                issuer_cn TEXT,
                numero_serie TEXT,
                status TEXT NOT NULL DEFAULT 'ativo',
                observacoes TEXT,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                certificado_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                descricao TEXT,
                data_hora TEXT NOT NULL,
                FOREIGN KEY (certificado_id) REFERENCES certificados(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT
            )
            """
        )
        for chave, valor in DEFAULT_CONFIG.items():
            conn.execute(
                "INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES (?, ?)",
                (chave, valor),
            )
        conn.execute(
            "UPDATE configuracoes SET valor = ? WHERE chave = 'template_mensagem' AND valor = ?",
            (DEFAULT_TEMPLATE, _TEMPLATE_ANTIGO),
        )
        # Padroniza cadastros antigos para caixa alta (feito em Python, não com o
        # UPPER() do SQLite, que não maiúsculiza acentos corretamente).
        for row in conn.execute("SELECT id, empresa, nome_socio FROM certificados").fetchall():
            empresa_maiuscula = (row["empresa"] or "").upper()
            socio_maiusculo = (row["nome_socio"] or "").upper()
            if empresa_maiuscula != row["empresa"] or socio_maiusculo != row["nome_socio"]:
                conn.execute(
                    "UPDATE certificados SET empresa = ?, nome_socio = ? WHERE id = ?",
                    (empresa_maiuscula, socio_maiusculo, row["id"]),
                )


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def salvar_arquivo_certificado(conteudo: bytes, nome_original: str) -> tuple[str, str]:
    """Grava o .pfx enviado em data/arquivos com um nome único e devolve
    (nome_exibido, caminho_absoluto)."""
    ARQUIVOS_DIR.mkdir(parents=True, exist_ok=True)
    nome_seguro = re.sub(r"[^A-Za-z0-9 ._&-]", "_", nome_original.strip()) or "certificado.pfx"
    caminho = ARQUIVOS_DIR / f"{uuid.uuid4().hex[:10]}_{nome_seguro}"
    caminho.write_bytes(conteudo)
    return nome_seguro, str(caminho)


def inserir_certificado(dados: dict) -> int:
    campos = [
        "empresa", "cnpj", "nome_socio", "telefone", "email", "arquivo_nome",
        "arquivo_path", "senha_cifrada", "data_emissao", "data_validade",
        "subject_cn", "issuer_cn", "numero_serie", "observacoes",
    ]
    valores = {c: dados.get(c, "") for c in campos}
    valores["empresa"] = valores["empresa"].upper()
    valores["nome_socio"] = valores["nome_socio"].upper()
    agora = _now()
    with get_conn() as conn:
        cur = conn.execute(
            f"""INSERT INTO certificados
                ({', '.join(campos)}, status, criado_em, atualizado_em)
                VALUES ({', '.join('?' for _ in campos)}, 'ativo', ?, ?)""",
            [*valores.values(), agora, agora],
        )
        cert_id = cur.lastrowid
        conn.execute(
            "INSERT INTO historico (certificado_id, tipo, descricao, data_hora) VALUES (?, ?, ?, ?)",
            (cert_id, "cadastro", f"Certificado cadastrado para {valores['empresa']}.", agora),
        )
    return cert_id


def atualizar_certificado(cert_id: int, dados: dict):
    campos = [
        "empresa", "cnpj", "nome_socio", "telefone", "email", "observacoes",
    ]
    presentes = {c: dados[c] for c in campos if c in dados}
    if not presentes:
        return
    if "empresa" in presentes:
        presentes["empresa"] = presentes["empresa"].upper()
    if "nome_socio" in presentes:
        presentes["nome_socio"] = presentes["nome_socio"].upper()
    set_clause = ", ".join(f"{c} = ?" for c in presentes)
    with get_conn() as conn:
        conn.execute(
            f"UPDATE certificados SET {set_clause}, atualizado_em = ? WHERE id = ?",
            [*presentes.values(), _now(), cert_id],
        )
        conn.execute(
            "INSERT INTO historico (certificado_id, tipo, descricao, data_hora) VALUES (?, ?, ?, ?)",
            (cert_id, "edicao", "Dados cadastrais atualizados.", _now()),
        )


def renovar_certificado(cert_id: int, dados: dict):
    """Substitui o arquivo/senha/validade de um certificado já existente."""
    campos = [
        "arquivo_nome", "arquivo_path", "senha_cifrada", "data_emissao",
        "data_validade", "subject_cn", "issuer_cn", "numero_serie",
    ]
    presentes = {c: dados[c] for c in campos if c in dados}
    set_clause = ", ".join(f"{c} = ?" for c in presentes)
    agora = _now()
    with get_conn() as conn:
        conn.execute(
            f"UPDATE certificados SET {set_clause}, status = 'ativo', atualizado_em = ? WHERE id = ?",
            [*presentes.values(), agora, cert_id],
        )
        nova_validade = dados.get("data_validade", "")
        conn.execute(
            "INSERT INTO historico (certificado_id, tipo, descricao, data_hora) VALUES (?, ?, ?, ?)",
            (cert_id, "renovacao", f"Certificado renovado. Nova validade: {nova_validade}.", agora),
        )


def excluir_certificado(cert_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM certificados WHERE id = ?", (cert_id,))


def marcar_status(cert_id: int, status: str, descricao: str = ""):
    with get_conn() as conn:
        conn.execute(
            "UPDATE certificados SET status = ?, atualizado_em = ? WHERE id = ?",
            (status, _now(), cert_id),
        )
        conn.execute(
            "INSERT INTO historico (certificado_id, tipo, descricao, data_hora) VALUES (?, ?, ?, ?)",
            (cert_id, "status", descricao or f"Status alterado para {status}.", _now()),
        )


def obter_certificado(cert_id: int) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM certificados WHERE id = ?", (cert_id,)).fetchone()
        return dict(row) if row else None


def listar_certificados() -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql_query("SELECT * FROM certificados ORDER BY data_validade ASC", conn)
    return df


def listar_historico(cert_id: Optional[int] = None, limite: int = 100) -> pd.DataFrame:
    with get_conn() as conn:
        if cert_id is not None:
            df = pd.read_sql_query(
                "SELECT h.*, c.empresa FROM historico h JOIN certificados c ON c.id = h.certificado_id "
                "WHERE h.certificado_id = ? ORDER BY h.data_hora DESC LIMIT ?",
                conn, params=(cert_id, limite),
            )
        else:
            df = pd.read_sql_query(
                "SELECT h.*, c.empresa FROM historico h JOIN certificados c ON c.id = h.certificado_id "
                "ORDER BY h.data_hora DESC LIMIT ?",
                conn, params=(limite,),
            )
    return df


def get_config(chave: str, default: str = "") -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT valor FROM configuracoes WHERE chave = ?", (chave,)).fetchone()
        return row["valor"] if row else default


def get_all_config() -> dict:
    with get_conn() as conn:
        rows = conn.execute("SELECT chave, valor FROM configuracoes").fetchall()
        return {r["chave"]: r["valor"] for r in rows}


def set_config(chave: str, valor: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO configuracoes (chave, valor) VALUES (?, ?) "
            "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
            (chave, valor),
        )
