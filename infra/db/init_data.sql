-- 插入药品基础信息
INSERT INTO drugs (id, name, generic_name, spec, manufacturer, is_rx, contraindications_json, flags_json)
VALUES
(1, '布洛芬片', 'Ibuprofen', '0.2g*24片', '某制药厂', FALSE, '["pregnancy"]', '["fever_high"]'),
(2, '阿莫西林胶囊', 'Amoxicillin', '0.25g*20粒', '某制药厂', TRUE, '[]', '[]'),
(3, '氯雷他定片', 'Loratadine', '10mg*10片', '某制药厂', FALSE, '[]', '[]');

-- 插入库存信息
INSERT INTO inventory (drug_id, stock, batch_no, expire_date)
VALUES
(1, 200, 'B20250101', '2026-12-31'),
(2, 150, 'A20250102', '2026-06-30'),
(3, 300, 'C20250103', '2027-01-31');

-- 插入价格信息（不同会员等级）
INSERT INTO prices (drug_id, list_price, member_tier, discount_rate)
VALUES
(1, 19.90, 'basic', 1.0),
(1, 19.90, 'gold', 0.9),
(2, 29.90, 'basic', 1.0),
(2, 29.90, 'gold', 0.85),
(3, 15.00, 'basic', 1.0),
(3, 15.00, 'gold', 0.95);