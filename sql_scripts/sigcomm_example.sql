----------------------------------------------------------------------
-- merlin, kinetic, PGA
----------------------------------------------------------------------

DROP TABLE IF EXISTS Merlin_policy CASCADE;
CREATE UNLOGGED TABLE MERLIN_policy (
       fid	      integer,
       rate 	      integer,
       PRIMARY key (fid)
);

CREATE OR REPLACE VIEW MERLIN_violation AS (
       SELECT tm.fid, rate AS req, vol AS asgn
       FROM tm, Merlin_policy
       WHERE tm.fid = Merlin_policy.fid AND rate > vol
);

CREATE OR REPLACE RULE Merlin_repair AS
       ON DELETE TO Merlin_violation
       DO INSTEAD
              UPDATE tm SET vol = OLD.req WHERE fid = OLD.fid;

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

DROP VIEW IF EXISTS PGA CASCADE;
CREATE OR REPLACE VIEW PGA AS(
       WITH PGA_group_policy AS (
       	    SELECT p1.sid_array AS sa1,
       	      	   p2.sid_array AS sa2, MB
            FROM PGA_group p1, PGA_group p2, PGA_policy
       	    WHERE p1.gid = gid1 AND p2.gid = gid2),
       PGA_group_policy2 AS (
            SELECT unnest (sa1)"sid1", sa2, MB
	    FROM PGA_group_policy)
       SELECT sid1, unnest (sa2)"sid2", MB
       FROM  PGA_group_policy2
);

CREATE OR REPLACE VIEW PGA_violation AS (
       SELECT fid, MB
       FROM tm, PGA       
       WHERE src = sid1 AND dst = sid2 AND
       ((MB = 'FW' AND FW=0) OR (MB='LB' AND LB=0)) 
);

CREATE OR REPLACE RULE PGA_repair AS
       ON DELETE TO PGA_violation
       DO INSTEAD
       (
       UPDATE tm SET FW = 1 WHERE fid = OLD.fid AND OLD.MB = 'FW';
       UPDATE tm SET LB = 1 WHERE fid = OLD.fid AND OLD.MB = 'LB';
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

CREATE OR REPLACE VIEW FW_violation AS (
       SELECT fid
       FROM tm, FW_policy_acl     
       WHERE FW = 1 AND 
       	     (src, dst) NOT IN (SELECT end1, end2 FROM FW_policy_acl)
);

CREATE OR REPLACE RULE FW_repair AS
       ON DELETE TO FW_violation
       DO INSTEAD
       	  DELETE FROM tm WHERE fid = OLD.fid;

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

----------------------------------------------------------------------
-- orchestrating Merlin, Kinetic, PGA
----------------------------------------------------------------------

DROP TABLE IF EXISTS p_PGA CASCADE;
CREATE UNLOGGED TABLE p_PGA (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);

CREATE OR REPLACE RULE run_PGA AS
       ON INSERT TO p_PGA
       WHERE (NEW.status = 'on')
       DO ALSO (
           DELETE FROM PGA_violation;
	   UPDATE p_PGA SET status = 'off' WHERE counts = NEW.counts;
	  );


DROP TABLE IF EXISTS p_FW CASCADE;
CREATE UNLOGGED TABLE p_FW (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);

CREATE OR REPLACE RULE run_FW AS
       ON INSERT TO p_FW
       WHERE (NEW.status = 'on')
       DO ALSO (
           DELETE FROM FW_violation;
	   UPDATE p_FW SET status = 'off' WHERE counts = NEW.counts;
	  );


DROP TABLE IF EXISTS p_Merlin CASCADE;
CREATE UNLOGGED TABLE p_Merlin (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);

CREATE OR REPLACE RULE run_Merlin AS
       ON INSERT TO p_Merlin
       WHERE (NEW.status = 'on')
       DO ALSO (
           DELETE FROM FW_violation;
	   UPDATE p_Merlin SET status = 'off' WHERE counts = NEW.counts;
	  );

----------------------------------------------------------------------
-- implement a total order
----------------------------------------------------------------------

CREATE OR REPLACE RULE PGA2FW AS
       ON UPDATE TO p_PGA
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO p_FW values (NEW.counts, 'on');

CREATE OR REPLACE RULE FW2Merlin AS
       ON UPDATE TO p_FW
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO p_Merlin values (NEW.counts, 'on');

CREATE OR REPLACE RULE Merlin2c AS
       ON UPDATE TO p_Merlin
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO clock values (NEW.counts);
