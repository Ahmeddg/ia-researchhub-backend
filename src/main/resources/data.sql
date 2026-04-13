-- Article Management System - Demo Data Script for Spring Boot Auto-Loading
-- Uses natural keys (username, email, doi, domain name) so FKs stay valid when IDs are not 1..n

CREATE EXTENSION IF NOT EXISTS pgcrypto;

INSERT INTO roles (name) VALUES ('ROLE_ADMIN') ON CONFLICT (name) DO NOTHING;
INSERT INTO roles (name) VALUES ('ROLE_USER') ON CONFLICT (name) DO NOTHING;
INSERT INTO roles (name) VALUES ('ROLE_MODERATOR') ON CONFLICT (name) DO NOTHING;
INSERT INTO roles (name) VALUES ('ROLE_RESEARCHER') ON CONFLICT (name) DO NOTHING;

INSERT INTO users (username, email, password, enabled) VALUES
('admin', 'admin@example.com', crypt('admin123', gen_salt('bf', 10)), true) ON CONFLICT (username) DO NOTHING;
INSERT INTO users (username, email, password, enabled) VALUES
('john_doe', 'john@example.com', crypt('password123', gen_salt('bf', 10)), true) ON CONFLICT (username) DO NOTHING;
INSERT INTO users (username, email, password, enabled) VALUES
('jane_smith', 'jane@example.com', crypt('password123', gen_salt('bf', 10)), true) ON CONFLICT (username) DO NOTHING;
INSERT INTO users (username, email, password, enabled) VALUES
('mike_wilson', 'mike@example.com', crypt('password123', gen_salt('bf', 10)), true) ON CONFLICT (username) DO NOTHING;
INSERT INTO users (username, email, password, enabled) VALUES
('sarah_jones', 'sarah@example.com', crypt('password123', gen_salt('bf', 10)), true) ON CONFLICT (username) DO NOTHING;
INSERT INTO users (username, email, password, enabled) VALUES
('tachref-1', 'ad@gmail.com', crypt('12345678', gen_salt('bf', 10)), true) 
ON CONFLICT (username) DO UPDATE
SET email = EXCLUDED.email,
    password = EXCLUDED.password,
    enabled = EXCLUDED.enabled;
INSERT INTO users (username, email, password, enabled) VALUES
('hazem', 'hazem@gmail.com', crypt('12345678', gen_salt('bf', 10)), true)
ON CONFLICT (username) DO UPDATE
SET email = EXCLUDED.email,
    password = EXCLUDED.password,
    enabled = EXCLUDED.enabled;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u JOIN roles r ON r.name = 'ROLE_ADMIN' WHERE u.username = 'admin'
ON CONFLICT DO NOTHING;
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u JOIN roles r ON r.name = 'ROLE_USER' WHERE u.username = 'admin'
ON CONFLICT DO NOTHING;
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u JOIN roles r ON r.name = 'ROLE_USER' WHERE u.username = 'john_doe'
ON CONFLICT DO NOTHING;
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u JOIN roles r ON r.name = 'ROLE_MODERATOR' WHERE u.username = 'john_doe'
ON CONFLICT DO NOTHING;
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u JOIN roles r ON r.name = 'ROLE_USER' WHERE u.username = 'jane_smith'
ON CONFLICT DO NOTHING;
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u JOIN roles r ON r.name = 'ROLE_USER' WHERE u.username = 'mike_wilson'
ON CONFLICT DO NOTHING;
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u JOIN roles r ON r.name = 'ROLE_USER' WHERE u.username = 'sarah_jones'
ON CONFLICT DO NOTHING;

INSERT INTO researchers (full_name, email, affiliation, biography) VALUES
('Dr. Alice Johnson', 'alice@mit.edu', 'Massachusetts Institute of Technology', 'Leading researcher in artificial intelligence with 15 years of experience in machine learning and deep neural networks.')
ON CONFLICT (email) DO NOTHING;
INSERT INTO researchers (full_name, email, affiliation, biography) VALUES
('Dr. Bob Chen', 'bob@stanford.edu', 'Stanford University', 'Expert in natural language processing and computer vision. Published over 50 peer-reviewed papers.')
ON CONFLICT (email) DO NOTHING;
INSERT INTO researchers (full_name, email, affiliation, biography) VALUES
('Dr. Carol Williams', 'carol@harvard.edu', 'Harvard University', 'Specialization in reinforcement learning and robotics. Founder of the AI Lab at Harvard.')
ON CONFLICT (email) DO NOTHING;
INSERT INTO researchers (full_name, email, affiliation, biography) VALUES
('Dr. David Brown', 'david@berkeley.edu', 'University of California Berkeley', 'Focuses on explainable AI and ethical machine learning implementations.')
ON CONFLICT (email) DO NOTHING;
INSERT INTO researchers (full_name, email, affiliation, biography) VALUES
('Dr. Emma Davis', 'emma@oxford.ac.uk', 'University of Oxford', 'Research interests include quantum computing and its applications to AI.')
ON CONFLICT (email) DO NOTHING;

