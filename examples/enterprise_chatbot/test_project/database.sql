-- Enterprise Management System Database Schema
-- Version: 2.1.0
-- Created: 2025-09-19

-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    age INTEGER CHECK (age >= 18 AND age <= 100),
    department VARCHAR(50) NOT NULL,
    salary DECIMAL(10,2) CHECK (salary > 0),
    active BOOLEAN DEFAULT TRUE,
    join_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skills table
CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User skills junction table
CREATE TABLE user_skills (
    user_id INTEGER,
    skill_id INTEGER,
    proficiency_level INTEGER CHECK (proficiency_level BETWEEN 1 AND 5),
    certified BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (user_id, skill_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- Projects table
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    start_date DATE NOT NULL,
    end_date DATE,
    budget DECIMAL(12,2),
    department VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User projects junction table
CREATE TABLE user_projects (
    user_id INTEGER,
    project_id INTEGER,
    role VARCHAR(50) NOT NULL,
    allocation_percentage DECIMAL(5,2) CHECK (allocation_percentage BETWEEN 0 AND 100),
    PRIMARY KEY (user_id, project_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Insert sample data
INSERT INTO skills (name, category, description) VALUES
('Python', 'Programming', 'High-level programming language'),
('JavaScript', 'Programming', 'Web programming language'),
('React', 'Framework', 'JavaScript library for building user interfaces'),
('Docker', 'DevOps', 'Containerization platform'),
('SQL', 'Database', 'Structured Query Language'),
('Analytics', 'Data Science', 'Data analysis and interpretation'),
('Tableau', 'Visualization', 'Business intelligence tool'),
('Kubernetes', 'DevOps', 'Container orchestration platform'),
('AWS', 'Cloud', 'Amazon Web Services cloud platform'),
('Terraform', 'DevOps', 'Infrastructure as Code tool');

INSERT INTO users (name, email, age, department, salary, active, join_date) VALUES
('Alice Johnson', 'alice.johnson@enterprise.com', 30, 'Engineering', 95000.00, TRUE, '2022-03-15'),
('Bob Smith', 'bob.smith@enterprise.com', 28, 'Marketing', 75000.00, TRUE, '2023-01-10'),
('Charlie Brown', 'charlie.brown@enterprise.com', 35, 'DevOps', 110000.00, TRUE, '2021-07-20');

INSERT INTO projects (name, description, status, start_date, budget, department) VALUES
('AgenticFlow Enhancement', 'Enhancing AI agent capabilities', 'active', '2025-01-15', 250000.00, 'Engineering'),
('Data Analysis Pipeline', 'Building automated data processing pipeline', 'active', '2025-02-01', 150000.00, 'Marketing'),
('Infrastructure Automation', 'Automating deployment and monitoring', 'active', '2024-11-01', 200000.00, 'DevOps');

-- Link users to skills
INSERT INTO user_skills (user_id, skill_id, proficiency_level, certified) VALUES
-- Alice's skills
(1, 1, 5, TRUE),   -- Python
(1, 2, 4, TRUE),   -- JavaScript  
(1, 3, 4, FALSE),  -- React
(1, 4, 3, FALSE),  -- Docker

-- Bob's skills
(2, 6, 5, TRUE),   -- Analytics
(2, 5, 4, TRUE),   -- SQL
(2, 7, 4, FALSE),  -- Tableau
(2, 1, 3, FALSE),  -- Python

-- Charlie's skills
(3, 8, 5, TRUE),   -- Kubernetes
(3, 4, 5, TRUE),   -- Docker
(3, 9, 4, TRUE),   -- AWS
(3, 1, 4, FALSE),  -- Python
(3, 10, 3, FALSE); -- Terraform

-- Link users to projects
INSERT INTO user_projects (user_id, project_id, role, allocation_percentage) VALUES
(1, 1, 'Lead Developer', 80.00),
(2, 2, 'Data Analyst', 90.00),
(3, 3, 'DevOps Engineer', 75.00);

-- Create indexes for better performance
CREATE INDEX idx_users_department ON users(department);
CREATE INDEX idx_users_active ON users(active);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_department ON projects(department);

-- Create views for common queries
CREATE VIEW active_users AS
SELECT u.*, 
       GROUP_CONCAT(s.name) as skills,
       p.name as current_project
FROM users u
LEFT JOIN user_skills us ON u.id = us.user_id
LEFT JOIN skills s ON us.skill_id = s.id
LEFT JOIN user_projects up ON u.id = up.user_id
LEFT JOIN projects p ON up.project_id = p.id AND p.status = 'active'
WHERE u.active = TRUE
GROUP BY u.id;

CREATE VIEW department_stats AS
SELECT 
    department,
    COUNT(*) as total_users,
    COUNT(CASE WHEN active = TRUE THEN 1 END) as active_users,
    AVG(salary) as average_salary,
    MIN(salary) as min_salary,
    MAX(salary) as max_salary
FROM users
GROUP BY department;

-- Sample queries that would be used by the application

-- Find all users with Python skills
-- SELECT u.name, u.department, us.proficiency_level 
-- FROM users u
-- JOIN user_skills us ON u.id = us.user_id
-- JOIN skills s ON us.skill_id = s.id
-- WHERE s.name = 'Python' AND u.active = TRUE;

-- Get department budget allocation
-- SELECT p.department, SUM(p.budget) as total_budget
-- FROM projects p
-- WHERE p.status = 'active'
-- GROUP BY p.department;

-- Find users working on multiple projects
-- SELECT u.name, COUNT(up.project_id) as project_count
-- FROM users u
-- JOIN user_projects up ON u.id = up.user_id
-- JOIN projects p ON up.project_id = p.id
-- WHERE p.status = 'active'
-- GROUP BY u.id, u.name
-- HAVING COUNT(up.project_id) > 1;