-- Table: public.members
-- Purpose: Application login accounts mapped 1:1 to players

CREATE TABLE IF NOT EXISTS public.members (
    id               SERIAL PRIMARY KEY,
    user_id          TEXT NOT NULL,                      -- login username
    password_hash    TEXT NOT NULL,                      -- store a hash, not plaintext
    players_id       INT4  NOT NULL,                     -- FK -> players(id)
    register_date    TIMESTAMP NOT NULL DEFAULT now(),
    is_free_package  BOOL NOT NULL DEFAULT TRUE,
    is_active        BOOL NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMP NOT NULL DEFAULT now(),
    updated_at       TIMESTAMP NOT NULL DEFAULT now(),

    CONSTRAINT members_user_id_unique UNIQUE (user_id),
    CONSTRAINT members_players_id_unique UNIQUE (players_id),
    CONSTRAINT members_players_id_fkey
        FOREIGN KEY (players_id) REFERENCES public.players(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Keep updated_at fresh
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_members_updated_at ON public.members;
CREATE TRIGGER trg_members_updated_at
BEFORE UPDATE ON public.members
FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

-- Helpful index for quick lookups by user_id
CREATE INDEX IF NOT EXISTS idx_members_user_id ON public.members(user_id);