INSERT INTO domains (name, description) VALUES
('Artificial Intelligence', 'AI and machine learning research including neural networks, deep learning, and intelligent systems.')
ON CONFLICT (name) DO NOTHING;
INSERT INTO domains (name, description) VALUES
('Data Science', 'Data analysis, big data processing, and statistical methods for data-driven decision making.')
ON CONFLICT (name) DO NOTHING;
INSERT INTO domains (name, description) VALUES
('Computer Vision', 'Image processing, object detection, facial recognition, and visual understanding systems.')
ON CONFLICT (name) DO NOTHING;
INSERT INTO domains (name, description) VALUES
('Natural Language Processing', 'Language understanding, text analysis, machine translation, and conversational AI.')
ON CONFLICT (name) DO NOTHING;
INSERT INTO domains (name, description) VALUES
('Robotics', 'Autonomous systems, robotic control, and human-robot interaction research.')
ON CONFLICT (name) DO NOTHING;

INSERT INTO publications (title, abstract_text, publication_date, pdf_url, doi, domain_id, status)
SELECT 'Deep Residual Learning for Image Recognition', 'We present a residual learning framework to ease training of very deep neural networks. This framework enables training networks with more than 150 layers, achieving record-breaking accuracy on ImageNet.', '2015-12-10', 'https://arxiv.org/pdf/1512.03385.pdf', '10.1109/CVPR.2016.90', d.id, 'PUBLISHED'
FROM domains d WHERE d.name = 'Computer Vision'
ON CONFLICT (doi) DO NOTHING;
INSERT INTO publications (title, abstract_text, publication_date, pdf_url, doi, domain_id, status)
SELECT 'Attention is All You Need', 'The dominant sequence transduction models are based on complex recurrent/convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.', '2017-06-12', 'https://arxiv.org/pdf/1706.03762.pdf', '10.5555/3295222.3295349', d.id, 'PUBLISHED'
FROM domains d WHERE d.name = 'Natural Language Processing'
ON CONFLICT (doi) DO NOTHING;
INSERT INTO publications (title, abstract_text, publication_date, pdf_url, doi, domain_id, status)
SELECT 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding', 'We introduce BERT, a new pre-training approach which stands for Bidirectional Encoder Representations from Transformers. Unlike previous language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text.', '2018-10-11', 'https://arxiv.org/pdf/1810.04805.pdf', '10.18653/v1/N19-1423', d.id, 'PUBLISHED'
FROM domains d WHERE d.name = 'Natural Language Processing'
ON CONFLICT (doi) DO NOTHING;
INSERT INTO publications (title, abstract_text, publication_date, pdf_url, doi, domain_id, status)
SELECT 'Generative Adversarial Nets', 'We propose a new framework for estimating generative models via an adversarial process, in which we simultaneously train two models: a generative model G that captures the data distribution, and a discriminative model D that estimates the probability that a sample came from the training data.', '2014-06-10', 'https://arxiv.org/pdf/1406.2661.pdf', '10.5555/2969033.2969125', d.id, 'PUBLISHED'
FROM domains d WHERE d.name = 'Artificial Intelligence'
ON CONFLICT (doi) DO NOTHING;
INSERT INTO publications (title, abstract_text, publication_date, pdf_url, doi, domain_id, status)
SELECT 'ImageNet-21K Pretraining for the Masses', 'Transformers trained on ImageNet-21K produce excellent results when fine-tuned on downstream tasks. We present ViT-g, a new model trained on ImageNet-21K that achieves state-of-the-art results on multiple benchmarks.', '2021-12-02', 'https://arxiv.org/pdf/2106.14881.pdf', '10.1007/978-3-030-58604-1_15', d.id, 'PUBLISHED'
FROM domains d WHERE d.name = 'Artificial Intelligence'
ON CONFLICT (doi) DO NOTHING;

INSERT INTO publication_researchers (publication_id, researcher_id)
SELECT p.id, r.id FROM publications p JOIN researchers r ON r.email = 'alice@mit.edu' WHERE p.doi = '10.1109/CVPR.2016.90'
ON CONFLICT DO NOTHING;
INSERT INTO publication_researchers (publication_id, researcher_id)
SELECT p.id, r.id FROM publications p JOIN researchers r ON r.email = 'bob@stanford.edu' WHERE p.doi = '10.5555/3295222.3295349'
ON CONFLICT DO NOTHING;
INSERT INTO publication_researchers (publication_id, researcher_id)
SELECT p.id, r.id FROM publications p JOIN researchers r ON r.email = 'david@berkeley.edu' WHERE p.doi = '10.5555/3295222.3295349'
ON CONFLICT DO NOTHING;
INSERT INTO publication_researchers (publication_id, researcher_id)
SELECT p.id, r.id FROM publications p JOIN researchers r ON r.email = 'bob@stanford.edu' WHERE p.doi = '10.18653/v1/N19-1423'
ON CONFLICT DO NOTHING;
INSERT INTO publication_researchers (publication_id, researcher_id)
SELECT p.id, r.id FROM publications p JOIN researchers r ON r.email = 'emma@oxford.ac.uk' WHERE p.doi = '10.18653/v1/N19-1423'
ON CONFLICT DO NOTHING;
INSERT INTO publication_researchers (publication_id, researcher_id)
SELECT p.id, r.id FROM publications p JOIN researchers r ON r.email = 'alice@mit.edu' WHERE p.doi = '10.5555/2969033.2969125'
ON CONFLICT DO NOTHING;
INSERT INTO publication_researchers (publication_id, researcher_id)
SELECT p.id, r.id FROM publications p JOIN researchers r ON r.email = 'carol@harvard.edu' WHERE p.doi = '10.1007/978-3-030-58604-1_15'
ON CONFLICT DO NOTHING;

