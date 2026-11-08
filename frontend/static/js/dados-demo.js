/* Email docente autorizado; restantes contas e operações são demonstração. */
window.SMARTCAMPUS_SEED = {
  "salas": [
    {
      "id": "S-01",
      "nome": "Sala T1"
    },
    {
      "id": "S-02",
      "nome": "Sala D12"
    },
    {
      "id": "REP",
      "nome": "Sala de Reparação"
    }
  ],
  "armarios": [
    {
      "id": "ARM-01",
      "nome": "Armário A1",
      "id_sala": "S-01"
    },
    {
      "id": "ARM-02",
      "nome": "Armário A2",
      "id_sala": "S-02"
    }
  ],
  "equipamentos": [
    {
      "id": "EQ-001",
      "codigo": "PORT-014",
      "nome": "Portátil 014",
      "tipo": "Portátil",
      "serie": "DEMO-014",
      "estado": "Em funcionamento",
      "tipo_local": "armario",
      "id_local": "ARM-01"
    },
    {
      "id": "EQ-002",
      "codigo": "PORT-028",
      "nome": "Portátil 028",
      "tipo": "Portátil",
      "serie": "DEMO-028",
      "estado": "Em funcionamento",
      "tipo_local": "armario",
      "id_local": "ARM-01"
    },
    {
      "id": "EQ-003",
      "codigo": "AIO-006",
      "nome": "PC AIO 006",
      "tipo": "PC all-in-one",
      "serie": "DEMO-006",
      "estado": "Avariado",
      "tipo_local": "sala",
      "id_local": "REP"
    },
    {
      "id": "EQ-004",
      "codigo": "PORT-021",
      "nome": "Portátil 021",
      "tipo": "Portátil",
      "serie": "DEMO-021",
      "estado": "Em funcionamento",
      "tipo_local": "sala",
      "id_local": "S-02"
    }
  ],
  "utilizadores": [
    {
      "id": "U-01",
      "nome": "António Correia (conta demo)",
      "email": "Antonio.correia@etpm.pt",
      "perfil": "Professor",
      "estado": "Ativo"
    },
    {
      "id": "U-02",
      "nome": "Carlos Mendes (exemplo)",
      "email": "carlos.demo@etpm.pt",
      "perfil": "Professor",
      "estado": "Ativo"
    },
    {
      "id": "U-05",
      "nome": "Administrador (demonstração)",
      "email": "admin.demo@etpm.pt",
      "perfil": "Administrador",
      "estado": "Ativo"
    }
  ],
  "atribuicoes": [
    {
      "id": "AT-001",
      "id_equipamento": "EQ-002",
      "id_destinatario": "U-03",
      "id_utilizador": "U-01",
      "inicio": "2026-11-03T09:15",
      "prazo": "",
      "fim": null
    },
    {
      "id": "AT-002",
      "id_equipamento": "EQ-001",
      "id_destinatario": "U-04",
      "id_utilizador": "U-02",
      "inicio": "2026-11-02T10:00",
      "prazo": "",
      "fim": "2026-11-02T12:00",
      "id_utilizador_devolucao": "U-01"
    }
  ],
  "avarias": [
    {
      "id": "AV-001",
      "id_equipamento": "EQ-003",
      "descricao": "Ecrã com falhas de imagem.",
      "data": "2026-11-02T14:00",
      "id_utilizador": "U-01",
      "resolucao": null
    }
  ],
  "transferencias": [
    {
      "id": "TR-001",
      "tipo": "equipamento",
      "id_objeto": "EQ-003",
      "origem": "Sala T1",
      "destino": "Sala Reparações",
      "data": "2026-11-02T14:00",
      "id_utilizador": "U-01"
    }
  ],
  "eventos": [
    {
      "id": "EV-004",
      "data": "2026-11-02T14:00",
      "tipo": "Transferência",
      "equipamento": "PC AIO 006",
      "utilizador": "António Correia (conta demo)",
      "descricao": "Sala T1 → Sala Reparações (avaria).",
      "aviso": false,
      "objeto": "PC AIO 006",
      "autor": "U-01"
    },
    {
      "id": "EV-005",
      "data": "2026-11-02T10:00",
      "tipo": "Atribuição",
      "equipamento": "Portátil 014",
      "utilizador": "Carlos Mendes (exemplo)",
      "descricao": "Equipamento atribuído a Marta Silva (exemplo).",
      "aviso": false,
      "objeto": "Portátil 014",
      "autor": "U-01"
    },
    {
      "id": "EV-001",
      "data": "2026-11-03T09:15",
      "tipo": "Atribuição",
      "equipamento": "Portátil 028",
      "utilizador": "António Correia (conta demo)",
      "descricao": "Equipamento atribuído a Diogo Santos (exemplo).",
      "aviso": false,
      "objeto": "Portátil 028",
      "autor": "U-01"
    },
    {
      "id": "EV-002",
      "data": "2026-11-02T14:00",
      "tipo": "Avaria",
      "equipamento": "PC AIO 006",
      "utilizador": "António Correia (conta demo)",
      "descricao": "Ecrã com falhas. Encaminhado para Sala Reparações.",
      "aviso": true,
      "objeto": "PC AIO 006",
      "autor": "U-01"
    },
    {
      "id": "EV-003",
      "data": "2026-11-02T12:00",
      "tipo": "Devolução",
      "equipamento": "Portátil 014",
      "utilizador": "António Correia (conta demo)",
      "descricao": "Utilização encerrada.",
      "aviso": false,
      "objeto": "Portátil 014",
      "autor": "U-01"
    }
  ],
  "destinatarios": [
    {
      "id": "U-03",
      "nome": "Diogo Santos (exemplo)",
      "tipo": "Aluno"
    },
    {
      "id": "U-04",
      "nome": "Marta Silva (exemplo)",
      "tipo": "Aluno"
    }
  ],
  "logs": [
    {
      "id": "LOG-INICIAL",
      "data": "2026-11-05T09:00:00.000Z",
      "ator": null,
      "nome": "Sistema de demonstração",
      "perfil": "Sistema",
      "acao": "Dados de exemplo carregados",
      "objeto": "Demonstração",
      "resultado": "Sucesso",
      "antes": null,
      "depois": {
        "equipamentos": 4,
        "contas": 3
      },
      "motivo": "Estado inicial fictício; os eventos anteriores são exemplos.",
      "protegido": true
    }
  ]
};