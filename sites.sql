-- 1️⃣ ลบข้อมูลเดิม
TRUNCATE TABLE site_player_tiers RESTART IDENTITY CASCADE;
TRUNCATE TABLE players RESTART IDENTITY CASCADE;

-- 2️⃣ INSERT players
INSERT INTO players (username, site_id, is_active, is_unlimited_code) VALUES
('nus9331', 1, true, true),
('manus9331', 1, true, true),
('Preechar', 1, true, true),
('nus9331', 2, true, true),
('aroon11', 2, true, true),
('manus9331', 2, true, true),
('wat3366', 2, true, true),
('koonogk', 2, true, true);

-- 3️⃣ INSERT site_player_tiers
INSERT INTO site_player_tiers (site_id, player_id, tier_id) VALUES
-- thai_789bet (site_id=1)
(1, (SELECT id FROM players WHERE username = 'nus9331' AND site_id = 1), 1),
(1, (SELECT id FROM players WHERE username = 'manus9331' AND site_id = 1), 1),
(1, (SELECT id FROM players WHERE username = 'nus9331' AND site_id = 1), 2),
(1, (SELECT id FROM players WHERE username = 'manus9331' AND site_id = 1), 2),
(1, (SELECT id FROM players WHERE username = 'Preechar' AND site_id = 1), 3),
(1, (SELECT id FROM players WHERE username = 'Preechar' AND site_id = 1), 4),

-- thai_jun88k36 (site_id=2)
(2, (SELECT id FROM players WHERE username = 'nus9331' AND site_id = 2), 1),
(2, (SELECT id FROM players WHERE username = 'aroon11' AND site_id = 2), 1),
(2, (SELECT id FROM players WHERE username = 'manus9331' AND site_id = 2), 1),
(2, (SELECT id FROM players WHERE username = 'aroon11' AND site_id = 2), 2),
(2, (SELECT id FROM players WHERE username = 'manus9331' AND site_id = 2), 2),
(2, (SELECT id FROM players WHERE username = 'nus9331' AND site_id = 2), 2),
(2, (SELECT id FROM players WHERE username = 'wat3366' AND site_id = 2), 3),
(2, (SELECT id FROM players WHERE username = 'koonogk' AND site_id = 2), 3),
(2, (SELECT id FROM players WHERE username = 'wat3366' AND site_id = 2), 4),
(2, (SELECT id FROM players WHERE username = 'koonogk' AND site_id = 2), 4),
(2, (SELECT id FROM players WHERE username = 'wat3366' AND site_id = 2), 5),
(2, (SELECT id FROM players WHERE username = 'koonogk' AND site_id = 2), 5);
