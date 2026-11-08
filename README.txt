SMARTCAMPUS V1 — RASCUNHO EXECUTÁVEL

ARRANQUE
1. Instalar Python 3.10 ou superior. Não são necessárias dependências externas.
2. Abrir um terminal nesta pasta.
3. Executar: python backend\app.py
   Alternativa: node servir.cjs (usa Python para iniciar o mesmo backend).
4. Abrir: http://127.0.0.1:8766/

O primeiro arranque cria database\smartcampus-demo.sqlite3 com o esquema e os
dados fictícios. A aplicação e a BD são apenas um rascunho local; não usar
dados escolares reais nem expor o servidor à rede.

CONTAS DE TESTE (palavra-passe: demo1234)
Professor: Antonio.correia@etpm.pt
Professor: carlos.demo@etpm.pt
Administrador: admin.demo@etpm.pt

ESTRUTURA ÚNICA
frontend\             As 15 páginas, estilos, scripts e dados de demonstração.
backend\app.py         Único servidor HTTP/API do rascunho.
backend\store.py       Acesso SQLite, inicialização e dados de demonstração.
database\schema.sql    Esquema SQLite do rascunho.
database\bd.txt        Inventário da BD e respetivos elementos usados.
database\smartcampus-demo.sqlite3
                      BD local criada automaticamente no primeiro arranque.
REGRAS_UPDATED.txt     Regras funcionais consolidadas.
testes\                Testes do frontend e da integração com o backend.

TESTES
node testes\regras.test.cjs
python -m unittest discover -s testes -p "test_backend.py"

LIMITES E PRÓXIMOS PASSOS
O backend e o esquema foram criados para a equipa poder experimentar o
frontend com autenticação, sessões, operações e persistência. Não são uma
solução pronta para produção. Rever as decisões marcadas para validação em
REGRAS_UPDATED.txt e as notas de passagem em backend\README.txt e
database\README.txt antes de continuar o desenvolvimento.

Os registos da BD são dados fictícios. A palavra-passe comum é exclusiva da
demonstração; o backend usa hash com salt e nunca regista passwords nos logs.
As contas novas criadas no protótipo também recebem a palavra-passe comum de
demonstração. Substituir esse fluxo antes de qualquer uso real.
