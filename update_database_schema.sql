-- =====================================================
-- 智能问卷自动填写系统 - 数据库表结构更新脚本
-- 用途: 为现有表添加缺失的字段，确保与代码兼容
-- =====================================================

USE wenjuan;

-- 检查并添加questionnaire_knowledge表的缺失字段
-- 添加question_text字段（如果不存在）
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE TABLE_SCHEMA = 'wenjuan' 
     AND TABLE_NAME = 'questionnaire_knowledge' 
     AND COLUMN_NAME = 'question_text') = 0,
    'ALTER TABLE questionnaire_knowledge ADD COLUMN question_text TEXT COMMENT "问题文本"',
    'SELECT "question_text字段已存在" as message'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加persona_name字段（如果不存在）
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE TABLE_SCHEMA = 'wenjuan' 
     AND TABLE_NAME = 'questionnaire_knowledge' 
     AND COLUMN_NAME = 'persona_name') = 0,
    'ALTER TABLE questionnaire_knowledge ADD COLUMN persona_name VARCHAR(100) COMMENT "数字人姓名"',
    'SELECT "persona_name字段已存在" as message'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加strategy_used字段（如果不存在）
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE TABLE_SCHEMA = 'wenjuan' 
     AND TABLE_NAME = 'questionnaire_knowledge' 
     AND COLUMN_NAME = 'strategy_used') = 0,
    'ALTER TABLE questionnaire_knowledge ADD COLUMN strategy_used VARCHAR(50) DEFAULT "conservative" COMMENT "使用的策略"',
    'SELECT "strategy_used字段已存在" as message'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加time_taken字段（如果不存在）
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE TABLE_SCHEMA = 'wenjuan' 
     AND TABLE_NAME = 'questionnaire_knowledge' 
     AND COLUMN_NAME = 'time_taken') = 0,
    'ALTER TABLE questionnaire_knowledge ADD COLUMN time_taken FLOAT DEFAULT 0.0 COMMENT "耗时(秒)"',
    'SELECT "time_taken字段已存在" as message'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加answer_records表的缺失字段
-- 添加question_text字段（如果不存在）
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE TABLE_SCHEMA = 'wenjuan' 
     AND TABLE_NAME = 'answer_records' 
     AND COLUMN_NAME = 'question_text') = 0,
    'ALTER TABLE answer_records ADD COLUMN question_text TEXT COMMENT "问题文本"',
    'SELECT "answer_records.question_text字段已存在" as message'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 创建questionnaire_sessions表（如果不存在）
