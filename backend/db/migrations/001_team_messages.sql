-- Adds company teams (members, invitations) and company <-> student messaging.
-- Safe to run more than once. Also appended to schema.sql for fresh installs.
USE p17_handshake;

-- ---------------------------------------------------------------------
-- company_members: who can act for a company, and with which role.
-- The company's original signup account is its 'owner' member.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS company_members (
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
CREATE TABLE IF NOT EXISTS team_invitations (
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
CREATE TABLE IF NOT EXISTS conversations (
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

CREATE TABLE IF NOT EXISTS messages (
  id                 INT AUTO_INCREMENT PRIMARY KEY,
  conversation_id    INT NOT NULL,
  sender_account_id  INT NULL,
  body               TEXT NOT NULL,
  job_id             INT NULL,
  event_id           INT NULL,
  created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  read_at            TIMESTAMP NULL,
  FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
  FOREIGN KEY (sender_account_id) REFERENCES accounts(id) ON DELETE SET NULL,
  FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL,
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE SET NULL,
  INDEX idx_messages_conversation (conversation_id, created_at)
) ENGINE=InnoDB;

-- Every existing company gets its signup account as owner.
INSERT INTO company_members (company_id, account_id, name, role)
SELECT c.account_id, c.account_id, c.company_name, 'owner'
FROM companies c
WHERE NOT EXISTS (SELECT 1 FROM company_members m WHERE m.account_id = c.account_id);
