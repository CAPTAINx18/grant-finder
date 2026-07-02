# Database Schema: GrantFinder Platform

This document describes the relational database schema of the GrantFinder platform, mapped directly from the Python SQLAlchemy 2.0 ORM models. All tables use `UUID` for primary keys and contain automatic UTC timezone-aware auditing timestamps.

---

## Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    users {
        uuid id PK
        varchar email UK "Index"
        varchar hashed_password
        boolean is_active
        boolean is_admin
        timestamptz created_at
        timestamptz updated_at
    }
    organizations {
        uuid id PK
        varchar name "Index"
        varchar website
        timestamptz created_at
        timestamptz updated_at
    }
    grant_providers {
        uuid id PK
        varchar name UK "Index"
        varchar website
        varchar provider_type
        timestamptz created_at
        timestamptz updated_at
    }
    grant_source_registry {
        uuid id PK
        varchar name UK "Index"
        varchar url
        varchar update_method
        varchar cron_schedule
        boolean is_active
        timestamptz last_run_at
        varchar last_run_status
        varchar last_run_error
        json metadata_json
        timestamptz created_at
        timestamptz updated_at
    }
    grants {
        uuid id PK
        uuid provider_id FK
        varchar name "Index"
        text description
        numeric funding_amount_min
        numeric funding_amount_max
        varchar currency
        timestamptz deadline
        varchar country_eligibility
        varchar official_source_link
        varchar application_link
        varchar document_url
        integer click_count
        integer bookmark_count
        tsvector search_vector "Index"
        vector embedding "HNSW Index"
        timestamptz created_at
        timestamptz updated_at
    }
    eligibility_rules {
        uuid id PK
        uuid grant_id FK
        varchar applicant_type "Index"
        varchar sector "Index"
        varchar project_stage "Index"
        numeric min_funding_required
        timestamptz created_at
        timestamptz updated_at
    }
    bookmarks {
        uuid id PK
        uuid user_id FK
        uuid grant_id FK
        varchar collection_name "Index"
        text notes
        varchar application_status
        timestamptz created_at
        timestamptz updated_at
    }
    alerts {
        uuid id PK
        uuid user_id FK
        varchar alert_type
        json filters
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }
    search_history {
        uuid id PK
        uuid user_id FK
        varchar query_text
        json filters
        integer results_count
        timestamptz created_at
        timestamptz updated_at
    }
    sessions {
        uuid id PK
        uuid user_id FK
        varchar token UK "Index"
        timestamptz expires_at
        timestamptz created_at
        timestamptz updated_at
    }
    audit_logs {
        uuid id PK
        uuid user_id FK
        varchar action "Index"
        varchar table_name "Index"
        uuid record_id
        json details
        timestamptz created_at
        timestamptz updated_at
    }

    users ||--o{ bookmarks : "creates"
    users ||--o{ alerts : "subscribes"
    users ||--o{ sessions : "establishes"
    users ||--o{ audit_logs : "triggers"
    users ||--o{ search_history : "performs"

    grant_providers ||--o{ grants : "publishes"
    grants ||--o{ eligibility_rules : "specifies"
    grants ||--o{ bookmarks : "is_saved"
```

---

## Table Columns and Constraints Specification

### 1. `users`
Tracks authenticated user details.
- **Indexes**:
  - `ix_users_id`: Primary key index.
  - `ix_users_email`: Unique index on email address.

### 2. `organizations`
General registry for companies, startups, and institutions using the platform.
- **Indexes**:
  - `ix_organizations_name`: Index on name for fast lookups.

### 3. `grant_providers`
Companies, government agencies, and foundations that issue grants.
- **Indexes**:
  - `ix_grant_providers_name`: Unique index on publisher name.

### 4. `grant_source_registry`
Pipeline manager for configuring RSS feeds, site scrapers, and external APIs.
- **Indexes**:
  - `ix_grant_source_registry_name`: Unique index on registry source name.

### 5. `grants`
Core grant record details.
- **Indexes**:
  - `ix_grants_name`: Index on grant name.
  - `ix_grants_provider_id`: Index on foreign key relationship to provider.
  - `grants_search_vector_idx`: PostgreSQL `GIN` index on `search_vector` column to support Full-Text keyword queries.
  - `grants_embedding_cosine_idx`: `HNSW` vector index on the 1536-dimensional `embedding` column using `vector_cosine_ops` operator class for cosine similarity semantic searches.

### 6. `eligibility_rules`
Scraped and normalized constraints for matching engines.
- **Indexes**:
  - `ix_eligibility_rules_grant_id`: Index on foreign key.

### 7. `bookmarks`
User saved grants folder.
- **Indexes**:
  - `ix_bookmarks_user_id`: Index on foreign key.
  - `ix_bookmarks_grant_id`: Index on foreign key.

### 8. `alerts`
Configured triggers for alerts and search preferences.
- **Indexes**:
  - `ix_alerts_user_id`: Index on foreign key.

### 9. `search_history`
Search logs.
- **Indexes**:
  - `ix_search_history_user_id`: Index on foreign key.

### 10. `sessions`
Secure login user tokens.
- **Indexes**:
  - `ix_sessions_token`: Unique index on active login JWT tokens.

### 11. `audit_logs`
System change trails.
- **Indexes**:
  - `ix_audit_logs_action`: Index on action column.
  - `ix_audit_logs_table_name`: Index on changed database table name.
