-- Tenants
CREATE TABLE IF NOT EXISTS tenants (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(255) UNIQUE NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Users (Auth service)
CREATE TABLE IF NOT EXISTS users (
    id             SERIAL PRIMARY KEY,
    email          VARCHAR(255) NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    tenant_id      INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (email, tenant_id)
);

-- Cars (Car service)
CREATE TABLE IF NOT EXISTS cars (
    id             SERIAL PRIMARY KEY,
    brand          VARCHAR(255) NOT NULL,
    model          VARCHAR(255) NOT NULL,
    plate          VARCHAR(64) NOT NULL,
    hourly_rate    INTEGER NOT NULL, -- in smallest unit (e.g. cents)
    owner_user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id      INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    status         VARCHAR(32) NOT NULL DEFAULT 'active',
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (plate, tenant_id)
);

-- Bookings (Booking service)
CREATE TABLE IF NOT EXISTS bookings (
    id               SERIAL PRIMARY KEY,
    car_id           INTEGER NOT NULL REFERENCES cars(id) ON DELETE CASCADE,
    borrower_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id        INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    start_time       TIMESTAMP NOT NULL,
    end_time         TIMESTAMP NOT NULL,
    status           VARCHAR(32) NOT NULL DEFAULT 'requested', -- requested, confirmed, cancelled, completed
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
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