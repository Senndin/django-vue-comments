-- Database schema of the Comments SPA, written in MySQL dialect for MySQL Workbench (D5).
--
-- The application itself runs on PostgreSQL (assumption A21). This file describes the same
-- application tables in MySQL syntax so that the schema can be opened, reviewed and compared
-- with the ER diagram in MySQL Workbench.
--
-- How to open it in MySQL Workbench:
--   1. File → Import → Reverse Engineer MySQL Create Script…
--   2. Pick this file, tick "Place imported objects on a diagram", click Execute.
--   3. File → Save Model As… → docs/db/schema.mwb
--   4. File → Export → Export as PNG… → docs/db/schema.png
--
-- Only application tables are listed. Django's own service tables (django_migrations,
-- django_session, django_admin_log, auth_permission, auth_group…) and the CAPTCHA store
-- (captcha_captchastore) are created by framework migrations and carry no domain meaning.

CREATE SCHEMA IF NOT EXISTS `comments` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `comments`;


-- Site user (accounts.User). A custom model from the very first migration, so that it can be
-- extended later; `username` follows requirement R5: latin letters and digits only.
CREATE TABLE `accounts_user` (
  `id`           BIGINT       NOT NULL AUTO_INCREMENT,
  `password`     VARCHAR(128) NOT NULL,
  `last_login`   DATETIME(6)  NULL,
  `is_superuser` TINYINT(1)   NOT NULL DEFAULT 0,
  `username`     VARCHAR(50)  NOT NULL COMMENT 'R5/A7: ^[A-Za-z0-9]+$',
  `first_name`   VARCHAR(150) NOT NULL DEFAULT '',
  `last_name`    VARCHAR(150) NOT NULL DEFAULT '',
  `email`        VARCHAR(254) NOT NULL COMMENT 'Required: it is copied into the comment form (A1)',
  `is_staff`     TINYINT(1)   NOT NULL DEFAULT 0,
  `is_active`    TINYINT(1)   NOT NULL DEFAULT 1,
  `date_joined`  DATETIME(6)  NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `accounts_user_username_uniq` (`username`)
) ENGINE = InnoDB;


-- Comment or reply (comments.Comment).
--
-- The tree is stored with two self references:
--   * `parent_id` — the direct parent, drives indentation and ordering inside a thread;
--   * `root_id`   — the top level comment of the thread, so the whole thread of any depth
--                   is fetched with a single indexed query (`WHERE root_id = ?`).
-- Both are NULL for a top level comment.
CREATE TABLE `comments_comment` (
  `id`              BIGINT       NOT NULL AUTO_INCREMENT,
  `parent_id`       BIGINT       NULL COMMENT 'Direct parent, NULL for a top level comment (R10)',
  `root_id`         BIGINT       NULL COMMENT 'Top level comment of the thread (R10)',
  `user_id`         BIGINT       NULL COMMENT 'Set when the author was signed in (A1)',
  `user_name`       VARCHAR(50)  NOT NULL COMMENT 'R5: latin letters and digits only',
  `email`           VARCHAR(254) NOT NULL COMMENT 'R6',
  `home_page`       VARCHAR(200) NOT NULL DEFAULT '' COMMENT 'R7: http/https only',
  `text`            LONGTEXT     NOT NULL COMMENT 'Safe HTML built by the server sanitizer (A10)',
  `attachment`      VARCHAR(100) NOT NULL DEFAULT '' COMMENT 'Path under MEDIA_ROOT, UUID file name (R16)',
  `attachment_type` VARCHAR(5)   NOT NULL DEFAULT '' COMMENT 'image | text (A11)',
  `ip_address`      VARCHAR(39)  NULL COMMENT 'Client IP, X-Real-IP from nginx (R2, A2)',
  `user_agent`      VARCHAR(255) NOT NULL DEFAULT '' COMMENT 'Client user agent (R2, A2)',
  `created_at`      DATETIME(6)  NOT NULL,
  PRIMARY KEY (`id`),

  -- Sorting of the top level table: user name, e-mail, date (R11, R14).
  INDEX `comments_comment_created_at_idx` (`created_at`),
  INDEX `comments_comment_user_name_idx` (`user_name`),
  INDEX `comments_comment_email_idx` (`email`),
  -- Indexes of the foreign keys are created by the ORM automatically.
  INDEX `comments_comment_parent_id_idx` (`parent_id`),
  INDEX `comments_comment_root_id_idx` (`root_id`),
  INDEX `comments_comment_user_id_idx` (`user_id`),

  CONSTRAINT `comments_comment_parent_fk`
    FOREIGN KEY (`parent_id`) REFERENCES `comments_comment` (`id`) ON DELETE CASCADE,
  CONSTRAINT `comments_comment_root_fk`
    FOREIGN KEY (`root_id`) REFERENCES `comments_comment` (`id`) ON DELETE CASCADE,
  -- Deleting an account keeps the comment: the text stays, the author becomes anonymous.
  CONSTRAINT `comments_comment_user_fk`
    FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`) ON DELETE SET NULL,

  -- An attachment and its type are filled in together or not at all (A11).
  CONSTRAINT `attachment_and_type_are_set_together` CHECK (
    (`attachment` = '' AND `attachment_type` = '')
    OR (`attachment` <> '' AND `attachment_type` <> '')
  )
) ENGINE = InnoDB;
