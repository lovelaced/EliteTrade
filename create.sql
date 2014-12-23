CREATE TABLE IF NOT EXISTS systems (
	name VARCHAR(255) NOT NULL,
	xcoord REAL NOT NULL,
	ycoord REAL NOT NULL,
	zcoord REAL NOT NULL,

	PRIMARY KEY (name)
);

CREATE TABLE IF NOT EXISTS distances (
	system_1 VARCHAR(255) NOT NULL,
	system_2 VARCHAR(255) NOT NULL,
	distance REAL NOT NULL,

	PRIMARY KEY (system_1, system_2),
	FOREIGN KEY (system_1) REFERENCES systems (name),
	FOREIGN KEY (system_2) REFERENCES systems (name)
);
