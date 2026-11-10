# Integração com backend e base de dados

Esta entrega implementa apenas o frontend e um modelo de demonstração. `model.js` é testável sem navegador, mas não é uma barreira de segurança. A API real deve validar novamente todas as operações, estados, destinos e permissões.

O HTML pode ser servido por Flask/Jinja. Antes de app.js, fornecer `window.SMARTCAMPUS_CONFIG` com `mode: "integrado"`, `currentUserId`, `currentUser` (id, nome, email, perfil e estado da conta autenticada), `routes`, `operations` e `csrfToken`, e um elemento `<script type="application/json" id="server-data">` contendo os dados serializados com o filtro `tojson` de Jinja. Carregar model.js antes de app.js. Não carregar dados-demo.js em produção.

O servidor fornece os arrays `salas`, `armarios`, `equipamentos`, `utilizadores`, `destinatarios`, `atribuicoes`, `avarias`, `transferencias`, `eventos`, `logs` no formato documentado pelo exemplo. Filtrar os dados conforme o perfil antes de os enviar; arrays sem autorização podem ser vazios. Fornecer apenas intervenientes necessários aos formulários autorizados. A sessão autenticada determina currentUserId. Usar a página de login real do backend.

## Operações POST

Mapa `operations`: equipamento, sala, armario, conta, estadoConta, atribuicao, devolucao, avaria, transferencia, ocultarLog, logout. Os nomes dos campos são os dos formulários e as regras de model.js. Enviar JSON, cookie da mesma origem e cabeçalho X-CSRFToken. O backend ignora qualquer autor/perfil fornecido pelo cliente e obtém a identidade da sessão.

Responder com JSON `{ "message": "Descrição" }`, HTTP 2xx no sucesso e 4xx/5xx em erro. Não redirecionar operações para HTML. A rota logout invalida a sessão e responde JSON; `routes.login` aponta para o login real. Após guardar, as páginas GET devem fornecer dados atualizados. O frontend de demonstração não calcula a auditoria real em modo integrado: esse trabalho é do servidor.

Datas dos formulários são hora local sem offset. Acordar Europe/Lisbon e normalizar para UTC no backend, considerando horas ambíguas na mudança de hora. Os logs usam a hora oficial do servidor, independente da data declarada da operação. Os filtros devem usar limites coerentes com o fuso exibido.

## Auditoria

Guardar evento e alteração de dados na mesma transação. Logs são acrescentados, não editados. Remoção lógica acrescenta uma entrada protegida com acao `Remoção lógica de log`, objeto igual ao ID do original, autor, timestamp, motivo e referência/conteúdo do original. O original continua intacto. A lista normal omite IDs visados por essas entradas; a vista completa mantém tudo. Proibir remoção das entradas protegidas e de contas de utilizador.

Registar login/logout, acessos recusados, consultas, validações e alterações no servidor. Não guardar passwords nem tokens. A API deve gerar logs de falhas mesmo que a interface seja contornada. Falhas técnicas de escrita devem ser monitorizadas fora da transação falhada, sem revelar segredos. Configurar retenção, arquivo, backups e privilégios mínimos de escrita.

Em produção, usar transações e controlo de concorrência para evitar dupla atribuição ou atualização perdida. Implementar idempotência dos POST, invalidar sessões quando uma conta é desativada e proteger o último Administrador. O armazenamento local da demonstração não garante integridade perante modificações deliberadas, acessos concorrentes de múltiplos computadores ou limpeza do navegador.

Fornecer sempre currentUser mesmo que a lista utilizadores esteja filtrada. Arrays ausentes são normalizados para listas vazias. A escolha ?page= só é suportada na demonstração aberta como ficheiro. Após remoção de log e alteração de estado de conta, o frontend recarrega a página GET para obter dados atualizados.

Decisão de minimização: tentativas falhadas não guardam o email introduzido (pode conter dados ou uma palavra-passe colocada no campo errado). O ator mantém-se não autenticado. A equipa de backend deve definir com o docente como correlacionar tentativas abusivas sem guardar segredos.
