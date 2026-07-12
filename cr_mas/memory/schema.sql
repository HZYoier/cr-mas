-- 审查档案主表：一次审查一条记录
CREATE TABLE IF NOT EXISTS review_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    commit_hash     TEXT,
    module          TEXT NOT NULL DEFAULT '',
    changed_files   TEXT NOT NULL,          -- JSON 数组
    total_issues    INTEGER DEFAULT 0,
    critical_count  INTEGER DEFAULT 0,
    verdict_json    TEXT,                    -- 最终裁决 JSON
    react_trace     TEXT,                    -- 推理链 JSON
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP     --时间戳
);

-- 用户反馈流水表：每条建议的采纳/忽略记录
CREATE TABLE IF NOT EXISTS user_feedback (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id       INTEGER NOT NULL,
    module          TEXT NOT NULL DEFAULT '',
    file_path       TEXT NOT NULL,
    line_number     INTEGER,
    agent_source    TEXT NOT NULL,           -- style/security/performance/readability/extension
    suggestion_type TEXT NOT NULL,
    suggestion_summary TEXT,
    user_action     TEXT,                    -- accept / ignore / modified
    was_critical    INTEGER DEFAULT 0,       -- 是否安全红线
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES review_records(id) ON DELETE CASCADE
);

-- 按模块+Agent 统计采纳率
CREATE VIEW IF NOT EXISTS agent_accuracy AS
SELECT
    module,
    agent_source,
    COUNT(*) AS total,
    SUM(CASE WHEN user_action = 'accept' THEN 1 ELSE 0 END) AS accepted,
    ROUND(SUM(CASE WHEN user_action = 'accept' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS rate
FROM user_feedback
GROUP BY module, agent_source;

-- flake8 翻译
CREATE TABLE IF NOT EXISTS style_translations (
    en TEXT PRIMARY KEY,
    zh TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

