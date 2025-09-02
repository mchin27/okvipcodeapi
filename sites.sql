-- 1️⃣ ลบข้อมูลเดิม
TRUNCATE TABLE site_player_tiers RESTART IDENTITY CASCADE;
TRUNCATE TABLE players RESTART IDENTITY CASCADE;

-- 2️⃣ INSERT players
INSERT INTO players (username, site_id, is_active, is_unlimited_code) VALUES
-- thai_789bet (site_id=1)
('nus9331', 1, true, true),
('manus9331', 1, true, true),
('Preechar', 1, true, true),
('kootong', 1, true, true),
('areeroon', 1, true, true),
('VIP0955171905', 1, true, true),
('tong551212', 1, true, true),

-- thai_jun88k36 (site_id=2)
('nus9331', 2, true, true),
('aroon11', 2, true, true),
('manus9331', 2, true, true),
('areeroon', 2, true, true),
('koomoo', 2, true, true),
('nrd1988', 2, true, true);

-- 3️⃣ INSERT site_player_tiers
INSERT INTO site_player_tiers (site_id, player_id, tier_id) VALUES

-- thai_789bet (site_id=1)
-- very_high
(1, (SELECT id FROM players WHERE username = 'nus9331' AND site_id = 1), 1),
(1, (SELECT id FROM players WHERE username = 'manus9331' AND site_id = 1), 1),
(1, (SELECT id FROM players WHERE username = 'areeroon' AND site_id = 1), 1),

-- high
(1, (SELECT id FROM players WHERE username = 'nus9331' AND site_id = 1), 2),
(1, (SELECT id FROM players WHERE username = 'manus9331' AND site_id = 1), 2),
(1, (SELECT id FROM players WHERE username = 'areeroon' AND site_id = 1), 2),

-- mid
(1, (SELECT id FROM players WHERE username = 'nus9331' AND site_id = 1), 3),
(1, (SELECT id FROM players WHERE username = 'manus9331' AND site_id = 1), 3),
(1, (SELECT id FROM players WHERE username = 'areeroon' AND site_id = 1), 3),
(1, (SELECT id FROM players WHERE username = 'Preechar' AND site_id = 1), 3),
(1, (SELECT id FROM players WHERE username = 'kootong' AND site_id = 1), 3),
(1, (SELECT id FROM players WHERE username = 'VIP0955171905' AND site_id = 1), 3),
(1, (SELECT id FROM players WHERE username = 'tong551212' AND site_id = 1), 3),

-- low
(1, (SELECT id FROM players WHERE username = 'Preechar' AND site_id = 1), 4),
(1, (SELECT id FROM players WHERE username = 'kootong' AND site_id = 1), 4),
(1, (SELECT id FROM players WHERE username = 'VIP0955171905' AND site_id = 1), 4),
(1, (SELECT id FROM players WHERE username = 'tong551212' AND site_id = 1), 4),


-- thai_jun88k36 (site_id=2)
-- very_high
(2, (SELECT id FROM players WHERE username = 'nus9331' AND site_id = 2), 1),
(2, (SELECT id FROM players WHERE username = 'aroon11' AND site_id = 2), 1),
(2, (SELECT id FROM players WHERE username = 'manus9331' AND site_id = 2), 1),

-- high
(2, (SELECT id FROM players WHERE username = 'aroon11' AND site_id = 2), 2),
(2, (SELECT id FROM players WHERE username = 'manus9331' AND site_id = 2), 2),
(2, (SELECT id FROM players WHERE username = 'nus9331' AND site_id = 2), 2),

-- mid
(2, (SELECT id FROM players WHERE username = 'areeroon' AND site_id = 2), 3),
(2, (SELECT id FROM players WHERE username = 'koomoo' AND site_id = 2), 3),
(2, (SELECT id FROM players WHERE username = 'nrd1988' AND site_id = 2), 3);



gen sql script insert players and site_player_tiers ตามข้อมูลด้านล่าง ตาม script ตัวอย่างข้างบน
{
  thai_789bet: {
    very_high: ["nus9331", "manus9331", "areeroon"],
    high:  ["nus9331", "manus9331","areeroon"],
    mid: ["nus9331", "manus9331","areeroon", "Preechar", "kootong", "VIP0955171905", "tong551212"],
    low: ["Preechar", "kootong", "VIP0955171905", "tong551212"],
    all: ["nus9331", "manus9331", "Preechar", "kootong", "areeroon", "VIP0955171905", "tong551212"]
  },
  thai_jun88k36: {
    very_high:["nus9331", "aroon11", "manus9331"],
    high: ["aroon11", "manus9331", "nus9331"],
    mid: ["areeroon", "koomoo", "nrd1988", "areeroon", "koomoo", "nrd1988"],
    low: [],
    all: ["aroon11", "manus9331", "nus9331","areeroon", "koomoo", "nrd1988"],
  }
}