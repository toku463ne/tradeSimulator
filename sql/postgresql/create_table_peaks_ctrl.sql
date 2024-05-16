CREATE TABLE IF NOT EXISTS peaks_ctrl (
    "codename" VARCHAR(50),
    "tablename" VARCHAR(100),
    "startep" INT,
    "endep" INT,
    "startdt" TIMESTAMP,
    "enddt" TIMESTAMP,
    PRIMARY KEY ("codename", "tablename")
);