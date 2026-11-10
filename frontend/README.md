# SmartCampus atualizado

## Abrir

1. Extrair o ZIP completo para uma pasta nova.
2. Abrir `index.html` no Chrome, Edge ou Brave. Manter todas as pastas juntas.
3. Introduzir uma conta de teste e a palavra-passe **demo1234**.

| Perfil | Email |
|---|---|
| Professor | Antonio.correia@etpm.pt |
| Outro professor | carlos.demo@etpm.pt |
| Administrador | admin.demo@etpm.pt |

Os endereços de demonstração não implicam contas reais da escola. Nunca introduzir uma palavra-passe escolar. O perfil vem de uma conta previamente registada, não do texto do email. Os alunos só figuram como destinatários de equipamentos e não entram.

Se o navegador impedir armazenamento em ficheiros locais, executar `node servir.cjs` nesta pasta e abrir http://127.0.0.1:8766 . Também pode usar `python -m http.server 8000`, se Python estiver instalado, e abrir http://127.0.0.1:8000 . Não é preciso instalar bibliotecas para a interface.

## Experimentar os logs

Entrar como Professor, marcar um equipamento disponível como avariado e transferi-lo de volta para uma sala depois de confirmar que está operacional. Sair e entrar como Administrador. Abrir Logs de auditoria, procurar o equipamento e consultar os valores Antes e Depois.

Usar **Remover da lista** num log normal, indicar um motivo e confirmar. Aparece um novo registo **Remoção lógica de log**, protegido contra remoção. Escolher **Todos, incluindo removidos** ou **Apenas removidos** para consultar o original. Não existe eliminação física de logs na aplicação.

## Funcionalidades

15 ecrãs: login, dashboard, equipamentos, ficha de equipamento, salas, armários, atribuição, devolução, avaria, transferência, histórico, eventos, logs, utilizadores e ficha de utilizador. Edição de nomes/fichas, contas ETPM únicas, email imutável, desativação/reativação com motivo, permissões, formulários e mensagens. Sem área de Aluno e sem módulo de reparações.

Os logs e as operações persistem no armazenamento local do navegador; a sessão está associada ao separador. Não usar dados reais. Não há backend de produção, autenticação real ou SQLite. O ficheiro `documentos/INTEGRACAO.md` explica como ligar às outras equipas. `documentos/REGRAS.md` contém a especificação atual e as propostas adotadas para validação do docente.

Não existe botão de reposição que elimine silenciosamente a auditoria. Limpar dados do navegador elimina a demonstração e os seus logs; isto não é um mecanismo seguro de auditoria. Para apresentar sem os seus testes, use outro perfil de navegador ou uma nova pasta de demonstração em modo ficheiro.

## Testes

Com Node instalado: `node testes/regras.test.cjs`. O relatório de testes e a revisão com Claude estão em `testes/`. Capturas são evidência de teste, não registos de produção.

Código preparado com assistência de IA a partir das referências do docente e das regras fornecidas pelo grupo. As equipas devem compreender e validar o trabalho antes da apresentação.
