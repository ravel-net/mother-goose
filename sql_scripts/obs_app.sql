----------------------------------------------------------------------
-- obs application
----------------------------------------------------------------------

CREATE OR REPLACE VIEW obs AS (
       SELECT  fid, dst as nid, vol as rate
       FROM tm
       WHERE src < 20
);

CREATE OR REPLACE RULE obs_in AS 
       ON INSERT TO obs
       DO INSTEAD
       	  INSERT INTO tm VALUES (NEW.fid,5,NEW.nid,1);

CREATE OR REPLACE RULE obs_del AS 
       ON DELETE TO obs
       DO INSTEAD
          DELETE from tm WHERE fid = OLD.fid ;

CREATE RULE obs_constaint AS
       ON INSERT TO p1
       WHERE NEW.status = 'on'
       DO ALSO
           UPDATE p1 SET status = 'off' WHERE counts = NEW.counts;

----------------------------------------------------------------------
-- recursive views on top of obs	   
----------------------------------------------------------------------

DROP TABLE IF EXISTS o1 CASCADE;
CREATE UNLOGGED TABLE o1 (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);
-- INSERT into o1 (counts) values (0) ;

DROP TABLE IF EXISTS o2 CASCADE;
CREATE UNLOGGED TABLE o2 (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);
-- INSERT into o2 (counts) values (0) ;

CREATE OR REPLACE RULE otick1 AS
       ON UPDATE TO o1
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO o2 values (NEW.counts, 'on');

CREATE OR REPLACE RULE otick2 AS
       ON UPDATE TO o2
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO p1 values (NEW.counts, 'on');

CREATE OR REPLACE VIEW obs_acl AS (
       SELECT DISTINCT nid as dst
       FROM obs
);

CREATE OR REPLACE RULE obs_acl_del AS 

       ON DELETE TO obs_acl
       DO INSTEAD
	  DELETE from obs WHERE nid = OLD.dst;

CREATE OR REPLACE RULE obs_acl_constraint AS
       ON INSERT TO o2
       WHERE NEW.status = 'on'
       DO ALSO
       	  (DELETE FROM obs_acl WHERE (dst = 30 OR dst = 50 OR dst = 100) ;
	   UPDATE o2 SET status = 'off' WHERE counts = NEW.counts;
	  );

CREATE OR REPLACE VIEW obs_lb AS (
       SELECT nid, sum (rate) as sum_rate
       FROM obs
       GROUP BY nid
);

CREATE OR REPLACE RULE obs_lb_del AS
       ON DELETE TO obs_lb
       DO INSTEAD
	  DELETE from obs WHERE fid IN
	  	 (SELECT fid FROM obs
		  WHERE nid = OLD.nid
		  ORDER BY rate	  
		  LIMIT 1
		 );

----------------------------------------------------------------------
-- acl, view and rules
----------------------------------------------------------------------

CREATE OR REPLACE VIEW acl AS (
       SELECT DISTINCT src, dst
       FROM tm
);

CREATE OR REPLACE RULE acl_in AS
       ON INSERT TO acl
       DO INSTEAD
       	  INSERT INTO tm VALUES ((SELECT max (fid) FROM tm) + 1 , NEW.src, NEW.dst, 2);
	  	 
CREATE OR REPLACE RULE acl_del AS
       ON DELETE TO acl
       DO INSTEAD
       	  DELETE from tm WHERE src = OLD.src AND dst = OLD.dst;

CREATE OR REPLACE RULE acl_constaint AS
       ON INSERT TO p2
       WHERE NEW.status = 'on'
       DO ALSO
           (DELETE FROM tm WHERE (src = 1 AND dst = 2);
	    DELETE FROM tm WHERE (src = 7 AND dst = 8);
            UPDATE p2 SET status = 'off' WHERE counts = NEW.counts;
	    );

CREATE OR REPLACE RULE acl_constaint2 AS
       ON INSERT TO acl
       DO ALSO
           (DELETE FROM acl WHERE (src = 5 AND dst = 10);
	    DELETE FROM acl WHERE (src = 7 AND dst = 8);
	    );

----------------------------------------------------------------------
-- tenants
----------------------------------------------------------------------

-- DROP TABLE IF EXISTS tenant_hosts CASCADE;
-- CREATE UNLOGGED TABLE tenant_hosts (
--        hid	integer,
--        PRIMARY key (hid)
-- );

-- CREATE OR REPLACE VIEW tenant_policy AS (
--        SELECT DISTINCT host1, host2 FROM utm
--        WHERE host1 IN (SELECT * FROM tenant_hosts)
--        	     AND host2 IN (SELECT * FROM tenant_hosts)
-- );

-- CREATE OR REPLACE RULE tenant_policy_ins AS
--        ON INSERT TO tenant_policy
--        DO INSTEAD
--        INSERT INTO utm (fid, host1, host2) values ((select max (counts) + 1 from clock), NEW.host1, NEW.host2);

-- CREATE OR REPLACE RULE tenant_policy_del AS
--        ON DELETE TO tenant_policy
--        DO INSTEAD
--        DELETE FROM utm WHERE host1 = OLD.host1 AND host2 = OLD.host2;
