PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS records (
    collection TEXT NOT NULL CHECK (
        collection IN (
            'salas', 'armarios', 'equipamentos', 'utilizadores',
            'destinatarios', 'atribuicoes', 'avarias', 'transferencias',
            'eventos', 'logs'
        )
    ),
    id TEXT NOT NULL,
    data_json TEXT NOT NULL CHECK (json_valid(data_json)),
    PRIMARY KEY (collection, id)
);

CREATE UNIQUE INDEX IF NOT EXISTS unique_user_email
    ON records (lower(json_extract(data_json, '$.email')))
    WHERE collection = 'utilizadores';

CREATE UNIQUE INDEX IF NOT EXISTS unique_equipment_code
    ON records (lower(json_extract(data_json, '$.codigo')))
    WHERE collection = 'equipamentos';

CREATE UNIQUE INDEX IF NOT EXISTS unique_equipment_serial
    ON records (lower(json_extract(data_json, '$.serie')))
    WHERE collection = 'equipamentos';

CREATE UNIQUE INDEX IF NOT EXISTS one_open_assignment_per_equipment
    ON records (json_extract(data_json, '$.id_equipamento'))
    WHERE collection = 'atribuicoes'
      AND json_type(data_json, '$.fim') = 'null';

CREATE TABLE IF NOT EXISTS credentials (
    user_id TEXT PRIMARY KEY,
    password_salt TEXT NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    csrf_token TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS sessions_expiry ON sessions (expires_at);
