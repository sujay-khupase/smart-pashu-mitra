-- Smart Pashu Mitra Database Schema

CREATE TABLE IF NOT EXISTS farmers (
    farmer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    village TEXT NOT NULL,
    mobile TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS animals (
    animal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    breed TEXT NOT NULL,
    age INTEGER NOT NULL,
    weight REAL NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (farmer_id) REFERENCES farmers (farmer_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vaccinations (
    vaccination_id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id INTEGER NOT NULL,
    vaccine_name TEXT NOT NULL,
    last_date TEXT,
    next_due_date TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (animal_id) REFERENCES animals (animal_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS health_queries (
    query_id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id INTEGER,
    symptom TEXT NOT NULL,
    advice TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (animal_id) REFERENCES animals (animal_id) ON DELETE SET NULL
);
