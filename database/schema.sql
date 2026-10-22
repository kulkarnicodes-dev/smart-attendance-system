-- OPTIONAL: tables are created automatically by the backend on first run.
-- Use this file only if you want to create them manually in MySQL.
CREATE DATABASE IF NOT EXISTS smart_attendance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_attendance;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(100) DEFAULT '',
  role VARCHAR(20) DEFAULT 'teacher'
);

CREATE TABLE IF NOT EXISTS students (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id VARCHAR(30) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  roll_no VARCHAR(30) NOT NULL UNIQUE,
  course VARCHAR(50) DEFAULT 'MCA',
  division VARCHAR(10) DEFAULT 'A',
  email VARCHAR(120) DEFAULT '',
  contact VARCHAR(20) DEFAULT '',
  consent TINYINT(1) DEFAULT 0,
  face_reference LONGTEXT,            -- JSON embeddings only, no photos
  face_count INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_pk INT NOT NULL,
  date DATE NOT NULL,
  time TIME,
  status VARCHAR(10) DEFAULT 'Present',
  confidence FLOAT DEFAULT 0,
  session VARCHAR(40) DEFAULT 'General',
  method VARCHAR(10) DEFAULT 'face',
  UNIQUE KEY uq_student_date_session (student_pk, date, session),
  INDEX (date),
  FOREIGN KEY (student_pk) REFERENCES students(id) ON DELETE CASCADE
);
