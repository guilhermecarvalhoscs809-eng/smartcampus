# SmartCampus

Este projeto inclui agora o frontend e as regras da entrega `SmartCampus_Atualizado`.

## Executar a demonstração

É necessário ter o Node.js instalado. A partir desta pasta:

```powershell
node servir.cjs
```

Abrir <http://127.0.0.1:8766/>. O servidor só aceita ligações locais.

Contas fictícias da demonstração (palavra-passe: `demo1234`):

| Perfil | Email |
|---|---|
| Professor | Antonio.correia@etpm.pt |
| Professor | carlos.demo@etpm.pt |
| Administrador | admin.demo@etpm.pt |

Usar apenas dados de demonstração. Não introduzir palavras-passe nem dados reais da escola.

## Conteúdo integrado

- `demo/` e `frontend/static/`: os 15 ecrãs, estilos, modelo e dados de demonstração atualizados.
- `documentos/REGRAS.md`: regras funcionais e permissões adotadas.
- `documentos/INTEGRACAO.md`: contrato previsto para integração futura com a API.
- `testes/regras.test.cjs`: testes das regras do modelo frontend.

O servidor Node resolve os URLs de ecrã para os ficheiros em `demo/`, permitindo que a navegação do frontend funcione sem alterar os ecrãs.

## Limites atuais

A aplicação integrada continua a ser uma demonstração: a autenticação, os dados e os logs ficam no armazenamento local do navegador. Não está ligada à base de dados SQLite nem ao backend Flask; os ficheiros backend existentes continuam por implementar. O modelo JavaScript não substitui validações, autorização e auditoria no servidor.

Para ligar o frontend ao backend, seguir `documentos/INTEGRACAO.md` e repetir as regras no servidor. Não tratar os logs locais como auditoria de produção.

## Testes

Com Node.js instalado:

```powershell
node testes/regras.test.cjs
```
