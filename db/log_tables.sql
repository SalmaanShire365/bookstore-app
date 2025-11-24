-- SQLite schema for logs table
CREATE TABLE IF NOT EXISTS logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    function_name TEXT NOT NULL,
    status TEXT NOT NULL,
    execution_time REAL,
    error_message TEXT,
    details TEXT
);

-- Example queries to view logs
-- Get all logs
SELECT * FROM logs ORDER BY timestamp DESC;

-- Get logs for specific function
SELECT * FROM logs WHERE function_name = 'get_all_reviews' ORDER BY timestamp DESC;

-- Get error logs only
SELECT * FROM logs WHERE status = 'error' ORDER BY timestamp DESC;

-- Get performance statistics
SELECT 
    function_name,
    COUNT(*) as call_count,
    AVG(execution_time) as avg_time,
    MIN(execution_time) as min_time,
    MAX(execution_time) as max_time,
    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
FROM logs
WHERE execution_time IS NOT NULL
GROUP BY function_name
ORDER BY avg_time DESC;
