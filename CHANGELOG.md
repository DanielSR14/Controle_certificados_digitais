# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto segue, de forma aproximada, [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Adicionado
- Publicação inicial do projeto como código aberto.
- Suporte a arquivo `.env` (opcional) via `python-dotenv` para a variável
  `APP_SECRET_KEY`.
- `README`, `CONTRIBUTING`, `SECURITY`, `LICENSE` (MIT) e modelos de issue/PR.

### Alterado
- Configurações padrão (nome do escritório, assinatura) passaram a ser
  genéricas; ajustáveis pela tela de Configurações.

## [1.0.0]

### Adicionado
- Dashboard com KPIs, gráfico de status, distribuição de vencimentos em 12
  meses, fila de alertas e histórico de ações.
- Cadastro de certificados por leitura do `.pfx/.p12` (emissão, validade,
  número de série, emissor, sugestão de empresa/CNPJ).
- Importação em lote a partir de uma pasta, com validação de senha.
- Renovação de certificado mantendo histórico.
- Geração de mensagens de aviso com placeholders e link do WhatsApp.
- Exportação CSV/XLSX e backup do banco SQLite.
- Cifragem das senhas dos certificados em repouso (Fernet).
- Interface htmx com tema claro/escuro e busca global (`Ctrl/Cmd + K`),
  funcionando offline.
