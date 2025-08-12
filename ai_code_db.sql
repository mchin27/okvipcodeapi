DROP VIEW IF EXISTS "public"."available_players_by_site_tier";
 WITH current_locks AS (
         SELECT players_lock.player_id
           FROM players_lock
          WHERE ((players_lock.timelock + ((players_lock.lock_time_minutes || ' minutes'::text))::interval) > now())
        ), todays_applies AS (
         SELECT DISTINCT pp.player_id
           FROM (promo_code_applies pca
             JOIN player_package_purchases pp ON ((pca.purchase_id = pp.id)))
          WHERE ((pca.apply_time)::date = CURRENT_DATE)
        ), active_packages AS (
         SELECT pp.player_id
           FROM ((player_package_purchases pp
             JOIN packages pk ON ((pp.package_id = pk.id)))
             LEFT JOIN promo_code_applies pca ON ((pca.purchase_id = pp.id)))
          WHERE (pk.is_active = true)
          GROUP BY pp.id, pk.code_limit, pp.player_id
         HAVING ((count(pca.id) < pk.code_limit) OR (pk.code_limit = 0))
        )
 SELECT s.site_key,
    t.name AS tier_name,
    p.username
   FROM (((players p
     JOIN sites s ON ((p.site_id = s.id)))
     JOIN site_player_tiers spt ON ((spt.player_id = p.id)))
     JOIN tiers t ON ((spt.tier_id = t.id)))
  WHERE ((p.is_active = true) AND (NOT (p.id IN ( SELECT current_locks.player_id
           FROM current_locks))) AND (NOT (p.id IN ( SELECT todays_applies.player_id
           FROM todays_applies))) AND ((p.is_unlimited_code = true) OR (p.id IN ( SELECT active_packages.player_id
           FROM active_packages))));

DROP VIEW IF EXISTS "public"."available_players_grouped_by_player";
 WITH current_locks AS (
         SELECT players_lock.player_id
           FROM players_lock
          WHERE ((players_lock.timelock + ((players_lock.lock_time_minutes || ' minutes'::text))::interval) > now())
        ), todays_applies AS (
         SELECT DISTINCT pp.player_id
           FROM (promo_code_applies pca
             JOIN player_package_purchases pp ON ((pca.purchase_id = pp.id)))
          WHERE ((pca.apply_time)::date = CURRENT_DATE)
        ), active_packages AS (
         SELECT pp.player_id
           FROM ((player_package_purchases pp
             JOIN packages pk ON ((pp.package_id = pk.id)))
             LEFT JOIN promo_code_applies pca ON ((pca.purchase_id = pp.id)))
          WHERE (pk.is_active = true)
          GROUP BY pp.player_id, pk.code_limit, pp.id
         HAVING ((count(pca.id) < pk.code_limit) OR (pk.code_limit = 0))
        ), eligible_players AS (
         SELECT p_1.id,
            p_1.username,
            p_1.site_id
           FROM players p_1
          WHERE ((p_1.is_active = true) AND (NOT (p_1.id IN ( SELECT current_locks.player_id
                   FROM current_locks))) AND (NOT (p_1.id IN ( SELECT todays_applies.player_id
                   FROM todays_applies))) AND ((p_1.is_unlimited_code = true) OR (p_1.id IN ( SELECT active_packages.player_id
                   FROM active_packages))))
        )
 SELECT p.username,
    s.site_key,
    string_agg(DISTINCT t.name, ', '::text ORDER BY t.name) AS tiers
   FROM (((eligible_players p
     JOIN sites s ON ((s.id = p.site_id)))
     JOIN site_player_tiers spt ON ((spt.player_id = p.id)))
     JOIN tiers t ON ((t.id = spt.tier_id)))
  GROUP BY p.username, s.site_key;

DROP TABLE IF EXISTS "public"."package_orders";
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS package_orders_id_seq;

