# SmartCampus regras e responsabilidades

Especificação funcional para as equipas de frontend, backend e base de dados
Versão 2 • 5 de novembro de 2026

O SmartCampus permite aos Professores e Administradores gerir equipamentos, localizações, atribuições e devoluções. Este documento define o comportamento esperado de cada função e as permissões que as equipas devem implementar em conjunto.


## 1 Regras principais confirmadas

Existem dois perfis de acesso: Professor e Administrador. Os alunos não utilizam o sistema nem têm credenciais de acesso. Podem continuar a constar como destinatários de equipamentos, se essa parte do projeto for mantida.

As contas de acesso têm de usar um endereço do domínio etpm.pt. O email identifica uma conta previamente criada; ter um email desse domínio não concede acesso nem privilégios automaticamente.

As contas não podem ser apagadas. O Administrador pode desativá-las, mantendo a identificação e os registos históricos. O Professor não pode desativar contas.

O Professor não pode apagar registos. Pode marcar equipamentos como avariados e registar transferências, além das atribuições e devoluções previstas no projeto.

Não existe um módulo de reparações nem registo de trabalhos de reparação. Ao marcar um equipamento como Avariado, o sistema encaminha-o para a Sala de Reparação e regista a movimentação.

Sempre que um equipamento sai da Sala de Reparação, é obrigatório escolher a sala de destino. Não existe regresso automático à sala anterior.

As permissões têm de ser verificadas pelo backend em cada pedido. Esconder botões no frontend não substitui essa verificação.


## 2 Aplicação destas regras

Estas regras substituem as anteriores propostas de acesso para Alunos e de registo de resolução de reparações. A entrega SmartCampus_Atualizado demonstra estes fluxos no frontend. A autenticação, autorização e auditoria reais ainda dependem do backend e da base de dados das outras equipas.

Nas páginas seguintes, “Proposta” identifica decisões adicionais que ainda devem ser aprovadas pelo docente. Uma permissão não confirmada não deve ser concedida automaticamente.


## 3 Perfis e permissões

Sim indica uma operação permitida pelas regras confirmadas ou pelo âmbito já previsto no projeto. Proposta indica uma decisão a validar. A indicação «Não» significa que a operação deve ficar indisponível para esse perfil.

| Operação | Professor | Administrador |
|---|---|---|

| Entrar com conta ETPM ativa | Sim | Sim |

| Consultar equipamentos e localizações | Sim | Sim |

| Atribuir equipamento e registar devolução | Sim | Sim |

| Marcar equipamento como avariado | Sim | Sim |

| Transferir equipamento entre salas | Sim | Sim |

| Transferir armário com equipamentos | Proposta | Sim |

| Registar e alterar a ficha de equipamento | Proposta | Sim |

| Criar ou alterar salas e armários | Proposta | Sim |

| Criar contas e alterar perfis | Não | sim |

| Desativar uma conta | Não | Sim |

| Reativar uma conta | Não | Proposta |

| Apagar uma conta | Não | Não |

| Apagar outros registos | Não |  sim mas fica nos logs |

  | Consultar histórico global e eventos | Nao | Sim |

| Confirmar saída da Sala de Reparação | Sim¹ | Sim¹ |

¹ A escolha de sala de destino é obrigatória. O estado exigido para permitir a saída deve ser confirmado; recomenda-se permitir a saída apenas quando o equipamento estiver operacional.

Regista as operações que realiza, confirma os equipamentos e destinos selecionados e fornece uma descrição quando comunica uma avaria. Não administra contas nem apaga informação.

Mantém as contas e a organização do inventário, gere as permissões aprovadas e acompanha os eventos. A desativação de uma conta não elimina operações feitas anteriormente por essa pessoa.


## 4 Contas e entrada no sistema

Recebe email e palavra-passe. Remove espaços no início e no fim do email e compara-o sem distinguir maiúsculas. Valida o domínio exato etpm.pt, a existência da conta, o estado Ativo e as credenciais. Uma conta inexistente, inativa ou com credenciais inválidas não entra. O perfil vem da conta guardada no servidor; o utilizador não escolhe ser Administrador ao entrar.

