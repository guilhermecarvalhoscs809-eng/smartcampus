/* Regras da demonstração. O backend deve repetir estas validações e manter a auditoria no servidor. */
(function(root){
 'use strict';
 const copy=x=>JSON.parse(JSON.stringify(x));
 const uid=p=>p+'-'+(globalThis.crypto?.randomUUID?.()||Date.now().toString(36)+Math.random().toString(36).slice(2));
 const clean=x=>String(x??'').trim();
 const norm=x=>clean(x).toLowerCase();
 const demand=(ok,msg)=>{if(!ok)throw Error(msg)};
 const emailOK=x=>/^[^\s@]+@etpm\.pt$/i.test(clean(x));
 const pages={Professor:['dashboard','equipamentos','salas','armarios','assignacao','devolucao','avaria','transferencia'],Administrador:['dashboard','equipamentos','registar-equipamento','salas','armarios','assignacao','devolucao','avaria','transferencia','utilizacoes','eventos','logs','utilizadores','criar-utilizador']};
 const actions={equipamento:'registar-equipamento',sala:'admin',armario:'admin',conta:'admin',estadoConta:'admin',ocultarLog:'admin',atribuicao:'assignacao',devolucao:'devolucao',avaria:'avaria',transferencia:'transferencia'};
 // Resolve a conta ativa; em produção, o Flask obtém a identidade da sessão, nunca de um ID enviado pelo browser.
 const user=(s,id)=>s.utilizadores.find(u=>u.id===id&&u.estado==='Ativo'&&emailOK(u.email)&&pages[u.perfil]);
 // Matriz usada para controlar a interface. Cada rota Flask tem de voltar a verificar a permissão no servidor.
 const allowed=(s,id,key)=>!!pages[user(s,id)?.perfil]?.includes(key);
 // Procura um registo pelo ID; os IDs recebidos em POST devem ser validados contra a base de dados.
 const get=(s,collection,id)=>s[collection].find(x=>x.id===id);
 // Indica se existe atribuição sem devolução; usar esta regra ao impedir operações incompatíveis.
 const inUse=(s,id)=>s.atribuicoes.find(a=>a.id_equipamento===id&&!a.fim);
 // Equipamento só pode ser atribuído se estiver operacional e sem atribuição ativa.
 const available=(s,e)=>e.estado==='Em funcionamento'&&!inUse(s,e.id);
 // Resolve a sala efetiva de um equipamento, incluindo os que estão dentro de armários.
 const room=(s,e)=>e.tipo_local==='sala'?e.id_local:get(s,'armarios',e.id_local)?.id_sala;
 // Nome de localização apresentado na interface; não substitui validação de destino na API.
 const localName=(s,e)=>(e.tipo_local==='armario'?(get(s,'armarios',e.id_local)?.nome+' · '):'')+(get(s,'salas',room(s,e))?.nome||'Sem sala');
 // Apenas auditoria da demonstração. No Flask, registar ator da sessão, hora do servidor e snapshots na mesma transação da alteração.
 // Preservar campos compatíveis: id, data, ator, nome, perfil, acao, objeto, resultado, antes, depois, motivo e protegido.
 function audit(s,actor,acao,objeto,resultado='Sucesso',antes=null,depois=null,motivo='',protectedEntry=false){
  const u=s.utilizadores.find(u=>u.id===actor);
  const entry={id:uid('LOG'),data:new Date().toISOString(),ator:actor||null,nome:u?.nome||'Não autenticado',perfil:u?.perfil||'—',acao,objeto:clean(objeto),resultado,antes:copy(antes),depois:copy(depois),motivo:clean(motivo),protegido:protectedEntry};
  s.logs.push(entry);return entry;
 }
 // Evento de demonstração. Em produção, gravá-lo atomicamente com a operação e usar a identidade autenticada do servidor.
 function event(s,actor,tipo,objeto,descricao){s.eventos.push({id:uid('EV'),data:new Date().toISOString(),tipo,objeto,descricao,autor:actor});}
 // Login simulado apenas para testes locais (palavra-passe partilhada); não usar esta função nem estes dados no Flask.
 // A rota real deve autenticar a conta, criar sessão/cookie e registar sucesso ou recusa sem guardar palavra-passe/email submetidos.
 function login(s,email,password){
  const found=s.utilizadores.find(u=>norm(u.email)===norm(email));
  const ok=emailOK(email)&&found&&user(s,found.id)&&password==='demo1234';
  audit(s,ok?found.id:null,'Login','Sessão',ok?'Sucesso':'Recusado',null,null,ok?'':'Credenciais inválidas ou conta indisponível',true);
  return ok?found.id:null;
 }
 // Simula as operações da aplicação e serve de especificação funcional para os handlers Flask.
 // Campos por operação (além de id opcional nas criações/edições):
 // equipamento: codigo, nome, serie, tipo, id_sala, id_armario;
 // sala: nome; armario: nome, id_sala; conta: nome, email, perfil;
 // estadoConta: id, estado, motivo; atribuicao: id_equipamento, id_destinatario, data, prazo;
 // devolucao: id_atribuicao, data; avaria: id_equipamento, motivo, data;
 // transferencia: tipo_objeto, id_objeto, id_sala, id_armario, operacional, data;
 // ocultarLog: id, motivo. Logout é uma rota separada e recebe {}.
 // O input usa os nomes dos formulários; consultar documentos/INTEGRACAO.md para as respostas e o contrato HTTP.
 // Reimplementar as regras abaixo no backend com transação, sessão, autorização e auditoria no servidor; não confiar neste modelo.
 function execute(source,actor,kind,input){
  const s=copy(source),d=Object.fromEntries(Object.entries(input).map(([k,v])=>[k,typeof v==='string'?v.trim():v]));
  const u=user(s,actor),admin=u?.perfil==='Administrador';
  try{
   demand(u,'A sessão terminou ou a conta está inativa.');
   demand(actions[kind]&&(actions[kind]==='admin'?admin:allowed(s,actor,actions[kind])),'Sem permissão para esta operação.');
   let before=null,after=null,target='',label=kind;
   const editCollections={conta:'utilizadores',equipamento:'equipamentos',sala:'salas',armario:'armarios'};if(d.id&&editCollections[kind])demand(get(s,editCollections[kind],d.id),'O registo a alterar já não existe.');
   const time=()=>{const n=Date.parse(d.data);demand(Number.isFinite(n)&&n<=Date.now(),'Indique uma data válida que não seja futura.');return new Date(n).toISOString()};
   const reason=()=>{demand(clean(d.motivo).length>=3,'Indique um motivo com pelo menos 3 caracteres.');};
   if(kind==='conta'){
    demand(d.nome&&emailOK(d.email),'Indique nome e email do domínio etpm.pt.');demand(pages[d.perfil],'Perfil inválido.');
    let obj=get(s,'utilizadores',d.id);before=obj?copy(obj):null;
    demand(!s.utilizadores.some(v=>v.id!==d.id&&norm(v.email)===norm(d.email)),'Este email já existe, mesmo que a conta esteja inativa.');
    if(obj){demand(norm(obj.email)===norm(d.email),'O email da conta não pode ser alterado.');if(obj.perfil==='Administrador'&&d.perfil!=='Administrador'&&obj.estado==='Ativo')demand(s.utilizadores.filter(v=>v.estado==='Ativo'&&v.perfil==='Administrador').length>1,'É necessário manter um Administrador ativo.');obj.nome=d.nome;obj.perfil=d.perfil;}
    else{obj={id:uid('U'),nome:d.nome,email:norm(d.email),perfil:d.perfil,estado:'Ativo'};s.utilizadores.push(obj);}
    after=copy(obj);target=obj.id;label=before?'Conta alterada':'Conta criada';
   }else if(kind==='estadoConta'){
    reason();const obj=get(s,'utilizadores',d.id);demand(obj,'Conta inexistente.');demand(['Ativo','Inativo'].includes(d.estado)&&obj.estado!==d.estado,'Estado inválido ou já aplicado.');
    if(d.estado==='Inativo'){demand(obj.id!==actor,'Não pode desativar a própria conta.');if(obj.perfil==='Administrador')demand(s.utilizadores.filter(v=>v.estado==='Ativo'&&v.perfil==='Administrador').length>1,'É necessário manter um Administrador ativo.');}
    before=copy(obj);obj.estado=d.estado;after=copy(obj);target=obj.id;label=d.estado==='Inativo'?'Conta desativada':'Conta reativada';
   }else if(kind==='sala'||kind==='armario'){
    demand(d.nome,'Indique o nome.');const col=kind==='sala'?'salas':'armarios';let obj=get(s,col,d.id);before=obj?copy(obj):null;
    demand(!s[col].some(v=>v.id!==d.id&&norm(v.nome)===norm(d.nome)),'Já existe um registo com este nome.');
    if(kind==='armario'){demand(get(s,'salas',d.id_sala)&&d.id_sala!=='REP','Escolha uma sala válida fora da Sala de Reparação.');if(obj)demand(obj.id_sala===d.id_sala,'Use Transferências para mudar a sala do armário.');}
    if(obj){demand(obj.id!=='REP','A Sala de Reparação é uma localização reservada.');obj.nome=d.nome;}
    else{obj={id:uid(kind==='sala'?'S':'ARM'),nome:d.nome,...(kind==='armario'?{id_sala:d.id_sala}:{})};s[col].push(obj);}
    after=copy(obj);target=obj.id;label=(kind==='sala'?'Sala':'Armário')+(before?' alterado':' criado');
   }else if(kind==='equipamento'){
    demand(d.codigo&&d.nome&&d.serie&&['Portátil','PC all-in-one','Outro'].includes(d.tipo),'Preencha os dados do equipamento.');
    demand(!s.equipamentos.some(e=>e.id!==d.id&&(norm(e.codigo)===norm(d.codigo)||norm(e.serie)===norm(d.serie))),'Código ou número de série já existente.');
    let obj=get(s,'equipamentos',d.id);before=obj?copy(obj):null;
    if(obj){Object.assign(obj,{codigo:d.codigo,nome:d.nome,serie:d.serie,tipo:d.tipo});}
    else{demand(get(s,'salas',d.id_sala)&&d.id_sala!=='REP','Escolha uma sala operacional. Para avarias use a operação própria.');if(d.id_armario)demand(get(s,'armarios',d.id_armario)?.id_sala===d.id_sala,'Armário incompatível com a sala.');obj={id:uid('EQ'),codigo:d.codigo,nome:d.nome,serie:d.serie,tipo:d.tipo,estado:'Em funcionamento',tipo_local:d.id_armario?'armario':'sala',id_local:d.id_armario||d.id_sala};s.equipamentos.push(obj);}
    target=obj.id;after=copy(obj);label=before?'Equipamento alterado':'Equipamento registado';
   }else if(kind==='atribuicao'){
    const e=get(s,'equipamentos',d.id_equipamento),dest=[...s.destinatarios,...s.utilizadores.filter(v=>v.estado==='Ativo')].find(v=>v.id===d.id_destinatario);
    demand(e&&available(s,e),'Equipamento indisponível.');demand(dest,'Destinatário inválido.');
    const data=time();if(d.prazo)demand(Number.isFinite(Date.parse(d.prazo))&&Date.parse(d.prazo)>=Date.parse(data),'Prazo anterior à atribuição ou inválido.');
    after={id:uid('AT'),id_equipamento:e.id,id_destinatario:dest.id,id_utilizador:actor,inicio:data,prazo:d.prazo?new Date(d.prazo).toISOString():'',fim:null};s.atribuicoes.push(after);target=e.id;label='Atribuição';
   }else if(kind==='devolucao'){
    const a=get(s,'atribuicoes',d.id_atribuicao);demand(a&&!a.fim,'Atribuição inexistente ou já devolvida.');const data=time();demand(Date.parse(data)>=Date.parse(a.inicio),'A devolução não pode ser anterior à atribuição.');
    before=copy(a);a.fim=data;a.id_utilizador_devolucao=actor;after=copy(a);target=a.id_equipamento;label='Devolução';
   }else if(kind==='avaria'){
    const e=get(s,'equipamentos',d.id_equipamento);demand(e,'Equipamento inválido.');demand(e.estado!=='Avariado','A avaria já está registada.');demand(!inUse(s,e.id),'Registe primeiro a devolução; avarias durante utilização aguardam regra do docente.');demand(get(s,'salas','REP'),'A Sala de Reparação não está configurada.');reason();const data=time();before=copy(e);const origin=localName(s,e);
    e.estado='Avariado';e.tipo_local='sala';e.id_local='REP';after=copy(e);target=e.id;label='Equipamento avariado';s.avarias.push({id:uid('AV'),id_equipamento:e.id,descricao:d.motivo,data,autor:actor});
    if(room(source,before)!=='REP'){const movement={id:uid('TR'),tipo:'equipamento',id_objeto:e.id,origem:origin,destino:'Sala de Reparação',data,autor:actor};s.transferencias.push(movement);audit(s,actor,'Transferência automática',e.id,'Sucesso',{local:origin},{local:'Sala de Reparação'},'Avaria');}
   }else if(kind==='transferencia'){
    demand(['equipamento','armario'].includes(d.tipo_objeto),'Tipo inválido.');const arm=d.tipo_objeto==='armario';demand(!arm||admin,'Só o Administrador transfere armários nesta proposta.');
    const obj=get(s,arm?'armarios':'equipamentos',d.id_objeto);demand(obj,'Objeto inválido.');const dest=get(s,'salas',d.id_sala);demand(dest,'Escolha a sala de destino.');demand(dest.id!=='REP','Para encaminhar à Sala de Reparação, registe uma avaria.');
    const affected=arm?s.equipamentos.filter(e=>e.tipo_local==='armario'&&e.id_local===obj.id):[obj];demand(!affected.some(e=>inUse(s,e.id)),'Existe equipamento em utilização. Registe primeiro a devolução.');
    if(d.id_armario)demand(!arm&&get(s,'armarios',d.id_armario)?.id_sala===dest.id,'O armário não pertence à sala escolhida.');
    const out=!arm&&room(s,obj)==='REP';if(out)demand(d.operacional==='sim','Confirme que o equipamento está operacional para sair da Sala de Reparação.');
    if(!out)demand(!affected.some(e=>e.estado==='Avariado'),'Equipamento avariado deve permanecer na Sala de Reparação.');
    demand(arm?obj.id_sala!==dest.id:!(obj.tipo_local===(d.id_armario?'armario':'sala')&&obj.id_local===(d.id_armario||dest.id)),'A origem e o destino são iguais.');
    const data=time(),origin=arm?get(s,'salas',obj.id_sala).nome:localName(s,obj);before=copy({objeto:obj,equipamentos:affected});
    if(arm)obj.id_sala=dest.id;else{obj.tipo_local=d.id_armario?'armario':'sala';obj.id_local=d.id_armario||dest.id;if(out)obj.estado='Em funcionamento';}
    const movement={id:uid('TR'),tipo:d.tipo_objeto,id_objeto:obj.id,origem:origin,destino:dest.nome+(d.id_armario?' / '+get(s,'armarios',d.id_armario).nome:''),data,autor:actor,equipamentos:affected.map(e=>e.id)};
    s.transferencias.push(movement);after=copy({objeto:obj,movimento:movement});target=obj.id;label=out?'Saída da Sala de Reparação':'Transferência';
   }else if(kind==='ocultarLog'){
    reason();const entry=get(s,'logs',d.id);demand(entry,'Log inexistente.');demand(!entry.protegido,'Este log de auditoria é protegido e não pode ser removido.');demand(!s.logs.some(l=>l.acao==='Remoção lógica de log'&&l.objeto===entry.id),'Este log já foi removido da lista normal.');
    audit(s,actor,'Remoção lógica de log',entry.id,'Sucesso',{log:entry},{visibilidade:'Removido da lista normal'},d.motivo,true);return {state:s,ok:true,message:'Log removido da lista normal. O original e a remoção continuam na auditoria.'};
   }else throw Error('Operação desconhecida.');
   audit(s,actor,label,target,'Sucesso',before,after,d.motivo||'');event(s,actor,label,target,d.motivo||label);
   return {state:s,ok:true,message:'Operação registada com sucesso. O histórico e os logs foram atualizados.'};
  }catch(err){const failed=copy(source);audit(failed,actor,'Operação recusada: '+kind,d.id||d.id_equipamento||d.id_objeto||'—','Recusado',null,null,err.message,true);return {state:failed,ok:false,message:err.message};}
 }
 const api={copy,uid,emailOK,pages,user,allowed,get,inUse,available,room,localName,audit,login,execute};
 if(typeof module!=='undefined')module.exports=api;root.SmartCampusModel=api;
})(typeof window!=='undefined'?window:globalThis);
