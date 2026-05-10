-- SQL schema
-- ---------------------------------------------------------
-- MATERIAL MASTER TABLE
-- Stores base water footprint values for each fiber
-- ---------------------------------------------------------

CREATE TABLE IF NOT EXISTS Material_Master (
    material_id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_name TEXT UNIQUE NOT NULL,

    WF_Green REAL NOT NULL CHECK(WF_Green >= 0),
    WF_Blue_Agri REAL NOT NULL CHECK(WF_Blue_Agri >= 0),
    WF_Grey_Agri REAL NOT NULL CHECK(WF_Grey_Agri >= 0),
    WF_Blue_Ind REAL NOT NULL CHECK(WF_Blue_Ind >= 0),
    WF_Grey_Ind REAL NOT NULL CHECK(WF_Grey_Ind >= 0),
    total_WF REAL NOT NULL CHECK(total_WF >= 0)
);

-- Index for faster material lookups
CREATE INDEX IF NOT EXISTS idx_material_name ON Material_Master(material_name);

-- ---------------------------------------------------------
-- PROCESS MASTER TABLE
-- Stores wet-processing / finishing impacts
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS Process_Master (
    process_id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_name TEXT UNIQUE NOT NULL,
    blue_add REAL NOT NULL CHECK(blue_add >= 0),
    grey_add REAL NOT NULL CHECK(grey_add >= 0)
);

-- Index for faster process lookups
CREATE INDEX IF NOT EXISTS idx_process_name ON Process_Master(process_name);

-- ---------------------------------------------------------
-- TRANSACTION LOGS
-- Stores every calculation performed by the user
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS Transaction_Log (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input_material TEXT NOT NULL,
    weight_entered REAL NOT NULL CHECK(weight_entered >= 0),
    selected_finishes TEXT,              -- comma-separated list
    calculated_output REAL NOT NULL CHECK(calculated_output >= 0),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------
-- CLUSTER MAP
-- Stores ML K-Means results
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS Cluster_Map (
    material_name TEXT PRIMARY KEY,
    cluster_id INTEGER NOT NULL CHECK(cluster_id >= 0)
);


-- ---------------------------------------------------------
-- OVERHEAD MASTER TABLE
-- Stores fixed manufacturing water use per process/item
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS Overhead_Master (
    process_name TEXT PRIMARY KEY,
    overhead REAL NOT NULL CHECK(overhead >= 0)
);

-- Insert realistic overhead values
INSERT OR IGNORE INTO Overhead_Master VALUES ('Default', 5.0);          -- baseline overhead
INSERT OR IGNORE INTO Overhead_Master VALUES ('Scouring', 12.0);        -- pretreatment step
INSERT OR IGNORE INTO Overhead_Master VALUES ('Desizing', 10.0);        -- starch removal
INSERT OR IGNORE INTO Overhead_Master VALUES ('Reactive Dyeing', 20.0); -- high water use
INSERT OR IGNORE INTO Overhead_Master VALUES ('Bio-Polishing', 8.0);    -- enzyme treatment
INSERT OR IGNORE INTO Overhead_Master VALUES ('Printing', 15.0);        -- screen/digital printing
INSERT OR IGNORE INTO Overhead_Master VALUES ('Finishing', 18.0);       -- water repellent/softener
INSERT OR IGNORE INTO Overhead_Master VALUES ('Bleach Wash', 25.0);     -- bleaching process
INSERT OR IGNORE INTO Overhead_Master VALUES ('Mercerizing', 22.0);     -- cotton strengthening
INSERT OR IGNORE INTO Overhead_Master VALUES ('Dyeing', 30.0);          -- general dyeing overhead
