-- Database: p17_handshake (PAIR=17, PORT_BASE=9170, prefix=p17)

CREATE DATABASE IF NOT EXISTS p17_handshake
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE p17_handshake;

-- ---------------------------------------------------------------------
-- accounts: single source of truth for login (email, password, role).
-- Students and companies each hold a 1:1 profile row keyed on account_id,
-- so /auth/login only ever queries one table before issuing a JWT.
-- ---------------------------------------------------------------------
CREATE TABLE accounts (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  email         VARCHAR(190) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role          ENUM('student', 'company') NOT NULL,
  created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- students
-- ---------------------------------------------------------------------
CREATE TABLE students (
  account_id        INT PRIMARY KEY,
  name              VARCHAR(150) NOT NULL,
  college_name      VARCHAR(190) NOT NULL,
  date_of_birth     DATE,
  city              VARCHAR(100),
  state             VARCHAR(100),
  country           VARCHAR(100),
  career_objective  TEXT,
  degree            VARCHAR(100),
  major             VARCHAR(100),
  graduation_year   SMALLINT,
  cgpa              DECIMAL(3,2),
  experience        TEXT,
  phone             VARCHAR(30),
  skills            TEXT,
  profile_picture_path VARCHAR(255),
  updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
  INDEX idx_students_name (name),
  INDEX idx_students_college (college_name),
  INDEX idx_students_major (major)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- companies
-- ---------------------------------------------------------------------
CREATE TABLE companies (
  account_id        INT PRIMARY KEY,
  company_name      VARCHAR(190) NOT NULL,
  location          VARCHAR(190) NOT NULL,
  description       TEXT,
  contact_info      VARCHAR(255),
  profile_picture_path VARCHAR(255),
  updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
  INDEX idx_companies_name (company_name)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- jobs
-- ---------------------------------------------------------------------
CREATE TABLE jobs (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  company_id      INT NOT NULL,
  title           VARCHAR(190) NOT NULL,
  description     TEXT,
  category        ENUM('full_time', 'part_time', 'on_campus', 'internship') NOT NULL,
  city            VARCHAR(100) NOT NULL,
  location        VARCHAR(190),
  is_remote       BOOLEAN NOT NULL DEFAULT FALSE,
  salary          DECIMAL(10,2),
  skills_required TEXT,
  posting_date    DATE NOT NULL,
  deadline        DATE NOT NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (company_id) REFERENCES companies(account_id) ON DELETE CASCADE,
  INDEX idx_jobs_title (title),
  INDEX idx_jobs_city (city),
  INDEX idx_jobs_category (category),
  INDEX idx_jobs_deadline (deadline),
  FULLTEXT INDEX ftx_jobs_search (title, description, skills_required)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- applications
-- ---------------------------------------------------------------------
CREATE TABLE applications (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  student_id   INT NOT NULL,
  job_id       INT NOT NULL,
  resume_path  VARCHAR(255) NOT NULL,
  status       ENUM('Pending', 'Reviewed', 'Declined') NOT NULL DEFAULT 'Pending',
  applied_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (student_id) REFERENCES students(account_id) ON DELETE CASCADE,
  FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
  UNIQUE KEY uq_student_job (student_id, job_id),
  INDEX idx_applications_status (status)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- events
-- ---------------------------------------------------------------------
CREATE TABLE events (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  company_id   INT NOT NULL,
  name         VARCHAR(190) NOT NULL,
  description  TEXT,
  event_date   DATE NOT NULL,
  event_time   TIME,
  location     VARCHAR(190),
  eligibility  VARCHAR(255),
  created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (company_id) REFERENCES companies(account_id) ON DELETE CASCADE,
  INDEX idx_events_date (event_date),
  INDEX idx_events_name (name)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- registrations
-- ---------------------------------------------------------------------
CREATE TABLE registrations (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  student_id     INT NOT NULL,
  event_id       INT NOT NULL,
  registered_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (student_id) REFERENCES students(account_id) ON DELETE CASCADE,
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  UNIQUE KEY uq_student_event (student_id, event_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- saved_items: backs the save_job_or_event assistant tool and the
-- student "Saved" views for jobs/events.
-- ---------------------------------------------------------------------
CREATE TABLE saved_items (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  student_id  INT NOT NULL,
  item_type   ENUM('job', 'event') NOT NULL,
  item_id     INT NOT NULL,
  saved_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (student_id) REFERENCES students(account_id) ON DELETE CASCADE,
  UNIQUE KEY uq_student_item (student_id, item_type, item_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- preferences: one row per student, read by get_student_preferences
-- and used to refine search_jobs / search_events tool calls.
-- ---------------------------------------------------------------------
CREATE TABLE preferences (
  student_id            INT PRIMARY KEY,
  preferred_categories   VARCHAR(255),
  preferred_cities       VARCHAR(255),
  min_salary             DECIMAL(10,2),
  preferred_skills       TEXT,
  remote_ok              BOOLEAN NOT NULL DEFAULT FALSE,
  updated_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (student_id) REFERENCES students(account_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- company_members: who can act for a company, and with which role.
-- The company's original signup account is its 'owner' member.
-- ---------------------------------------------------------------------
CREATE TABLE company_members (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  company_id      INT NOT NULL,
  account_id      INT NOT NULL UNIQUE,
  name            VARCHAR(150) NOT NULL,
  role            ENUM('owner', 'admin', 'recruiter', 'hiring_manager', 'viewer') NOT NULL,
  last_active_at  TIMESTAMP NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (company_id) REFERENCES companies(account_id) ON DELETE CASCADE,
  FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
  INDEX idx_members_company (company_id)
) ENGINE=InnoDB;
-- ---------------------------------------------------------------------
-- team_invitations: pending invites. Only a SHA-256 hash of the invite
-- token is stored, so a database leak doesn't expose usable links.
-- ---------------------------------------------------------------------
CREATE TABLE team_invitations (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  company_id   INT NOT NULL,
  email        VARCHAR(190) NOT NULL,
  name         VARCHAR(150) NOT NULL,
  role         ENUM('admin', 'recruiter', 'hiring_manager', 'viewer') NOT NULL,
  token_hash   CHAR(64) NOT NULL UNIQUE,
  invited_by   INT NULL,
  expires_at   TIMESTAMP NOT NULL,
  created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (company_id) REFERENCES companies(account_id) ON DELETE CASCADE,
  FOREIGN KEY (invited_by) REFERENCES accounts(id) ON DELETE SET NULL,
  UNIQUE KEY uq_invite_company_email (company_id, email)
) ENGINE=InnoDB;
-- ---------------------------------------------------------------------
-- conversations / messages: one thread per (company, student) pair.
-- Messages may reference a job or event ("invite to apply / to event").
-- ---------------------------------------------------------------------
CREATE TABLE conversations (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  company_id       INT NOT NULL,
  student_id       INT NOT NULL,
  created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_message_at  TIMESTAMP NULL,
  FOREIGN KEY (company_id) REFERENCES companies(account_id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES students(account_id) ON DELETE CASCADE,
  UNIQUE KEY uq_conversation_pair (company_id, student_id),
  INDEX idx_conversations_recent (company_id, last_message_at)
) ENGINE=InnoDB;
