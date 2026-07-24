-- 001_initial_schema.sql
-- Esquema inicial: 6 tablas + pgvector (maestro.md sección 6).
-- Idempotente: se puede re-ejecutar sin error sobre una BD ya inicializada.

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 1. usuarios
-- ============================================
CREATE TABLE IF NOT EXISTS usuarios (
    id            BIGSERIAL PRIMARY KEY,
    phone_number  TEXT UNIQUE NOT NULL,
    nombre        TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================
-- 2. perfiles_cliente
-- ============================================
CREATE TABLE IF NOT EXISTS perfiles_cliente (
    id                     BIGSERIAL PRIMARY KEY,
    user_id                BIGINT NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE,
    scoring_crediticio     INTEGER,
    productos_contratados  JSONB DEFAULT '[]'::jsonb,
    segmento               TEXT,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================
-- 3. cuentas
-- ============================================
CREATE TABLE IF NOT EXISTS cuentas (
    id                BIGSERIAL PRIMARY KEY,
    user_id           BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo_cuenta       TEXT NOT NULL,
    saldo_disponible  NUMERIC(12,2) NOT NULL DEFAULT 0,
    saldo_bloqueado   NUMERIC(12,2) NOT NULL DEFAULT 0,
    moneda            TEXT NOT NULL DEFAULT 'PEN',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cuentas_user_id ON cuentas(user_id);

-- ============================================
-- 4. movimientos
-- ============================================
CREATE TABLE IF NOT EXISTS movimientos (
    id           BIGSERIAL PRIMARY KEY,
    cuenta_id    BIGINT NOT NULL REFERENCES cuentas(id) ON DELETE CASCADE,
    fecha        TIMESTAMPTZ NOT NULL DEFAULT now(),
    monto        NUMERIC(12,2) NOT NULL,
    descripcion  TEXT,
    tipo         TEXT NOT NULL CHECK (tipo IN ('debito', 'credito'))
);

CREATE INDEX IF NOT EXISTS idx_movimientos_cuenta_id ON movimientos(cuenta_id);

-- ============================================
-- 5. operaciones
-- ============================================
CREATE TABLE IF NOT EXISTS operaciones (
    id                BIGSERIAL PRIMARY KEY,
    user_id           BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    cuenta_origen_id  BIGINT NOT NULL REFERENCES cuentas(id) ON DELETE CASCADE,
    monto             NUMERIC(12,2) NOT NULL,
    destino           TEXT NOT NULL,
    estado            TEXT NOT NULL DEFAULT 'pendiente'
                        CHECK (estado IN ('pendiente', 'confirmada', 'cancelada', 'ejecutada')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    confirmed_at      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_operaciones_user_id ON operaciones(user_id);
CREATE INDEX IF NOT EXISTS idx_operaciones_cuenta_origen_id ON operaciones(cuenta_origen_id);

-- ============================================
-- 6. bank_documents (RAG semántico, sin FK)
-- ============================================
CREATE TABLE IF NOT EXISTS bank_documents (
    id          BIGSERIAL PRIMARY KEY,
    content     TEXT NOT NULL,
    embedding   vector(1536) NOT NULL,
    category    TEXT,
    metadata    JSONB DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice ivfflat para búsqueda semántica aproximada
-- lists = 100 recomendado para dataset chico; recalcular (~filas/1000) si crece
CREATE INDEX IF NOT EXISTS idx_bank_documents_embedding
    ON bank_documents
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
