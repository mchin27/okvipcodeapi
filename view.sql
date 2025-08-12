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
        ), eligible_usernames AS (
         SELECT DISTINCT p_1.username
           FROM players p_1
          WHERE ((p_1.is_active = true) AND (NOT (p_1.id IN ( SELECT current_locks.player_id
                   FROM current_locks))) AND (NOT (p_1.id IN ( SELECT todays_applies.player_id
                   FROM todays_applies))) AND ((p_1.is_unlimited_code = true) OR (p_1.id IN ( SELECT active_packages.player_id
                   FROM active_packages))))
        )
 SELECT p.username,
    string_agg(DISTINCT s.site_key, ', '::text ORDER BY s.site_key) AS site_keys,
    string_agg(DISTINCT t.name, ', '::text ORDER BY t.name) AS tiers
   FROM (((players p
     JOIN sites s ON ((s.id = p.site_id)))
     JOIN site_player_tiers spt ON ((spt.player_id = p.id)))
     JOIN tiers t ON ((spt.tier_id = t.id)))
  WHERE (p.username IN ( SELECT eligible_usernames.username
           FROM eligible_usernames))
  GROUP BY p.username;


