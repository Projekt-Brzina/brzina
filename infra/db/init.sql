DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = 'brzina_user'
    ) THEN
        CREATE ROLE brzina_user LOGIN PASSWORD 'changeme';
    END IF;
END
$$;
-- Tenants
CREATE TABLE IF NOT EXISTS tenants (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(255) UNIQUE NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Insert demo tenant if not exists
INSERT INTO tenants (id, name, slug)
    VALUES (1, 'Demo Tenant', 'demo')
    ON CONFLICT (id) DO NOTHING;


CREATE TABLE IF NOT EXISTS users (
    id             SERIAL PRIMARY KEY,
    email          VARCHAR(255) NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    name           VARCHAR(255),
    tenant_id      INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    payment_info   VARCHAR(255),
    is_admin       BOOLEAN NOT NULL DEFAULT FALSE,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (email, tenant_id)
);


CREATE TABLE IF NOT EXISTS cars (
    id             SERIAL PRIMARY KEY,
    brand          VARCHAR(255) NOT NULL,
    model          VARCHAR(255) NOT NULL,
    plate          VARCHAR(64) NOT NULL,
    hourly_rate    NUMERIC(10,2) NOT NULL,
    owner_user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id      INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    year           INTEGER,
    color          VARCHAR(64),
    description    TEXT,
    status         VARCHAR(32) NOT NULL DEFAULT 'active',
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (plate, tenant_id)
);


CREATE TABLE IF NOT EXISTS bookings (
    id                 SERIAL PRIMARY KEY,
    car_id             INTEGER NOT NULL REFERENCES cars(id) ON DELETE CASCADE,
    borrower_user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id          INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    start_time         TIMESTAMP NOT NULL,
    end_time           TIMESTAMP NOT NULL,
    total_cost         NUMERIC(10,2),
    status             VARCHAR(32) NOT NULL DEFAULT 'requested', -- requested, confirmed, cancelled, completed
    payment_status     VARCHAR(32),
    cancellation_reason VARCHAR(255),
    created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Booking Events (Event Sourcing)
CREATE TABLE IF NOT EXISTS booking_events (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER NOT NULL,
    tenant_id INTEGER NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    event_data JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Payments (Payment service)
CREATE TABLE IF NOT EXISTS payments (
    id           SERIAL PRIMARY KEY,
    booking_id   INTEGER NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    tenant_id    INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    amount       INTEGER NOT NULL,
    status       VARCHAR(32) NOT NULL DEFAULT 'pending', -- pending, success, failed
    mock_ref     VARCHAR(255),
    created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);