INSERT INTO projects (title, description, ai_category, domain_id)
SELECT 'Advanced Computer Vision System', 'Development of cutting-edge computer vision algorithms for real-time object detection and semantic segmentation applications.', 'Deep Learning', d.id
FROM domains d WHERE d.name = 'Computer Vision'
AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.title = 'Advanced Computer Vision System');
INSERT INTO projects (title, description, ai_category, domain_id)
SELECT 'Natural Language Understanding Engine', 'Building a comprehensive NLP system capable of understanding context, sentiment analysis, and semantic relationships in text.', 'NLP', d.id
FROM domains d WHERE d.name = 'Natural Language Processing'
AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.title = 'Natural Language Understanding Engine');
INSERT INTO projects (title, description, ai_category, domain_id)
SELECT 'Autonomous Robot Navigation', 'Creating intelligent navigation systems for autonomous robots using computer vision and machine learning.', 'Robotics', d.id
FROM domains d WHERE d.name = 'Robotics'
AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.title = 'Autonomous Robot Navigation');
INSERT INTO projects (title, description, ai_category, domain_id)
SELECT 'Healthcare Diagnostic AI', 'Developing AI models for medical image analysis and disease diagnosis using deep learning techniques.', 'Deep Learning', d.id
FROM domains d WHERE d.name = 'Artificial Intelligence'
AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.title = 'Healthcare Diagnostic AI');
INSERT INTO projects (title, description, ai_category, domain_id)
SELECT 'Predictive Analytics Platform', 'Building a comprehensive data analytics platform for predictive modeling and business intelligence.', 'Data Science', d.id
FROM domains d WHERE d.name = 'Data Science'
AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.title = 'Predictive Analytics Platform');

INSERT INTO news (title, content, created_at, user_id)
SELECT 'AI Research Breakthrough: New Model Achieves 99.5% Accuracy', 'Researchers have announced a breakthrough in AI research with a new model achieving 99.5% accuracy on the ImageNet dataset. The model uses novel attention mechanisms and transfer learning techniques.', NOW(), u.id
FROM users u WHERE u.username = 'admin'
AND NOT EXISTS (SELECT 1 FROM news n WHERE n.title = 'AI Research Breakthrough: New Model Achieves 99.5% Accuracy');
INSERT INTO news (title, content, created_at, user_id)
SELECT 'International Conference on AI and Machine Learning Announced', 'The 2024 International Conference on AI and Machine Learning will be held in Vancouver, Canada. Registration is now open with early bird discounts available until March 31st.', NOW(), u.id
FROM users u WHERE u.username = 'john_doe'
AND NOT EXISTS (SELECT 1 FROM news n WHERE n.title = 'International Conference on AI and Machine Learning Announced');
INSERT INTO news (title, content, created_at, user_id)
SELECT 'New Open-Source AI Framework Released', 'A new open-source framework for building and deploying AI models has been released. The framework simplifies the process of creating, training, and deploying machine learning models.', NOW(), u.id
FROM users u WHERE u.username = 'jane_smith'
AND NOT EXISTS (SELECT 1 FROM news n WHERE n.title = 'New Open-Source AI Framework Released');
INSERT INTO news (title, content, created_at, user_id)
SELECT 'PhD Opportunities in AI and Data Science', 'Leading universities are offering fully funded PhD positions in artificial intelligence and data science. Apply now for the 2024-2025 academic year.', NOW(), u.id
FROM users u WHERE u.username = 'admin'
AND NOT EXISTS (SELECT 1 FROM news n WHERE n.title = 'PhD Opportunities in AI and Data Science');
INSERT INTO news (title, content, created_at, user_id)
SELECT 'AI Ethics Guidelines Published by International Committee', 'New international guidelines for ethical AI development have been published. These guidelines cover fairness, transparency, accountability, and human oversight.', NOW(), u.id
FROM users u WHERE u.username = 'john_doe'
AND NOT EXISTS (SELECT 1 FROM news n WHERE n.title = 'AI Ethics Guidelines Published by International Committee');

-- Super-user access for tachref-1
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u CROSS JOIN roles r 
WHERE u.username = 'tachref-1' AND r.name IN ('ROLE_ADMIN', 'ROLE_USER', 'ROLE_MODERATOR', 'ROLE_RESEARCHER')
ON CONFLICT DO NOTHING;

-- Super-user access for hazem
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u CROSS JOIN roles r
WHERE u.username = 'hazem' AND r.name IN ('ROLE_ADMIN', 'ROLE_USER', 'ROLE_MODERATOR', 'ROLE_RESEARCHER')
ON CONFLICT DO NOTHING;