CREATE TABLE IF NOT EXISTS questionnaire_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    session_id VARCHAR(100) NOT NULL COMMENT '会话ID',
    questionnaire_url VARCHAR(500) NOT NULL COMMENT '问卷URL',
    persona_id INT NOT NULL COMMENT '数字人ID',
    persona_name VARCHAR(100) COMMENT '数字人姓名',
    total_questions INT DEFAULT 0 COMMENT '总问题数',
    successful_answers INT DEFAULT 0 COMMENT '成功回答数',
    success_rate DECIMAL(5,2) DEFAULT 0.00 COMMENT '成功率(%)',
    total_time FLOAT DEFAULT 0.0 COMMENT '总耗时(秒)',
    session_type VARCHAR(50) DEFAULT 'unknown' COMMENT '会话类型',
    strategy_used VARCHAR(50) DEFAULT 'conservative' COMMENT '使用的策略',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    UNIQUE KEY unique_session (session_id, persona_id),
    INDEX idx_session_id (session_id),
    INDEX idx_questionnaire_url (questionnaire_url),
    INDEX idx_persona_id (persona_id),
    INDEX idx_session_type (session_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='问卷会话记录表';

-- 创建detailed_answering_records表（如果不存在）
CREATE TABLE IF NOT EXISTS detailed_answering_records (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    session_id VARCHAR(100) NOT NULL COMMENT '会话ID',
    task_id VARCHAR(100) NOT NULL COMMENT '任务ID',
    persona_id INT NOT NULL COMMENT '数字人ID',
    questionnaire_url VARCHAR(500) NOT NULL COMMENT '问卷URL',
    question_number INT NOT NULL COMMENT '问题编号',
    question_text TEXT NOT NULL COMMENT '问题文本',
    question_type VARCHAR(50) NOT NULL COMMENT '问题类型',
    available_options JSON COMMENT '可用选项(JSON格式)',
    selected_answer TEXT NOT NULL COMMENT '选择的答案',
    answer_strategy VARCHAR(50) COMMENT '答题策略',
    success BOOLEAN DEFAULT FALSE COMMENT '是否成功',
    error_message TEXT COMMENT '错误信息',
    time_taken FLOAT DEFAULT 0.0 COMMENT '耗时(秒)',
    screenshot_before LONGBLOB COMMENT '操作前截图',
    screenshot_after LONGBLOB COMMENT '操作后截图',
    page_content_before TEXT COMMENT '操作前页面内容',
    page_content_after TEXT COMMENT '操作后页面内容',
    browser_info JSON COMMENT '浏览器信息(JSON格式)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_session_task (session_id, task_id),
    INDEX idx_persona (persona_id),
    INDEX idx_question (question_number),
    INDEX idx_success (success)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='详细答题记录表';

-- 创建page_analysis_records表（如果不存在）
CREATE TABLE IF NOT EXISTS page_analysis_records (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    session_id VARCHAR(100) NOT NULL COMMENT '会话ID',
    task_id VARCHAR(100) NOT NULL COMMENT '任务ID',
    questionnaire_url VARCHAR(500) NOT NULL COMMENT '问卷URL',
    page_number INT DEFAULT 1 COMMENT '页面编号',
    page_title VARCHAR(200) COMMENT '页面标题',
    total_questions INT DEFAULT 0 COMMENT '总问题数',
    questions_data JSON COMMENT '问题数据(JSON格式)',
    page_structure JSON COMMENT '页面结构(JSON格式)',
    navigation_elements JSON COMMENT '导航元素(JSON格式)',
    screenshot LONGBLOB COMMENT '页面截图',
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '分析时间',
    
    INDEX idx_session_page (session_id, page_number),
    INDEX idx_task_id (task_id),
    INDEX idx_questionnaire_url (questionnaire_url)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='页面分析记录表';

-- 修复experience_type字段的ENUM值（如果表已存在）
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE TABLE_SCHEMA = 'wenjuan' 
     AND TABLE_NAME = 'questionnaire_knowledge' 
     AND COLUMN_NAME = 'experience_type') > 0,
    'ALTER TABLE questionnaire_knowledge MODIFY COLUMN experience_type ENUM("success", "failure", "detailed_step_experience", "enhanced_scout_experience", "step_experience") COMMENT "经验类型"',
    'SELECT "experience_type字段不存在，跳过修改" as message'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 重新创建视图（确保字段存在后）
DROP VIEW IF EXISTS scout_success_experiences;
CREATE VIEW scout_success_experiences AS
SELECT 
    qk.questionnaire_url,
    COALESCE(qk.question_text, qk.question_content) as question_text,
    qk.answer_choice,
    qk.experience_description,
    qk.persona_name,
    qk.strategy_used,
    qk.created_at,
    qs.success_rate
FROM questionnaire_knowledge qk
LEFT JOIN questionnaire_sessions qs ON qk.session_id = qs.session_id AND qk.persona_id = qs.persona_id
WHERE qk.persona_role = 'scout' 
AND (qk.experience_type = 'success' OR qk.success = 1)
ORDER BY qk.questionnaire_url, qk.created_at DESC;

DROP VIEW IF EXISTS questionnaire_completion_stats;
CREATE VIEW questionnaire_completion_stats AS
SELECT 
    questionnaire_url,
    COUNT(DISTINCT session_id) as total_sessions,
    COUNT(DISTINCT CASE WHEN persona_role = 'scout' THEN persona_id END) as scout_count,
    COUNT(DISTINCT CASE WHEN persona_role = 'target' THEN persona_id END) as target_count,
    AVG(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100 as overall_success_rate,
    COUNT(CASE WHEN experience_type = 'success' THEN 1 END) as success_experiences,
    MAX(created_at) as last_attempt
FROM questionnaire_knowledge
WHERE questionnaire_url IS NOT NULL
GROUP BY questionnaire_url
ORDER BY last_attempt DESC;

-- 显示更新完成信息
SELECT '数据库表结构更新完成！' as message;
SELECT 'questionnaire_knowledge表字段:' as info;
DESCRIBE questionnaire_knowledge; 