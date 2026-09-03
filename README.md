# Controle de Certificados Digitais

Aplicação web local, em **Flask + htmx**, para escritórios de contabilidade
gerenciarem os certificados digitais `.pfx/.p12` dos clientes: cadastro por
leitura do arquivo, acompanhamento de vencimento, renovação e geração de
mensagens de aviso prontas para copiar/colar ou enviar pelo WhatsApp.

[![CI](https://github.com/DanielSR14/Controle_certificados_digitais/actions/workflows/ci.yml/badge.svg)](https://github.com/DanielSR14/Controle_certificados_digitais/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)
![htmx](https://img.shields.io/badge/htmx-2.x-3366CC)
![SQLite](https://img.shields.io/badge/SQLite-local-003B57?logo=sqlite&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

> Ferramenta de uso **interno**, pensada para rodar em um PC da rede do
> escritório e servir os demais computadores. Não foi projetada para exposição
> na internet pública. Veja [SECURITY.md](SECURITY.md).

---

## Funcionalidades

| Área | O que faz |
|------|-----------|
| **Cadastro por leitura do `.pfx`** | Ao subir o arquivo e informar a senha, a aplicação abre o certificado (via `cryptography`) e preenche emissão, validade, número de série, emissor e uma sugestão de empresa/CNPJ a partir do *subject*. |
| **Importação em lote** | Aponta para uma pasta, escaneia todos os `.pfx/.p12`, valida as senhas (com sugestão a partir do nome do arquivo no padrão `... Validade dd mm aaaa - Senha 123456.pfx`) e importa tudo de uma vez. |
| **Dashboard** | KPIs de válidos / vence em breve / vencidos, gráfico de status (Chart.js), distribuição de vencimentos nos próximos 12 meses, fila de alertas por urgência e histórico de ações. |
| **Situação automática** | Cada certificado é classificado como *Válido*, *Vence em breve*, *Vencido* ou *Cancelado*, conforme o prazo de aviso configurável (padrão: 30 dias). |
| **Mensagens de aviso** | Modelo com placeholders (`{SAUDACAO}`, `{EMPRESA}`, `{DATA_VENCIMENTO}`, `{SITUACAO_VENCIMENTO}`, …), geração individual ou em lote e link direto do WhatsApp (`wa.me`) com o telefone já normalizado. |
| **Renovação** | Substitui arquivo, senha e validade de um certificado existente, mantendo o histórico. |
| **Exportação e backup** | CSV, XLSX e cópia do banco SQLite em um clique. |
| **Extras de interface** | Tema claro/escuro, busca global (`Ctrl/Cmd + K`), navegação parcial com htmx (sem recarregar a página). Funciona **100% offline** — htmx e Chart.js são vendorizados. |

## Stack

- **Backend:** Python 3.11+ e [Flask](https://flask.palletsprojects.com/),
  organizado em blueprints (dashboard, certificados, mensagens, configurações).
- **Leitura de certificados:** [`cryptography`](https://cryptography.io/) (PKCS#12 / X.509).
- **Persistência:** SQLite local, criado automaticamente em `data/certificados.db`.
- **Frontend:** templates Jinja2 + [htmx](https://htmx.org) + [Chart.js](https://www.chartjs.org/),
  CSS próprio, ícones SVG inline (estilo Feather, MIT).
- **Planilhas:** `pandas` + `openpyxl` para importação/exportação.

## Requisitos

- Python **3.11 ou superior**
- Windows, Linux ou macOS (o script `iniciar.bat` é específico do Windows)

## Instalação

```bash
git clone https://github.com/DanielSR14/Controle_certificados_digitais.git
cd Controle_certificados_digitais

python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

## Como rodar

```bash
python run.py
```

Acesse **http://localhost:8501**.

A aplicação sobe em `0.0.0.0:8501`, ficando acessível para outros computadores
da rede interna em `http://<ip-deste-pc>:8501`. No Windows, o atalho
`iniciar.bat` faz isso e mostra o IP a usar (libere a porta `8501` no Firewall
se os outros PCs não conseguirem acessar).

## Configuração

Copie `.env.example` para `.env` se quiser fixar a chave de sessão do Flask:

```bash
cp .env.example .env
```

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `APP_SECRET_KEY` | Chave de sessão do Flask. Se ausente, é gerada aleatoriamente a cada início. | *(aleatória)* |

As demais opções — **nome do escritório**, **assinatura**, **prazo de aviso** e
**modelo de mensagem** — são ajustadas pela própria interface, em
**Configurações**, e ficam salvas no banco.

## Estrutura do projeto

```
run.py                    Ponto de entrada (python run.py)
iniciar.bat               Atalho Windows: sobe na rede interna e mostra o IP
requirements.txt
src/
  db.py                   Acesso ao SQLite, migrações e configurações
  domain.py               Regras de negócio: situação, saudação, montagem de mensagem
  pfx_utils.py            Leitura de .pfx/.p12 (cryptography) e parsing de nome de arquivo
  crypto_utils.py         Cifra/decifra as senhas dos certificados (Fernet)
webapp/
  __init__.py             Fábrica da aplicação Flask (create_app)
  routes_dashboard.py     KPIs, gráficos, avisos, histórico
  routes_certificados.py  Cadastro, edição, renovação, exclusão, busca global
  routes_mensagens.py     Mensagem individual e link do WhatsApp
  routes_config.py        Modelo de mensagem, importação em lote, exportar/backup
  htmx_utils.py           Helpers de resposta htmx (toasts via HX-Trigger)
  icons.py                Ícones SVG inline
  pending.py              Área de estágio em memória para fluxos validar → confirmar
  templates/              Páginas Jinja2 + partials/ (fragmentos htmx)
  static/                 CSS próprio + htmx e Chart.js vendorizados
data/                     Criado em runtime — NÃO versionado
  certificados.db         Banco local
  arquivos/               Cópia dos .pfx cadastrados
  .secret.key             Chave local de criptografia das senhas
```

## Backup

- **Configurações → Exportar e backup → Baixar backup (.db)** gera uma cópia do
  banco (inclui senhas cifradas e histórico).
- Para backup manual, copie a pasta `data/` inteira para um local seguro.
- Trate `data/` como **sensível**: contém os certificados dos clientes e a
  chave de criptografia.

## Segurança

As senhas dos certificados são gravadas **cifradas** (Fernet), com uma chave
gerada localmente em `data/.secret.key`. Isso evita texto puro no banco, mas
**não** substitui o controle de acesso ao computador e ao backup. O
`iniciar.bat` publica a aplicação na rede interna **sem autenticação** — use
apenas em rede confiável. Detalhes e reporte de vulnerabilidades em
[SECURITY.md](SECURITY.md).

## Testes

```bash
pip install -r requirements-dev.txt
pytest -q
```

Os testes de fumaça sobem a aplicação com um banco temporário — não tocam em `data/`.

## Contribuindo

Contribuições são bem-vindas — veja [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

[MIT](LICENSE).