Exemplo de domínio válido: nome@etpm.pt. nome@etpm.pt.outro.pt não é válido. Não aceitar automaticamente subdomínios ou outros domínios sem decisão explícita da escola. O login de produção não utiliza a palavra-passe partilhada da demonstração.

Termina a sessão no servidor. Depois da saída, páginas e operações protegidas voltam a exigir autenticação. Usar o botão Voltar do navegador não pode restabelecer uma sessão terminada.

Proposta: apenas um Administrador pode criar contas de Professor ou Administrador. O email ETPM tem de ser único, incluindo contas inativas, para evitar identidades duplicadas e preservar o histórico. Não existe criação de conta por iniciativa do público.

Proposta: o Administrador pode alterar o nome e o perfil. O email fica imutável após a criação. A expressão “não pode ser apagado” é tratada como proibição de eliminar a conta e a sua identidade; a possibilidade de corrigir um email errado deve ser confirmada pelo docente.

Só o Administrador pode desativar. A operação guarda autor, data e motivo, impede novos logins e deve invalidar sessões ativas. O nome e o email permanecem disponíveis nas operações anteriores. Proposta: o Administrador também pode reativar a mesma conta, com registo do evento.

Proposta de proteção administrativa: impedir a desativação ou remoção de privilégios do último Administrador ativo. Confirmar também se um Administrador pode desativar a própria conta.


## 5 Inventário e localizações

A consulta mostra identificação, tipo, estado e localização. O registo exige código único e uma localização válida. Proposta: restringir a criação e alteração de fichas ao Administrador; o Professor continua a poder executar as operações de avaria e transferência autorizadas.

Uma sala identifica um espaço físico. Cada armário pertence a uma sala. Um equipamento fica diretamente numa sala ou associado a um armário; a sala desse armário determina a sua localização física. Não pode ficar simultaneamente associado a duas localizações.


## 6 Operações com equipamentos

Selecionar o equipamento e mostrar a origem atual. Escolher uma sala de destino válida, diferente da origem, e, quando aplicável, um armário dessa sala. Confirmar a operação. O sistema altera a localização e regista equipamento, origem, destino, autor e data. Uma transferência comum não altera automaticamente o estado do equipamento.

Selecionar armário e sala de destino. A mudança da sala do armário muda a localização física de todos os equipamentos que continuam associados a ele. Deve existir confirmação com a quantidade de equipamentos afetados e um evento que permita identificar os objetos abrangidos. A autorização do Professor para este caso permanece uma proposta.

Professor ou Administrador seleciona o equipamento e descreve o problema. Numa única operação, o sistema muda o estado para Avariado, remove a associação a um armário quando exista, coloca o equipamento diretamente na Sala de Reparação e regista a avaria e a movimentação. Se já estiver nessa sala, regista a mudança de estado sem inventar uma transferência entre salas iguais.

A Sala de Reparação deve existir antes de se permitir esta operação. Se não existir, a operação falha com uma mensagem clara; o sistema não pode gravar apenas parte da alteração. Uma repetição do mesmo pedido não deve duplicar a avaria nem os eventos.

O utilizador tem de escolher explicitamente a sala para onde o equipamento vai. Se escolher um armário, este tem de pertencer à sala indicada. O sistema não preenche um destino presumido a partir do histórico nem permite guardar sem destino.

Proposta a validar: nesta operação, confirmar que o equipamento está operacional e mudar o estado para Em funcionamento ao mesmo tempo que é transferido. Se continuar avariado, permanece na Sala de Reparação. Esta confirmação não é um módulo de reparação e não exige dados de técnico, peças, custos ou intervenção.

Professor ou Administrador seleciona um equipamento disponível e operacional e um destinatário válido. Regista o início da utilização e quem fez a atribuição. Um equipamento não pode ter duas atribuições ativas. Uma atribuição não muda a sala por si só; uma mudança física deve ser registada como transferência.

Selecionar uma atribuição aberta e confirmar a devolução, guardando data e autor. A data não pode ser anterior ao início. Quem recebe a devolução pode ser diferente de quem fez a atribuição. Fechar a utilização não apaga o histórico nem elimina uma avaria existente.


