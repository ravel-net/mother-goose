DROP TABLE IF EXISTS PGA_t CASCADE;
DROP TABLE IF EXISTS PGA_table CASCADE;
DROP VIEW IF EXISTS PGA_t_view CASCADE;



CREATE TABLE PGA_t AS(
	SELECT p1.sid_array AS sa1,
	       p2.sid_array AS sa2, MB
	FROM PGA_group p1, PGA_group p2, PGA_policy
	WHERE p1.gid = gid1 AND p2.gid = gid2	 
);

CREATE OR REPLACE FUNCTION f_policy()
RETURNS TRIGGER AS
$$
if(TD["event"] == "INSERT"):
	new_gid1 = TD["new"]["gid1"]
	new_gid2 = TD["new"]["gid2"]
	new_MB = TD["new"]["mb"]
	sa1 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(new_gid1))
	sa2 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(new_gid2))
	if(sa1.nrows()!=0 and sa2.nrows()!=0):
		sa1_str = "ARRAY"+ str(sa1[0]["sid_array"])
		sa2_str = "ARRAY"+ str(sa2[0]["sid_array"])
		plpy.execute("INSERT INTO PGA_t VALUES("+ sa1_str+ ", "+ sa2_str+ ", '"+ str(new_MB)+ "');")

if(TD["event"] == "DELETE"):
	old_gid1 = TD["old"]["gid1"]
        old_gid2 = TD["old"]["gid2"]
        old_MB = TD["old"]["mb"]
	sa1 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(old_gid1))
	sa2 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(old_gid2))
	plpy.execute("DELETE FROM PGA_t WHERE sa1 = ARRAY"+ str(sa1[0]["sid_array"])+ " and sa2 = ARRAY"+ str(sa2[0]["sid_array"]))
if(TD["event"] == "UPDATE"):
	old_gid1 = TD["old"]["gid1"]
        old_gid2 = TD["old"]["gid2"]
        old_MB = TD["old"]["mb"]  
	new_gid1 = TD["new"]["gid1"]
        new_gid2 = TD["new"]["gid2"]
        new_MB = TD["new"]["mb"]
	old_sa1 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(old_gid1))
        old_sa2 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(old_gid2))
	plpy.execute("DELETE FROM PGA_t WHERE sa1 = ARRAY"+ str(sa1[0]["sid_array"])+ " and sa2 = ARRAY"+ str(sa2[0]["sid_array"]))
	sa1 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(new_gid1))
        sa2 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(new_gid2))
        if(sa1.nrows()!=0 and sa2.nrows()!=0):
                sa1_str = "ARRAY"+ str(sa1[0]["sid_array"])
                sa2_str = "ARRAY"+ str(sa2[0]["sid_array"])
                plpy.execute("INSERT INTO PGA_t VALUES("+ sa1_str+ ", "+ sa2_str+ ", '"+ str(new_MB)+ "');")
return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER t_policy
	BEFORE INSERT OR DELETE OR UPDATE ON PGA_policy
	FOR EACH ROW
EXECUTE PROCEDURE f_policy();

CREATE OR REPLACE FUNCTION f_group()
RETURNS TRIGGER AS
$$
if(TD["event"] == "INSERT"):
	new_gid = TD["new"]["gid"]
	new_sa = TD["new"]["sid_array"]
	r_gid1 = plpy.execute("SELECT * FROM PGA_policy WHERE gid1 = "+ str(new_gid))
	if(r_gid1.nrows()!=0):
		r_other = plpy.execute("SELECT * FROM PGA_group WHERE gid = "+ str(r_gid1[0]["gid2"]))
		if(r_other.nrows()!= 0):
			plpy.execute("INSERT INTO PGA_t VALUES(ARRAY"+ str(new_sa)+ ", ARRAY"+ str(r_other[0]["sid_array"])+ ", '"+ str(r_gid1[0]["mb"])+ "')")
	r_gid2 = plpy.execute("SELECT * FROM PGA_policy WHERE gid2 = "+ str(new_gid))
	if(r_gid2.nrows()!=0):
        	r_other2 = plpy.execute("SELECT * FROM PGA_group WHERE gid = "+ str(r_gid1[0]["gid1"]))
        	if(r_other2.nrows()!= 0):
                	plpy.execute("INSERT INTO PGA_t VALUES(ARRAY"+ str(new_sa)+ ", ARRAY"+ str(r_other2[0]["sid_array"])+ ", '"+ str(r_gid2[0]["MB"])+ "')")

if(TD["event"] == "DELETE"):
        old_gid = TD["old"]["gid"]
        old_sa = TD["old"]["sid_array"]
	plpy.execute("DELETE FROM PGA_t WHERE sa1 = ARRAY"+str(old_sa)+ "or sa2 = ARRAY"+ str(old_sa))

