-- =====================================================
-- 智能问卷自动填写系统 - 数据库表结构
-- 创建时间: 2025-05-29
-- 说明: 包含问卷会话、知识库、答题记录等核心表
-- =====================================================

-- 使用数据库
USE wenjuan;

-- =====================================================
-- 1. 问卷会话表 (questionnaire_sessions)
-- 用途: 记录每个数字人的问卷填写会话信息
-- =====================================================
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
    session_type VARCHAR(50) DEFAULT 'unknown' COMMENT '会话类型(scout/target/enhanced_browser_automation等)',
    strategy_used VARCHAR(50) DEFAULT 'conservative' COMMENT '使用的策略(conservative/aggressive/enhanced)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 索引
    UNIQUE KEY unique_session (session_id, persona_id) COMMENT '会话和数字人唯一约束',
    INDEX idx_session_id (session_id) COMMENT '会话ID索引',
    INDEX idx_questionnaire_url (questionnaire_url) COMMENT '问卷URL索引',
    INDEX idx_persona_id (persona_id) COMMENT '数字人ID索引',
    INDEX idx_session_type (session_type) COMMENT '会话类型索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='问卷会话记录表';

-- =====================================================
-- 2. 问卷知识库表 (questionnaire_knowledge)
-- 用途: 存储敢死队的答题经验和成功模式，供大部队学习
-- =====================================================
CREATE TABLE IF NOT EXISTS questionnaire_knowledge (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    session_id VARCHAR(100) NOT NULL COMMENT '会话ID',
    questionnaire_url VARCHAR(500) NOT NULL COMMENT '问卷URL',
    question_content TEXT COMMENT '问题内容',
    question_text TEXT COMMENT '问题文本',
    question_type VARCHAR(50) COMMENT '问题类型(single_choice/multiple_choice/text_input等)',
    question_number INT COMMENT '问题编号',
    answer_choice TEXT COMMENT '选择的答案',
    persona_id INT COMMENT '数字人ID',
    persona_name VARCHAR(100) COMMENT '数字人姓名',
    persona_role ENUM('scout', 'target') COMMENT '数字人角色(scout=敢死队, target=大部队)',
    success BOOLEAN COMMENT '是否成功',
    experience_type ENUM('success', 'failure', 'detailed_step_experience', 'enhanced_scout_experience', 'step_experience') COMMENT '经验类型',
    experience_description TEXT COMMENT '经验描述',
    strategy_used VARCHAR(50) DEFAULT 'conservative' COMMENT '使用的策略',
    time_taken FLOAT DEFAULT 0.0 COMMENT '耗时(秒)',
    page_screenshot LONGBLOB COMMENT '页面截图',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 索引
    INDEX idx_session_id (session_id) COMMENT '会话ID索引',
    INDEX idx_questionnaire_url (questionnaire_url) COMMENT '问卷URL索引',
    INDEX idx_persona_id (persona_id) COMMENT '数字人ID索引',
    INDEX idx_success_type (success, experience_type) COMMENT '成功类型复合索引',
    INDEX idx_persona_role (persona_role) COMMENT '角色索引',
    INDEX idx_question_number (question_number) COMMENT '问题编号索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='问卷知识库表-存储答题经验';

-- =====================================================
-- 3. 答题记录表 (answer_records)
-- 用途: 详细记录每个问题的答题过程和结果
-- =====================================================
CREATE TABLE IF NOT EXISTS answer_records (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    session_id VARCHAR(100) NOT NULL COMMENT '会话ID',
    task_id VARCHAR(100) NOT NULL COMMENT '任务ID',
    questionnaire_url VARCHAR(500) NOT NULL COMMENT '问卷URL',
    persona_id INT NOT NULL COMMENT '数字人ID',
    persona_name VARCHAR(100) COMMENT '数字人姓名',
    persona_role ENUM('scout', 'target') COMMENT '数字人角色',
    question_number INT COMMENT '问题编号',
    question_content TEXT COMMENT '问题内容',
    question_text TEXT COMMENT '问题文本',
    question_options JSON COMMENT '问题选项(JSON格式)',
    answer_choice TEXT COMMENT '选择的答案',
    page_screenshot LONGBLOB COMMENT '页面截图',
    success BOOLEAN COMMENT '是否成功',
    error_message TEXT COMMENT '错误信息',
    browser_profile_id VARCHAR(100) COMMENT '浏览器配置文件ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 索引
    INDEX idx_session_id (session_id) COMMENT '会话ID索引',
    INDEX idx_task_id (task_id) COMMENT '任务ID索引',
    INDEX idx_persona_id (persona_id) COMMENT '数字人ID索引',
    INDEX idx_questionnaire_url (questionnaire_url) COMMENT '问卷URL索引',
    INDEX idx_success (success) COMMENT '成功状态索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='详细答题记录表';

-- =====================================================
-- 4. 任务管理表 (questionnaire_tasks)
-- 用途: 管理问卷任务的整体状态和进度
-- =====================================================
CREATE TABLE IF NOT EXISTS questionnaire_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    task_id VARCHAR(100) UNIQUE NOT NULL COMMENT '任务ID',
    session_id VARCHAR(100) NOT NULL COMMENT '会话ID',
    questionnaire_url VARCHAR(500) NOT NULL COMMENT '问卷URL',
    status ENUM('pending', 'running', 'success', 'failed', 'analyzing') COMMENT '任务状态',
    scout_count INT DEFAULT 2 COMMENT '敢死队人数',
    target_count INT DEFAULT 10 COMMENT '目标答题人数',
    scout_completed INT DEFAULT 0 COMMENT '敢死队完成数',
    target_completed INT DEFAULT 0 COMMENT '目标团队完成数',
    success_rate DECIMAL(5,2) COMMENT '成功率(%)',
    analysis_result JSON COMMENT '分析结果(JSON格式)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_task_id (task_id) COMMENT '任务ID索引',
    INDEX idx_session_id (session_id) COMMENT '会话ID索引',
    INDEX idx_status (status) COMMENT '状态索引',
    INDEX idx_questionnaire_url (questionnaire_url) COMMENT '问卷URL索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='问卷任务管理表';

-- =====================================================
-- 5. 数字人分配表 (persona_assignments)
-- 用途: 记录数字人的任务分配和浏览器配置
-- =====================================================
CREATE TABLE IF NOT EXISTS persona_assignments (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    task_id VARCHAR(100) NOT NULL COMMENT '任务ID',
    session_id VARCHAR(100) NOT NULL COMMENT '会话ID',
    persona_id INT NOT NULL COMMENT '数字人ID',
    persona_name VARCHAR(100) COMMENT '数字人姓名',
    persona_role ENUM('scout', 'target') COMMENT '数字人角色',
    browser_profile_id VARCHAR(100) COMMENT '浏览器配置文件ID',
    status ENUM('pending', 'running', 'success', 'failed') COMMENT '分配状态',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '分配时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    
    -- 索引
    INDEX idx_task_id (task_id) COMMENT '任务ID索引',
    INDEX idx_persona_id (persona_id) COMMENT '数字人ID索引',
    INDEX idx_browser_profile_id (browser_profile_id) COMMENT '浏览器配置文件ID索引',
    INDEX idx_status (status) COMMENT '状态索引',
    INDEX idx_persona_role (persona_role) COMMENT '角色索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数字人任务分配表';

-- =====================================================
-- 6. 详细答题记录表 (detailed_answering_records)
-- 用途: 记录browser-use的详细执行步骤和结果
-- =====================================================
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
    
    -- 索引
    INDEX idx_session_task (session_id, task_id) COMMENT '会话任务复合索引',
    INDEX idx_persona (persona_id) COMMENT '数字人索引',
    INDEX idx_question (question_number) COMMENT '问题编号索引',
    INDEX idx_success (success) COMMENT '成功状态索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='详细答题记录表';

-- =====================================================
-- 7. 页面分析记录表 (page_analysis_records)
-- 用途: 记录问卷页面的分析结果和结构信息
-- =====================================================
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
    
    -- 索引
    INDEX idx_session_page (session_id, page_number) COMMENT '会话页面复合索引',
    INDEX idx_task_id (task_id) COMMENT '任务ID索引',
    INDEX idx_questionnaire_url (questionnaire_url) COMMENT '问卷URL索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='页面分析记录表';

-- =====================================================
-- 插入初始化数据（如果需要）
-- =====================================================

-- 可以在这里添加一些初始化数据，比如默认配置等

-- =====================================================
-- 创建视图（用于方便查询）
-- =====================================================

-- 敢死队成功经验视图
CREATE OR REPLACE VIEW scout_success_experiences AS
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

-- 问卷完成统计视图
CREATE OR REPLACE VIEW questionnaire_completion_stats AS
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

-- =====================================================
-- 说明文档
-- =====================================================

/*
表结构说明:

1. questionnaire_sessions: 核心会话表，记录每个数字人的问卷填写会话
   - 用于统计成功率、耗时等关键指标
   - 支持敢死队和大部队的区分

2. questionnaire_knowledge: 知识库核心表，存储答题经验
   - 敢死队的成功经验会被大部队查询和学习
   - 支持多种经验类型，包括成功/失败模式

3. answer_records: 详细答题记录，记录每个问题的具体答题过程
   - 用于问题级别的分析和调试

4. questionnaire_tasks: 任务管理表，跟踪整个问卷任务的状态
   - 管理敢死队和大部队的协调

5. persona_assignments: 数字人分配表，管理角色分配和浏览器配置
   - 确保每个数字人有独立的浏览器环境

6. detailed_answering_records: browser-use详细执行记录
   - 记录AI代理的每个操作步骤

7. page_analysis_records: 页面分析记录
   - 存储问卷页面的结构分析结果

使用说明:
1. 先执行此SQL文件创建所有表结构
2. 敢死队答题时，经验会保存到questionnaire_knowledge表
3. 大部队答题时，会查询questionnaire_knowledge获取成功经验
4. 通过scout_success_experiences视图可以方便查询敢死队的成功经验
*/ 