## 7 Histórico eventos e alertas

Cada operação concluída gera um evento com identificador, data e hora, autor e objeto afetado. Alterações de estado e localização guardam os valores anteriores e novos. A desativação de um utilizador preserva a ligação aos seus eventos. Consultas podem filtrar por período, equipamento, operação e autor, de acordo com as permissões aprovadas.

O dashboard apresenta resumos coerentes com os dados e as permissões. Um aviso de avaria pode identificar um equipamento que está na Sala de Reparação. Proposta: manter os alertas e os eventos sem edição manual pelo Professor. Limites de tempo e quantidade para outros alertas continuam por definir.


## 8 Responsabilidades das equipas

Criar ecrãs de entrada, inventário, salas, armários, atribuições, devoluções, avarias, transferências, utilizadores e consulta de eventos. Mostrar apenas ações autorizadas, pedir destino na saída da Sala de Reparação e apresentar erros e confirmações. Remover as vistas de Aluno e a função de registar reparação ou resolução da proposta anterior.

Autenticar e terminar sessões; validar domínio, estado da conta e permissões em cada pedido; filtrar os dados devolvidos; rejeitar operações proibidas mesmo por acesso direto; gravar avaria, localização e eventos de forma indivisível. Nunca aceitar o autor ou perfil enviado pelo navegador como prova de identidade.

Garantir unicidade de emails e códigos, relações válidas entre equipamentos, armários e salas, estados de conta e preservação do histórico. Manter o autor de cada operação e permitir consultar origem e destino. Impedir que uma operação incompleta deixe estado e localização inconsistentes.

As três equipas acordam nomes de campos, estados, identificadores, datas e mensagens de erro. Testam os mesmos cenários com Professor e Administrador, incluindo pedidos recusados e operações repetidas. O professor valida as propostas antes de serem tratadas como regras finais.


## 9 Decisões ainda por confirmar

Confirmar quem pode criar e alterar fichas, salas e armários; se o Professor pode transferir armários; quem consulta histórico global; se o email é imutável; quem reativa contas; e quais os registos que um Administrador pode eliminar. Proposta conservadora: preservar registos com histórico e usar inativação quando aplicável.

Confirmar o estado necessário para sair da Sala de Reparação e quem o confirma. Definir também o que acontece quando se comunica uma avaria ou transferência de equipamento com uma atribuição ativa. Até existir regra, não encerrar a atribuição silenciosamente; propor devolução prévia ou decisão explícita do docente.


## 10 Critérios de aceitação

Usar estes cenários para verificar a implementação conjunta. Os casos identificados como proposta só passam a ser obrigatórios depois de aprovação.

Uma conta ativa com email @etpm.pt e credenciais corretas entra. Email externo, conta inexistente, conta inativa ou palavra-passe errada são recusados.

O sistema apenas autentica Professores e Administradores. Um destinatário Aluno não ganha conta de acesso nem menu próprio.

O Professor não encontra ações de apagar ou desativar contas. Um pedido direto ao backend para executar essas ações também é recusado.

Uma conta desativada continua identificada no histórico e não pode iniciar sessão. Nenhuma ação elimina fisicamente a conta.

Marcar um equipamento como Avariado muda a localização para a Sala de Reparação e deixa registos coerentes da operação. Uma falha não permite gravar só metade da mudança.

Tentar retirar equipamento da Sala de Reparação sem sala de destino dá erro. Escolher um armário de outra sala também dá erro.

Uma transferência válida conserva a origem no histórico, muda a localização atual e regista autor e data. Destino igual à origem é recusado.

Uma segunda atribuição ativa do mesmo equipamento é recusada. Uma devolução anterior à atribuição é recusada. O autor da devolução fica registado separadamente.

Após Sair ou desativação da conta, novos pedidos protegidos exigem autenticação válida. O botão Voltar não concede acesso.

Não existem formulários de técnico, intervenção ou custos de reparação. A Sala de Reparação funciona como localização para equipamentos avariados.

