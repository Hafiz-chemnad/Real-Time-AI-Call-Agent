"""initial schema

Revision ID: 54186b2fed3f
Revises: 
Create Date: 2026-07-26 22:07:58.439283

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54186b2fed3f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    -- =====================================================================
-- Agent — Full Postgres Schema (Milestone 3: Make Everything Dynamic)
-- =====================================================================
-- Run this against your Postgres database (Supabase or local).
-- Requires the pgvector extension for the vector-mode knowledge base.
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS vector;     -- for knowledge_chunks embeddings

-- ---------------------------------------------------------------------
-- businesses — the root table, everything else references this
-- ---------------------------------------------------------------------
CREATE TABLE businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    tone VARCHAR(100),
    hours TEXT,
    transfer_numbers JSONB,
    knowledge_mode VARCHAR(20) NOT NULL DEFAULT 'vectorless'
        CHECK (knowledge_mode IN ('vectorless', 'vector')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- prompts — one system prompt per business (one-to-one for now)
-- ---------------------------------------------------------------------
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    system_prompt_template TEXT NOT NULL,
    variables JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (business_id)
);

-- ---------------------------------------------------------------------
-- guardrails — one guardrail config per business (one-to-one for now)
-- ---------------------------------------------------------------------
CREATE TABLE guardrails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    scope TEXT,
    out_of_scope_response TEXT,
    require_confirmation_for JSONB,
    escalate_on JSONB,
    never_reveal JSONB,
    no_hallucination_instruction TEXT,
    pii_handling_instruction TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (business_id)
);

-- ---------------------------------------------------------------------
-- tools — many tools per business (form-based or webhook-based)
-- ---------------------------------------------------------------------
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    execution_type VARCHAR(20) NOT NULL CHECK (execution_type IN ('api', 'webhook')),
    parameters JSONB NOT NULL,

    -- used when execution_type = 'api'
    url TEXT,
    method VARCHAR(10),
    auth_config JSONB,
    body_template JSONB,

    -- used when execution_type = 'webhook'
    webhook_url TEXT,

    requires_confirmation BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (business_id, tool_name)
);

-- ---------------------------------------------------------------------
-- knowledge_base — vectorless text OR pointer to a vector collection
-- ---------------------------------------------------------------------
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    mode VARCHAR(20) NOT NULL CHECK (mode IN ('vectorless', 'vector')),

    -- used when mode = 'vectorless'
    content TEXT,

    -- used when mode = 'vector'
    vector_collection_id VARCHAR(255),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- knowledge_chunks — actual embedded chunks, only used in vector mode
-- ---------------------------------------------------------------------
CREATE TABLE knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- adjust dimension to match your embedding model
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_knowledge_chunks_embedding
    ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX idx_knowledge_chunks_business_id
    ON knowledge_chunks(business_id);

-- ---------------------------------------------------------------------
-- call_logs — every interaction, across every channel
-- ---------------------------------------------------------------------
CREATE TABLE call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    channel VARCHAR(20) NOT NULL DEFAULT 'phone'
        CHECK (channel IN ('phone', 'chat', 'voice_web')),
    transcript TEXT,
    summary TEXT,
    tools_called JSONB,
    latency_metrics JSONB,
    escalated BOOLEAN NOT NULL DEFAULT false,
    escalation_reason VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_call_logs_business_id ON call_logs(business_id);
CREATE INDEX idx_call_logs_created_at ON call_logs(created_at);

-- ---------------------------------------------------------------------
-- Auto-update `updated_at` on row changes (applies to all relevant tables)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_businesses_updated_at
    BEFORE UPDATE ON businesses
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_prompts_updated_at
    BEFORE UPDATE ON prompts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_guardrails_updated_at
    BEFORE UPDATE ON guardrails
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_tools_updated_at
    BEFORE UPDATE ON tools
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_knowledge_base_updated_at
    BEFORE UPDATE ON knowledge_base
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)

def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS call_logs, knowledge_chunks, knowledge_base,
        tools, guardrails, prompts, businesses CASCADE;
    """)