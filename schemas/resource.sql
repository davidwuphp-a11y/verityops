PRAGMA foreign_keys=ON;

CREATE TABLE orders(order_id TEXT PRIMARY KEY NOT NULL, status TEXT, paid INTEGER, approved INTEGER,
                                permitted INTEGER, clock INTEGER, deadline INTEGER);

CREATE TABLE payments(id INTEGER PRIMARY KEY,
                order_id TEXT NOT NULL REFERENCES orders(order_id), request_key TEXT UNIQUE,
                amount INTEGER, actor TEXT, approved INTEGER, permitted INTEGER,
                status TEXT, clock INTEGER, deadline INTEGER);

CREATE TABLE tickets(order_ref TEXT PRIMARY KEY NOT NULL REFERENCES orders(order_id), status TEXT);
