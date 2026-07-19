-- db/init.sql
-- Runs once when the Postgres container is first created.

CREATE TABLE IF NOT EXISTS bills (
    id               SERIAL PRIMARY KEY,
    created_at       TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    bill_name        VARCHAR(100)   NOT NULL,
    amount_paid      NUMERIC(10, 2),            -- NULL until marked paid
    due_date         DATE           NOT NULL,
    recurs_monthly   BOOLEAN        DEFAULT FALSE,
    is_paid          BOOLEAN        DEFAULT FALSE,
    paid_at          TIMESTAMP
);