if(TD["event"] == "UPDATE"):
	new_gid = TD["new"]["gid"]
        new_sa = TD["new"]["sid_array"]
	old_gid = TD["old"]["gid"]
        old_sa = TD["old"]["sid_array"]
	r_gid1 = plpy.execute("SELECT * FROM PGA_policy WHERE gid1 = "+ str(new_gid))
        if(r_gid1.nrows()!=0):
                r_other = plpy.execute("SELECT * FROM PGA_group WHERE gid = "+ str(r_gid1[0]["gid2"]))
                if(r_other.nrows()!= 0):
                        plpy.execute("INSERT INTO PGA_t VALUES(ARRAY"+ str(new_sa)+ ", ARRAY"+ str(r_other[0]["sid_array"])+ ", '"+ str(r_gid1[0]["mb"])+ "')")
        r_gid2 = plpy.execute("SELECT * FROM PGA_policy WHERE gid2 = "+ str(new_gid))
        if(r_gid2.nrows()!=0):
                r_other2 = plpy.execute("SELECT * FROM PGA_group WHERE gid = "+ str(r_gid1[0]["gid1"]))
                if(r_other2.nrows()!= 0):
                        plpy.execute("INSERT INTO PGA_t VALUES(ARRAY"+ str(new_sa)+ ", ARRAY"+ str(r_other2[0]["sid_array"])+ ", '"+ str(r_gid2[0]["MB"])+ "')")
	plpy.execute("DELETE FROM PGA_t WHERE sa1 = ARRAY"+str(old_sa)+ "or sa2 = ARRAY"+ str(old_sa))

return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER t_group
	AFTER INSERT OR DELETE OR UPDATE ON PGA_group
	FOR EACH ROW
EXECUTE PROCEDURE f_group();

CREATE VIEW PGA_t_view AS(
	WITH PGA_t_2 AS(
	  SELECT unnest (sa1)"sid1", sa2, MB
	  FROM PGA_t)
	SELECT sid1, unnest (sa2)"sid2", MB
	FROM PGA_t_2
);

CREATE TABLE PGA_table AS
	SELECT sid1, sid2, MB, count(*) AS n
	FROM PGA_t_view
	GROUP BY sid1, sid2, MB
;



CREATE OR REPLACE FUNCTION f_unnest() 
RETURNS TRIGGER AS
$$
if(TD["event"] == "INSERT"):
	new_sa1q = TD["new"]["sa1"]
	new_sa2q = TD["new"]["sa2"]
	new_mbq = TD["new"]["mb"]
	for i in new_sa1q:
		for j in new_sa2q:
			f = plpy.execute("SELECT * FROM PGA_table WHERE sid1 = "+ str(i)+ " and sid2 = "+ str(j) +" and mb='" + str(new_mbq)+"'")
			if(f.nrows()!=0):
				plpy.execute("UPDATE PGA_table SET n = n+1 WHERE sid1 = "+str(i) + " and sid2 = "+ str(j)+" and mb='" + str(new_mbq)+"'")
			else:
				plpy.execute("INSERT INTO PGA_table VALUES("+ str(i)+ ", "+ str(j)+", '"+ str(new_mbq) + "', 1)")
	
if(TD["event"] == "DELETE"):
	old_sa1q = TD["old"]["sa1"]
	old_sa2q = TD["old"]["sa2"]
	old_mbq = TD["old"]["mb"]
	for i in old_sa1q:
		for j in old_sa2q:
			plpy.execute("UPDATE PGA_table SET n = n - 1 WHERE sid1 = "+str(i) + " and sid2 = "+ str(j)+" and mb='" + str(old_mbq)+"'")
				
	plpy.execute("DELETE FROM PGA_table WHERE n = 0")

if(TD["event"] == "UPDATE"):
	old_sa1q = TD["old"]["sa1"]
        old_sa2q = TD["old"]["sa2"]
        old_mbq = TD["old"]["mb"]
        for i in old_sa1q:
                for j in old_sa2q:
                        plpy.execute("UPDATE PGA_table SET n = n - 1 WHERE sid1 = "+str(i) + " and sid2 = "+ str(j)+" and mb='" + str(old_mbq)+"'")
	plpy.execute("DELETE FROM PGA_table WHERE n = 0")
        new_sa1q = TD["new"]["sa1"]
        new_sa2q = TD["new"]["sa2"]
        new_mbq = TD["new"]["mb"]
        for i in new_sa1q:
                for j in new_sa2q:
                        f = plpy.execute("SELECT * FROM PGA_table WHERE sid1 = "+ str(i)+ " and sid2 = "+ str(j)+" and mb='" + str(new_mbq)+"'")
                        if(f.nrows()!=0):
                                plpy.execute("UPDATE PGA_table SET n = n+1 WHERE sid1 = "+str(i) + " and sid2 = "+ str(j)+" and mb='" + str(new_mbq)+"'")
                        else:
                                plpy.execute("INSERT INTO PGA_table VALUES("+ str(i)+ ", "+ str(j)+", '"+ str(new_mbq) + "', 1)")



return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER t_unnest
	AFTER INSERT OR DELETE OR UPDATE ON PGA_t
	FOR EACH ROW
EXECUTE PROCEDURE f_unnest();











