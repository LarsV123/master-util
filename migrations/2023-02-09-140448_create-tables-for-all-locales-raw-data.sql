-- Create tables for all locales (raw data)

BEGIN;


-- sql
CREATE TABLE country_list_en_US (
    id VARCHAR(64) NOT NULL,
    value VARCHAR(64) NOT NULL,
    PRIMARY KEY(id)
    ) 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_0900_ai_ci;

-- sql
CREATE TABLE country_list_th_TH (
    id VARCHAR(64) NOT NULL,
    value VARCHAR(64) NOT NULL,
    PRIMARY KEY(id)
    ) 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_0900_ai_ci;

-- sql
CREATE TABLE country_list_zh_Hans (
    id VARCHAR(64) NOT NULL,
    value VARCHAR(64) NOT NULL,
    PRIMARY KEY(id)
    ) 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_0900_ai_ci;

-- sql
CREATE TABLE country_list_uk_UA (
    id VARCHAR(64) NOT NULL,
    value VARCHAR(64) NOT NULL,
    PRIMARY KEY(id)
    ) 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_0900_ai_ci;

-- sql
CREATE TABLE country_list_fr_FR (
    id VARCHAR(64) NOT NULL,
    value VARCHAR(64) NOT NULL,
    PRIMARY KEY(id)
    ) 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_0900_ai_ci;

-- sql
CREATE TABLE country_list_no_NO (
    id VARCHAR(64) NOT NULL,
    value VARCHAR(64) NOT NULL,
    PRIMARY KEY(id)
    ) 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_0900_ai_ci;

-- sql
CREATE TABLE country_list_ja_JP (
    id VARCHAR(64) NOT NULL,
    value VARCHAR(64) NOT NULL,
    PRIMARY KEY(id)
    ) 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_0900_ai_ci;


COMMIT;