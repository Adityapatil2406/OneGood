CREATE DATABASE IF NOT EXISTS onegood CHARACTER SET utf8mb4;
USE onegood;
CREATE TABLE IF NOT EXISTS entries (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  entry_date DATE NOT NULL UNIQUE,          -- one good thing per day
  note       VARCHAR(280) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