-- Table Definition
CREATE TABLE "public"."package_orders" (
    "id" int4 NOT NULL DEFAULT nextval('package_orders_id_seq'::regclass),
    "player_id" int4,
    "package_id" int4,
    "slip_url" text,
    "notify_telegram" bool DEFAULT false,
    "telegram_id" text,
    "status" text DEFAULT 'pending'::text,
    "order_time" timestamp DEFAULT now(),
    "approved_time" timestamp,
    CONSTRAINT "package_orders_package_id_fkey" FOREIGN KEY ("package_id") REFERENCES "public"."packages"("id"),
    CONSTRAINT "package_orders_player_id_fkey" FOREIGN KEY ("player_id") REFERENCES "public"."players"("id"),
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "public"."package_tiers";
-- Table Definition
CREATE TABLE "public"."package_tiers" (
    "package_id" int4 NOT NULL,
    "tier_id" int4 NOT NULL,
    CONSTRAINT "package_tiers_package_id_fkey" FOREIGN KEY ("package_id") REFERENCES "public"."packages"("id"),
    CONSTRAINT "package_tiers_tier_id_fkey" FOREIGN KEY ("tier_id") REFERENCES "public"."tiers"("id"),
    PRIMARY KEY ("package_id","tier_id")
);

DROP TABLE IF EXISTS "public"."packages";
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS packages_id_seq;

-- Table Definition
CREATE TABLE "public"."packages" (
    "id" int4 NOT NULL DEFAULT nextval('packages_id_seq'::regclass),
    "name" text NOT NULL,
    "description" text,
    "price" numeric,
    "sale_price" numeric,
    "code_limit" int4,
    "site_id" int4,
    "logo_url" text,
    "is_active" bool DEFAULT true,
    CONSTRAINT "packages_site_id_fkey" FOREIGN KEY ("site_id") REFERENCES "public"."sites"("id"),
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "public"."player_package_purchases";
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS player_package_purchases_id_seq;

-- Table Definition
CREATE TABLE "public"."player_package_purchases" (
    "id" int4 NOT NULL DEFAULT nextval('player_package_purchases_id_seq'::regclass),
    "player_id" int4,
    "package_id" int4,
    "purchase_time" timestamp NOT NULL DEFAULT now(),
    CONSTRAINT "player_package_purchases_package_id_fkey" FOREIGN KEY ("package_id") REFERENCES "public"."packages"("id"),
    CONSTRAINT "player_package_purchases_player_id_fkey" FOREIGN KEY ("player_id") REFERENCES "public"."players"("id"),
    PRIMARY KEY ("id")
);

DROP VIEW IF EXISTS "public"."player_package_usage_view";
 SELECT p.id AS player_id,
    p.username,
    pk.name AS package_name,
    count(DISTINCT pca.id) AS total_codes_used,
    string_agg(DISTINCT t.name, ', '::text) AS tiers_allowed,
    min(ppp.purchase_time) AS first_purchase,
    max(ppp.purchase_time) AS last_purchase
   FROM (((((players p
     JOIN player_package_purchases ppp ON ((p.id = ppp.player_id)))
     JOIN packages pk ON ((ppp.package_id = pk.id)))
     LEFT JOIN promo_code_applies pca ON ((ppp.id = pca.purchase_id)))
     LEFT JOIN package_tiers pt ON ((pk.id = pt.package_id)))
     LEFT JOIN tiers t ON ((pt.tier_id = t.id)))
  GROUP BY p.id, p.username, pk.name;

DROP TABLE IF EXISTS "public"."players";
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS players_id_seq;

-- Table Definition
CREATE TABLE "public"."players" (
    "id" int4 NOT NULL DEFAULT nextval('players_id_seq'::regclass),
    "username" text NOT NULL,
    "site_id" int4,
    "first_name" text,
    "last_name" text,
    "phone" text,
    "email" text,
    "is_active" bool DEFAULT true,
    "is_unlimited_code" bool DEFAULT true,
    "telegram_id" int4,
    CONSTRAINT "players_site_id_fkey" FOREIGN KEY ("site_id") REFERENCES "public"."sites"("id"),
    PRIMARY KEY ("id")
);


-- Indices
CREATE UNIQUE INDEX players_username_site_id_key ON public.players USING btree (username, site_id);

DROP TABLE IF EXISTS "public"."players_lock";
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS players_lock_id_seq;

-- Table Definition
CREATE TABLE "public"."players_lock" (
    "id" int4 NOT NULL DEFAULT nextval('players_lock_id_seq'::regclass),
    "player_id" int4 NOT NULL,
    "timelock" timestamp NOT NULL,
    "lock_time_minutes" int4 NOT NULL,
    "lock_message" text,
    "lock_code" int4 DEFAULT 0,
    "created_at" timestamp DEFAULT now(),
    CONSTRAINT "players_lock_player_id_fkey" FOREIGN KEY ("player_id") REFERENCES "public"."players"("id") ON DELETE CASCADE,
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "public"."promo_code_applies";
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS promo_code_applies_id_seq;

-- Table Definition
CREATE TABLE "public"."promo_code_applies" (
    "id" int4 NOT NULL DEFAULT nextval('promo_code_applies_id_seq'::regclass),
    "purchase_id" int4,
    "promo_code" text NOT NULL,
    "point" numeric,
    "status" text NOT NULL,
    "apply_time" timestamp NOT NULL DEFAULT now(),
    CONSTRAINT "promo_code_applies_purchase_id_fkey" FOREIGN KEY ("purchase_id") REFERENCES "public"."player_package_purchases"("id"),
    PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "public"."site_player_tiers";
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS site_player_tiers_id_seq;

-- Table Definition
CREATE TABLE "public"."site_player_tiers" (
    "id" int4 NOT NULL DEFAULT nextval('site_player_tiers_id_seq'::regclass),
    "site_id" int4,
    "player_id" int4,
    "tier_id" int4,
    CONSTRAINT "site_player_tiers_player_id_fkey" FOREIGN KEY ("player_id") REFERENCES "public"."players"("id"),
    CONSTRAINT "site_player_tiers_site_id_fkey" FOREIGN KEY ("site_id") REFERENCES "public"."sites"("id"),
    CONSTRAINT "site_player_tiers_tier_id_fkey" FOREIGN KEY ("tier_id") REFERENCES "public"."tiers"("id"),
    PRIMARY KEY ("id")
);


-- Indices
CREATE UNIQUE INDEX site_player_tiers_site_id_player_id_tier_id_key ON public.site_player_tiers USING btree (site_id, player_id, tier_id);

DROP TABLE IF EXISTS "public"."sites";
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS sites_id_seq;

-- Table Definition
CREATE TABLE "public"."sites" (
    "id" int4 NOT NULL DEFAULT nextval('sites_id_seq'::regclass),
    "site_key" text NOT NULL,
    "name" text,
    PRIMARY KEY ("id")
);


-- Indices
CREATE UNIQUE INDEX sites_site_key_key ON public.sites USING btree (site_key);

DROP TABLE IF EXISTS "public"."tiers";
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS tiers_id_seq;

-- Table Definition
CREATE TABLE "public"."tiers" (
    "id" int4 NOT NULL DEFAULT nextval('tiers_id_seq'::regclass),
    "name" text NOT NULL,
    PRIMARY KEY ("id")
);


-- Indices
CREATE UNIQUE INDEX tiers_name_key ON public.tiers USING btree (name);

DROP VIEW IF EXISTS "public"."vw_player_package_status";
 SELECT pp.id AS purchase_id,
    p.username,
    pk.name AS package_name,
    pk.code_limit,
    count(pa.id) AS codes_received,
    (pk.code_limit - count(pa.id)) AS codes_remaining
   FROM (((player_package_purchases pp
     JOIN players p ON ((pp.player_id = p.id)))
     JOIN packages pk ON ((pp.package_id = pk.id)))
     LEFT JOIN promo_code_applies pa ON ((pa.purchase_id = pp.id)))
  GROUP BY pp.id, p.username, pk.name, pk.code_limit;




INSERT INTO "public"."package_tiers" ("package_id", "tier_id") VALUES
(1, 4),
(1, 3),
(2, 4),
(2, 3),
(3, 1),
(3, 2),
(4, 3),
(4, 4),
(5, 2),
(5, 3),
(6, 2),
(6, 3),
(7, 1),
(7, 2),
(8, 3),
(8, 4),
(9, 2),
(9, 3);
INSERT INTO "public"."packages" ("id", "name", "description", "price", "sale_price", "code_limit", "site_id", "logo_url", "is_active") VALUES
(1, 'ใช้คูปองแพ็กเกจยิงโค้ดฟรี', 'ได้แน่นอน แนบคูปองแทนสลิปรับสิทธิ์ ไม่มีจำกัดเวลา', 0, 0, 1, 2, '/images/procodeAi.png', 't'),
(2, 'แพ็กเกจสุ่มราคามินิ 1 โค้ด', 'ได้แน่นอน 1 โค้ด ยอดโค้ดราคาสุ่ม 10-50 ต่อโค้ด  ไม่มีจำกัดเวลา ได้แน่นอน 1 โค้ด', 10, 0, 1, 2, '/images/procodeAi.png', 't'),
(3, 'แพ็กเกจมินิวัดใจ 1 โค้ด (ประกันยอดโค้ดราคา 20 ไม่มีขาดทุน)', 'ประกันยอดโค้ดราคา 20 บาทขึ้นไป ไม่มีจำกัดเวลา ได้แน่นอน 1 โค้ด', 20, 0, 1, 2, '/images/procodeAi.png', 't'),
(4, 'แพ็กเกจสุ่มราคา 3 โค้ด (ไม่มีขาดทุน)', 'ได้แน่นอน 3 โค้ด ยอดโค้ดราคาสุ่ม 10-50 ต่อโค้ด ไม่มีจำกัดเวลายิงให้จนครบ 3 โค้ดตามจำนวน', 35, 0, 3, 2, '/images/procodeAi.png', 't'),
(5, 'แพ็กเกจประกันราคา 3 โค้ด (ประกันยอดโค้ดราคา 15 ไม่มีขาดทุน)', 'ได้แน่นอน 3 โค้ด ประกันยอดยอดโค้ดราคา 15 บาทขึ้นไป ยอดรับประกันราคารวม 3 โค้ด 45 บาทขึ้นไป ไม่มีจำกัดเวลายิงให้จนครบ 3 โค้ดตามจำนวน', 40, 0, 3, 2, '/images/procodeAi.png', 't'),
(6, 'แพ็กเกจประกันราคา 5 โค้ด (ประกันยอดโค้ดราคา 15 ไม่มีขาดทุน)', 'ได้แน่นอน 5 โค้ด ประกันยอดยอดโค้ดราคา 15 บาทขึ้นไป ยอดรับประกันราคารวม 5 โค้ด 75 บาทขึ้นไป ไม่มีจำกัดเวลายิงให้จนครบ 5 โค้ดตามจำนวน', 80, 70, 5, 2, '/images/procodeAi.png', 't'),
(7, 'แพ็กเกจประกันราคา 5 โค้ด (ประกันยอดโค้ดราคา 20 ไม่มีขาดทุน)', 'ได้แน่นอน 5 โค้ด ประกันยอดโค้ดราคา 20 บาทขึ้นไป ยอดรับประกันราคารวม 5 โค้ด 100 บาทขึ้นไป ไม่มีจำกัดเวลายิงให้จนครบ 5 โค้ดตามจำนวน', 100, 90, 5, 2, '/images/procodeAi.png', 't'),
(8, 'แพ็กเกจสุ่มราคา 7 โค้ด (ไม่มีขาดทุน)', 'ได้แน่นอน 7 โค้ด ยอดโค้ดราคาสุ่ม 10-50 ต่อโค้ด ไม่มีจำกัดเวลายิงให้จนครบ 7 โค้ดตามจำนวน', 100, 0, 7, 2, '/images/procodeAi.png', 't'),
(9, 'แพ็กเกจประกันราคา 10 โค้ด (ประกันยอดโค้ดราคา 15 ไม่มีขาดทุน)', 'ได้แน่นอน 10 โค้ด ประกันยอดยอดโค้ดราคา 15 บาทขึ้นไป ยอดรับประกันราคารวม 10 โค้ด 150 บาทขึ้นไป ไม่มีจำกัดเวลายิงให้จนครบ 10 โค้ดตามจำนวน', 159, 139, 10, 2, '/images/procodeAi.png', 't');


INSERT INTO "public"."players" ("id", "username", "site_id", "first_name", "last_name", "phone", "email", "is_active", "is_unlimited_code", "telegram_id") VALUES
(1, 'nus9331', 1, NULL, NULL, NULL, NULL, 't', 't', NULL),
(2, 'manus9331', 1, NULL, NULL, NULL, NULL, 't', 't', NULL),
(3, 'Preechar', 1, NULL, NULL, NULL, NULL, 't', 't', NULL),
(4, 'nus9331', 2, NULL, NULL, NULL, NULL, 't', 't', NULL),
(5, 'aroon11', 2, NULL, NULL, NULL, NULL, 't', 't', NULL),
(6, 'manus9331', 2, NULL, NULL, NULL, NULL, 't', 't', NULL),
(7, 'wat3366', 2, NULL, NULL, NULL, NULL, 't', 't', NULL),
(8, 'koonogk', 2, NULL, NULL, NULL, NULL, 't', 't', NULL);


INSERT INTO "public"."site_player_tiers" ("id", "site_id", "player_id", "tier_id") VALUES
(1, 1, 1, 1),
(2, 1, 2, 1),
(3, 1, 1, 2),
(4, 1, 2, 2),
(5, 1, 3, 3),
(6, 1, 3, 4),
(7, 2, 4, 1),
(8, 2, 5, 1),
(9, 2, 6, 1),
(10, 2, 5, 2),
(11, 2, 6, 2),
(12, 2, 4, 2),
(13, 2, 7, 3),
(14, 2, 8, 3),
(15, 2, 7, 4),
(16, 2, 8, 4),
(17, 2, 7, 5),
(18, 2, 8, 5);
INSERT INTO "public"."sites" ("id", "site_key", "name") VALUES
(1, 'thai_789bet', 'Thai 789Bet'),
(2, 'thai_jun88k36', 'Thai JUN88K36');
INSERT INTO "public"."tiers" ("id", "name") VALUES
(1, 'very_high'),
(2, 'high'),
(3, 'mid'),
(4, 'low'),
(5, 'all');

