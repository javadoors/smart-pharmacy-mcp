CREATE TABLE IF NOT EXISTS drugs (
  id BIGINT PRIMARY KEY,
  name TEXT NOT NULL,
  generic_name TEXT,
  spec TEXT,
  manufacturer TEXT,
  is_rx BOOLEAN DEFAULT FALSE,
  contraindications_json JSONB,
  flags_json JSONB
);

CREATE TABLE IF NOT EXISTS inventory (
  drug_id BIGINT REFERENCES drugs(id),
  stock INT DEFAULT 0,
  batch_no TEXT,
  expire_date DATE
);

CREATE TABLE IF NOT EXISTS prices (
  drug_id BIGINT REFERENCES drugs(id),
  list_price NUMERIC(10,2),
  member_tier TEXT,
  discount_rate NUMERIC(5,2) DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS orders (
  id BIGSERIAL PRIMARY KEY,
  member_id BIGINT,
  total NUMERIC(10,2),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
  order_id BIGINT REFERENCES orders(id),
  drug_id BIGINT,
  qty INT,
  unit_price NUMERIC(10,2),
  final_price NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGSERIAL PRIMARY KEY,
  actor TEXT,
  action TEXT,
  entity TEXT,
  before JSONB,
  after JSONB,
  ts TIMESTAMP DEFAULT NOW()
);