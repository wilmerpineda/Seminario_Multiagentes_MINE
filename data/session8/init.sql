CREATE TABLE IF NOT EXISTS regions (region TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS customers (customer TEXT PRIMARY KEY, region TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sellers (seller TEXT PRIMARY KEY, region TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, period DATE NOT NULL, region TEXT NOT NULL, seller TEXT NOT NULL, customer TEXT NOT NULL, revenue NUMERIC(14,2) NOT NULL, cost NUMERIC(14,2) NOT NULL);
CREATE TABLE IF NOT EXISTS opportunities (id INTEGER PRIMARY KEY, period DATE NOT NULL, region TEXT NOT NULL, seller TEXT NOT NULL, customer TEXT NOT NULL, status TEXT NOT NULL, cycle_days INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY, period DATE NOT NULL, region TEXT NOT NULL, actual_revenue NUMERIC(14,2) NOT NULL, target_revenue NUMERIC(14,2) NOT NULL);
CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, period DATE NOT NULL, region TEXT NOT NULL, customer TEXT NOT NULL, balance NUMERIC(14,2) NOT NULL, payment_status TEXT NOT NULL, due_date DATE NOT NULL);

INSERT INTO regions(region) VALUES ('Andina'), ('Caribe'), ('Pacífica'), ('Centro') ON CONFLICT DO NOTHING;
INSERT INTO customers(customer, region) VALUES ('Acme SAS','Andina'),('Norte Ltda','Caribe'),('Pacífico SA','Pacífica'),('Central SAS','Centro') ON CONFLICT DO NOTHING;
INSERT INTO sellers(seller, region) VALUES ('Ana','Andina'),('Bruno','Caribe'),('Carla','Pacífica'),('Diego','Centro') ON CONFLICT DO NOTHING;

INSERT INTO sales
SELECT n, (DATE '2025-01-01' + ((n-1) % 24) * INTERVAL '1 month')::date,
       (ARRAY['Andina','Caribe','Pacífica','Centro'])[((n-1)%4)+1],
       (ARRAY['Ana','Bruno','Carla','Diego'])[((n-1)%4)+1],
       (ARRAY['Acme SAS','Norte Ltda','Pacífico SA','Central SAS'])[((n-1)%4)+1],
       8000000 + (n%12)*350000 + CASE WHEN n%4=0 THEN 900000 ELSE 0 END,
       5200000 + (n%10)*220000
FROM generate_series(1,192) n ON CONFLICT DO NOTHING;

INSERT INTO opportunities
SELECT n, (DATE '2025-01-01' + ((n-1)%24)*INTERVAL '1 month')::date,
       (ARRAY['Andina','Caribe','Pacífica','Centro'])[((n-1)%4)+1],
       (ARRAY['Ana','Bruno','Carla','Diego'])[((n-1)%4)+1],
       (ARRAY['Acme SAS','Norte Ltda','Pacífico SA','Central SAS'])[((n-1)%4)+1],
       CASE WHEN n%3=0 THEN 'won' ELSE 'lost' END, 15+(n%70)
FROM generate_series(1,240) n ON CONFLICT DO NOTHING;

INSERT INTO goals
SELECT n, (DATE '2025-01-01' + ((n-1)%24)*INTERVAL '1 month')::date,
       (ARRAY['Andina','Caribe','Pacífica','Centro'])[((n-1)%4)+1], 38000000+(n%5)*600000, 40000000
FROM generate_series(1,96) n ON CONFLICT DO NOTHING;

INSERT INTO payments
SELECT n, (DATE '2025-01-01' + ((n-1)%24)*INTERVAL '1 month')::date,
       (ARRAY['Andina','Caribe','Pacífica','Centro'])[((n-1)%4)+1],
       (ARRAY['Acme SAS','Norte Ltda','Pacífico SA','Central SAS'])[((n-1)%4)+1],
       1000000+(n%8)*250000, CASE WHEN n%4=0 THEN 'overdue' ELSE 'paid' END,
       DATE '2026-01-01' + (n%120)
FROM generate_series(1,120) n ON CONFLICT DO NOTHING;

DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bi_reader') THEN
    CREATE ROLE bi_reader LOGIN PASSWORD 'local-reader-password';
  END IF;
END $$;
GRANT CONNECT ON DATABASE session8 TO bi_reader;
GRANT USAGE ON SCHEMA public TO bi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bi_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO bi_reader;
