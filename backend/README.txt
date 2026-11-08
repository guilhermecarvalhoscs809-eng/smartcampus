BACKEND — RASCUNHO PARA DESENVOLVIMENTO

O servidor único está em app.py e usa apenas a biblioteca padrão do Python.
Executar desde a raiz smartcampusv1:

    python backend\app.py

O servidor só escuta em 127.0.0.1. Serve o frontend existente, injeta a
configuração e os dados da sessão e fornece uma API JSON. store.py é apenas o
módulo auxiliar de acesso à BD, não um segundo servidor.

ROTAS DISPONÍVEIS NO RASCUNHO
- POST /api/login: valida a conta demo e abre sessão com cookie HttpOnly.
- POST /api/logout: exige sessão e token CSRF, regista saída e invalida sessão.
- GET /api/session: consulta a sessão atual.
- GET /equipamentos.html?secao=equipamentos|salas|armarios: separadores
  unificados de inventário e localizações.
- GET /assignacao.html?vista=ativas: consulta de atribuições abertas.
- GET /devolucao.html?vista=historico: histórico de devoluções do Administrador.
- POST /api/operations/{equipamento,sala,armario,conta,estadoConta,
  atribuicao,devolucao,avaria,transferencia,ocultarLog}: exige sessão e CSRF.
- GET /{pagina}.html: serve páginas e exige autenticação, exceto login.

As operações usam as regras de REGRAS_UPDATED.txt e o contrato presente no
frontend. Erros de validação respondem com HTTP 4xx e JSON { "message": "..." }.
Os dados e logs da operação são guardados na mesma transação SQLite.
Professor e Administrador podem consultar as pessoas associadas a atribuições
ativas. Mais de duas atribuições ativas gera alerta no frontend, sem bloqueio
no backend.

PARA A EQUIPA QUE VAI CONTINUAR
1. Validar todas as decisões do protótipo com o docente.
2. Rever autorização por rota e dados mínimos visíveis para cada perfil.
3. Adicionar migrações/versionamento de esquema e testes das regras.
4. Substituir a password partilhada e o fluxo de criação de contas demo.
5. Rever CSRF, sessões, rate limiting, backups, concorrência e política de
   auditoria antes de qualquer utilização real.

Este servidor é intencionalmente local e demonstrativo, não é uma API de
produção. Não o expor à rede e não reutilizar as credenciais de teste.
