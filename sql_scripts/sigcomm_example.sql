----------------------------------------------------------------------
-- merlin, kinetic, PGA
----------------------------------------------------------------------

----------------------------------------------------------------------
-- PGA (endpoints, service chain)
----------------------------------------------------------------------

DROP TABLE IF EXISTS PGA_policy CASCADE;
CREATE UNLOGGED TABLE PGA_policy (
       gid1	      integer,
       gid2 	      integer,
       MB	      text,
       PRIMARY key (gid1, gid2)		
);
CREATE INDEX ON PGA_policy (gid1, gid2);

DROP TABLE IF EXISTS PGA_group CASCADE;
CREATE UNLOGGED TABLE PGA_group (
       gid	      integer,
       sid_array      integer[],
       PRIMARY key (gid)
);
CREATE INDEX ON PGA_group (gid);

CREATE OR REPLACE VIEW PGA AS(
       WITH TMP AS (
       	    SELECT gid1 AS gid, sid_array AS sid_array2, MB
	    FROM PGA_policy, PGA_group
	    WHERE gid2 = gid
       )
       SELECT unnest(sid_array)"sid1" , unnest(sid_array2)"sid2", MB
       FROM TMP, PGA_group WHERE TMP.gid = PGA_group.gid
);

CREATE OR REPLACE VIEW PGA_violation AS (
       SELECT fid, MB
       FROM tm, PGA       
       WHERE src = sid1 AND dst = sid2 AND
       ((MB = 'FW' AND FW=0) OR (MB='LB' AND LB=0)) 
);

----------------------------------------------------------------------
-- kinetic (stateful firewall)
----------------------------------------------------------------------
DROP TABLE IF EXISTS FW_policy_acl CASCADE;
CREATE UNLOGGED TABLE FW_policy_acl (
       end1	      integer,
       end2 	      integer,
       allow	      integer,
       PRIMARY key (end1, end2)		
);
CREATE INDEX ON FW_policy_acl (end1,end2);

DROP TABLE IF EXISTS FW_policy_user CASCADE;
CREATE UNLOGGED TABLE FW_policy_user (
       uid	      integer
);

CREATE OR REPLACE RULE FW1 AS
       ON INSERT TO tm
       WHERE ((NEW.src, NEW.dst) NOT IN (SELECT end2, end1 FROM FW_policy_acl)) AND 
       	      (NEW.src IN (SELECT * FROM FW_policy_user))
       DO ALSO (
       	  INSERT INTO FW_policy_acl VALUES (NEW.dst, NEW.src, 1);
       );

CREATE OR REPLACE RULE FW2 AS
       ON DELETE TO tm
       WHERE (SELECT count(*) FROM tm WHERE src = OLD.src AND dst = OLD.dst) = 1
       DO ALSO 
       	  DELETE FROM FW_policy_acl WHERE end2 = OLD.src AND end1 = OLD.dst;

-- CREATE OR REPLACE RULE acl2utm AS
--        ON UPDATE TO acl
--        DO INSTEAD
--        	  DELETE FROM utm WHERE host1 = NEW.end1 AND host2 = NEW.end2;

----------------------------------------------------------------------
-- Merlin
----------------------------------------------------------------------
-- 
-- DROP TABLE IF EXISTS tm_delta CASCADE;
-- CREATE UNLOGGED TABLE tm_delta (
--        fid      integer,
--        src	integer,
--        dst	integer,
--        vol	integer,
--        FW	integer,
--        LB	integer,       
--        isadd	integer
-- );
-- CREATE INDEX ON tm_delta (fid,src,dst);

INSERT INTO PGA_policy (gid1, gid2, MB)
VALUES (1,2,'FW'),
       (4,3,'LB');

INSERT INTO PGA_group 
       (gid, sid_array)
VALUES
	(1, ARRAY[5]),
	(2, ARRAY[6]),
	(3, ARRAY[6,7]),
	(4, ARRAY[5,8]);

INSERT INTO FW_policy_user VALUES (5),(8);



-- CREATE OR REPLACE FUNCTION protocol_fun() RETURNS TRIGGER AS
-- $$
-- plpy.notice ("engage ravel protocol")

-- ct = plpy.execute("""select max (counts) from clock""")[0]['max']
-- plpy.execute ("INSERT INTO p_spv VALUES (" + str (ct+1) + ", 'on');")
-- return None;
-- $$
-- LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

-- CREATE TRIGGER tp_up_trigger
--      AFTER UPDATE ON tp
--      FOR EACH ROW
--    EXECUTE PROCEDURE protocol_fun();

-- CREATE OR REPLACE VIEW acl AS(
--        -- SELECT DISTINCT fid, end1, end2, allow
--        SELECT DISTINCT fid, allow
--        FROM acl_policy, tm
--        WHERE  src = end1 AND dst = end2 and allow = 0
-- );
