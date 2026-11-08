BASE DE DADOS — RASCUNHO SQLITE

schema.sql é o esquema inicial. No primeiro arranque do backend, store.py cria
smartcampus-demo.sqlite3 nesta pasta e carrega os dados fictícios de
frontend\static\js\dados-demo.js. Não é preciso instalar SQLite à parte.

O esquema é deliberadamente simples para desbloquear a execução do frontend:
- records guarda as coleções JSON de domínio e valida IDs e JSON.
- Índices únicos protegem emails, códigos e séries.
- Um índice parcial impede duas atribuições abertas ao mesmo equipamento.
- credentials guarda hash PBKDF2-SHA256 com salt, nunca passwords em texto.
- sessions guarda sessões expiradas e tokens CSRF.

Este modelo é um protótipo; ainda não tem tabelas normalizadas nem chaves
estrangeiras entre todas as entidades. Antes de continuar, a equipa de BD
deve decidir o modelo relacional final com a equipa de backend, criar
migrações e acrescentar testes de integridade. Preservar sempre o histórico
e gravar auditoria e alteração de negócio na mesma transação.

smartcampus-demo.sqlite3 contém apenas dados inventados para testes locais.
Não adicionar dados reais, não publicar esta BD e não a tratar como cópia de
segurança ou base de produção.

O ficheiro bd.txt contém o inventário dos componentes SQLite utilizados e as
tarefas recomendadas para a equipa de base de dados.
