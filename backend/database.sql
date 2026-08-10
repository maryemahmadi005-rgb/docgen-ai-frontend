-- =========================================================
-- SCHEMA FINAL DE BASE DE DONNÉES — MySQL Workbench Compatible
-- =========================================================

CREATE DATABASE IF NOT EXISTS readme_sync_db;
USE readme_sync_db;

-- 1. users
CREATE TABLE users (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NULL,
    github_username VARCHAR(255) NULL,
    github_token TEXT NULL, -- encrypted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. repositories
CREATE TABLE repositories (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    github_url VARCHAR(500) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    default_branch VARCHAR(255) DEFAULT 'main',
    tracked_branch VARCHAR(255) NULL,
    local_clone_path VARCHAR(500) NULL,
    last_synced_commit_sha VARCHAR(64) NULL,
    sync_mode ENUM('manual','automatic') DEFAULT 'manual',
    sync_mode_updated_at TIMESTAMP NULL,
    sync_method ENUM('webhook','polling') DEFAULT 'webhook',
    webhook_id VARCHAR(255) NULL,
    webhook_secret TEXT NULL, -- encrypted
    current_readme_version_id CHAR(36) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_repo_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uq_repo_user_fullname UNIQUE (user_id, full_name)
);

-- 3. analyses
CREATE TABLE analyses (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    repository_id CHAR(36) NOT NULL,
    languages JSON NULL,
    frameworks JSON NULL,
    dependencies JSON NULL,
    file_structure JSON NULL,
    important_files JSON NULL,
    install_scripts JSON NULL,
    run_scripts JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_analyses_repo FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);

-- 4. generated_readmes
CREATE TABLE generated_readmes (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    repository_id CHAR(36) NOT NULL UNIQUE,
    sections_json JSON NULL,
    content_md LONGTEXT NULL,
    current_version_id CHAR(36) NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_genreadme_repo FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);

-- 5. readme_versions
CREATE TABLE readme_versions (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    readme_id CHAR(36) NOT NULL,
    version_number INT NOT NULL,
    sections_json JSON NULL,
    content_md LONGTEXT NULL,
    triggered_by ENUM('initial_generation','manual_edit','sync_auto','sync_manual_approved') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_versions_readme FOREIGN KEY (readme_id) REFERENCES generated_readmes(id) ON DELETE CASCADE
);

-- Add deferred FKs now that readme_versions exists
ALTER TABLE repositories
    ADD CONSTRAINT fk_repo_currentversion FOREIGN KEY (current_readme_version_id) REFERENCES readme_versions(id) ON DELETE SET NULL;

ALTER TABLE generated_readmes
    ADD CONSTRAINT fk_genreadme_currentversion FOREIGN KEY (current_version_id) REFERENCES readme_versions(id) ON DELETE SET NULL;

-- 6. commits
CREATE TABLE commits (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    repository_id CHAR(36) NOT NULL,
    sha VARCHAR(64) NOT NULL,
    parent_sha VARCHAR(64) NULL,
    author_name VARCHAR(255) NULL,
    author_email VARCHAR(255) NULL,
    message TEXT NULL,
    is_bot_commit BOOLEAN DEFAULT FALSE,
    processed BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_commits_repo FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE,
    CONSTRAINT uq_commit_repo_sha UNIQUE (repository_id, sha)
);

-- 7. file_changes
CREATE TABLE file_changes (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    commit_id CHAR(36) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    change_type ENUM('added','modified','deleted','renamed') NOT NULL,
    diff_summary LONGTEXT NULL,
    CONSTRAINT fk_filechanges_commit FOREIGN KEY (commit_id) REFERENCES commits(id) ON DELETE CASCADE
);

-- 8. detected_changes
CREATE TABLE detected_changes (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    commit_id CHAR(36) NOT NULL,
    impact_category ENUM('feature','dependency','structure','config','license','none') NULL,
    affected_sections JSON NULL,
    confidence_score FLOAT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_detected_commit FOREIGN KEY (commit_id) REFERENCES commits(id) ON DELETE CASCADE
);

-- 9. pending_updates
CREATE TABLE pending_updates (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    repository_id CHAR(36) NOT NULL,
    commit_id CHAR(36) NOT NULL,
    detected_change_id CHAR(36) NOT NULL,
    base_readme_version_id CHAR(36) NOT NULL,
    sections_diff JSON NULL,
    proposed_content_md LONGTEXT NULL,
    proposed_sections_json JSON NULL,
    status ENUM('pending','approved','rejected','stale') DEFAULT 'pending',
    resolved_by CHAR(36) NULL,
    rejection_reason TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    CONSTRAINT fk_pending_repo FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE,
    CONSTRAINT fk_pending_commit FOREIGN KEY (commit_id) REFERENCES commits(id) ON DELETE CASCADE,
    CONSTRAINT fk_pending_detected FOREIGN KEY (detected_change_id) REFERENCES detected_changes(id) ON DELETE CASCADE,
    CONSTRAINT fk_pending_baseversion FOREIGN KEY (base_readme_version_id) REFERENCES readme_versions(id) ON DELETE RESTRICT,
    CONSTRAINT fk_pending_resolvedby FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 10. webhook_events
CREATE TABLE webhook_events (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    repository_id CHAR(36) NOT NULL,
    event_type VARCHAR(100) NULL,
    delivery_id VARCHAR(255) UNIQUE NOT NULL,
    signature_valid BOOLEAN NULL,
    payload_summary JSON NULL,
    processed BOOLEAN DEFAULT FALSE,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_webhook_repo FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);