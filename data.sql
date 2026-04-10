PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS viewer_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visited_at TEXT NOT NULL,
    page TEXT NOT NULL DEFAULT '/portfolio',
    ip_address TEXT,
    user_agent TEXT,
    referrer TEXT,
    language TEXT,
    platform TEXT,
    timezone TEXT,
    screen_width INTEGER,
    screen_height INTEGER
);

CREATE INDEX IF NOT EXISTS idx_viewer_details_visited_at ON viewer_details (visited_at DESC);
CREATE INDEX IF NOT EXISTS idx_viewer_details_page ON viewer_details (page);
CREATE INDEX IF NOT EXISTS idx_viewer_details_ip ON viewer_details (ip_address);

CREATE VIEW IF NOT EXISTS viewer_daily_summary AS
SELECT
    substr(visited_at, 1, 10) AS visit_date,
    COUNT(*) AS total_views,
    COUNT(DISTINCT ip_address) AS unique_visitors
FROM viewer_details
GROUP BY substr(visited_at, 1, 10)
ORDER BY visit_date DESC;

CREATE TABLE IF NOT EXISTS contact_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submitted_at TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,               -- This is the new column!
    message TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    status TEXT NOT NULL DEFAULT 'received'
);

CREATE INDEX IF NOT EXISTS idx_contact_messages_submitted_at ON contact_messages (submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_contact_messages_email ON contact_messages (email);