Repetir a confirmação de uma operação não cria movimentos duplicados. O utilizador, o equipamento, a data e as alterações são consultáveis por quem tiver permissão.

## 11 Logs de auditoria e remoção de logs

O sistema mantém um registo de auditoria para permitir reconstruir o que aconteceu. Regista entradas e saídas de sessão, tentativas recusadas, consultas de páginas e filtros, criação e alteração de fichas, atribuições, devoluções, avarias, movimentos, alterações de contas e operações sobre os próprios logs. Não guarda palavras-passe, tokens de sessão nem o conteúdo de cada tecla escrita. “Tudo o que aconteceu” refere-se às ações e resultados dentro da aplicação, não à atividade fora dela.

Cada log tem um identificador único, data e hora, identificação e perfil do autor quando autenticado, ação, objeto afetado, resultado, motivo e, nas alterações de dados, valores anteriores e novos. Uma tentativa sem autenticação é identificada como tal, sem atribuir a identidade de uma pessoa apenas porque alguém escreveu o seu email. A hora oficial e o autor devem ser determinados pelo servidor em produção.

O Administrador consulta os logs e filtra por texto, resultado, período e visibilidade. O Professor não elimina logs nem acede à auditoria global nesta versão. A consulta da auditoria também fica registada.

“Apagar um log” significa retirá-lo da lista normal por remoção lógica, nunca destruir o original. Exige confirmação, motivo e permissão de Administrador. A operação cria um novo log de **Remoção lógica de log**, com autor, data, motivo, identificador do original e o seu conteúdo preservado. O original mantém-se consultável em **Todos, incluindo removidos** ou **Apenas removidos**. Uma segunda remoção do mesmo registo é recusada e auditada.

Os logs que registam remoções, logins, logouts e ações recusadas são protegidos na interface: não podem ser removidos nem editados. Assim, remover um registo não permite remover o rasto dessa ação. Nenhum perfil dispõe de um botão para apagar definitivamente a auditoria. Uma política de retenção e arquivo, se necessária, deve ser acordada separadamente.

Operação e log de auditoria devem ser gravados na mesma transação no backend. Se não for possível preservar a auditoria, uma alteração de dados não pode ser apresentada como concluída. Os dados de auditoria devem ser protegidos contra alterações diretas, com acesso controlado e cópias de segurança.

Na demonstração frontend, os dados e logs persistem apenas no armazenamento local desse navegador. Apagar esse armazenamento ou alterar o código pode destruir ou falsificar os dados. A demonstração comprova os fluxos, mas não fornece uma auditoria resistente a manipulação, sincronização entre computadores ou recuperação de dados apagados fora da aplicação.

### Testes adicionais de aceitação

1. Marcar um equipamento como avariado produz registos da mudança de estado e do movimento para a Sala de Reparação.
2. Remover um log exige motivo e cria um novo log protegido, sem alterar o conteúdo do original.
3. Filtrar por logs removidos permite consultar o original e relacioná-lo com o registo da remoção.
4. O Professor não pode remover logs nem desativar contas, mesmo enviando um pedido direto ao backend.
5. Uma tentativa recusada é registada sem palavras-passe ou outros segredos.
6. Uma conta desativada perde acesso; o seu nome continua no histórico das operações anteriores.

## 12 Decisões adotadas no protótipo para validação

Para tornar os percursos testáveis, o protótipo adota as propostas conservadoras: só o Administrador cria e altera fichas, salas, armários e contas, transfere armários e consulta histórico global, eventos e logs. O Professor consulta inventário e locais, atribui, recebe devoluções, comunica avarias e transfere equipamentos. Nenhum perfil apaga equipamentos, salas, armários ou contas.

A saída da Sala de Reparação exige confirmação de funcionamento e sala de destino, gravando estado e localização em conjunto. Equipamentos com utilização aberta exigem devolução antes de avaria ou transferência. O email da conta é imutável. O Administrador pode reativar contas, mas não desativar a própria nem retirar o perfil ao último Administrador ativo. Estas escolhas continuam sujeitas à aprovação do docente.
