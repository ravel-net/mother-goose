DROP TABLE IF EXISTS lb_m CASCADE;
DROP TRIGGER IF EXISTS utm_1 ON utm;
DROP TRIGGER IF EXISTS lb_tb_1 ON lb_tb;

---CREATE TABLE lb_m AS 
---SELECT sid, count(*) AS load
---FROM lb_tb, utm
---WHERE lb_tb.sid = utm.host2
---GROUP BY sid;

CREATE TABLE lb_m AS(
	SELECT sid,
		(SELECT count(*) FROM utm
		 WHERE host2 = sid) AS load
	FROM lb_tb
	);


CREATE OR REPLACE FUNCTION r_1()
RETURNS TRIGGER AS
$$
if(TD["event"] == "INSERT"):
	new_host2 = TD["new"]["host2"]
	m_row = plpy.execute("SELECT * FROM lb_tb WHERE sid ="+ str(new_host2))
	#if(m_row.nrows() ==0):
		#plpy.execute("INSERT INTO lb_m VALUES ("+ str(new_host2)+ ", 1);")
	#else:
	if(m_row.nrows() != 0):
		plpy.execute("UPDATE lb_m SET load = load + 1 WHERE sid = "+ str(new_host2) + ";")

if(TD["event"] == "DELETE"):
	old_host2 = TD["old"]["host2"]
	plpy.execute("UPDATE lb_m SET load = load - 1 WHERE sid = "+ str(old_host2) + ";")
	#plpy.execute("delete from lb_m where load = 0;")
	

return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;



CREATE TRIGGER utm_1
	BEFORE INSERT OR DELETE ON utm
	FOR EACH ROW
EXECUTE PROCEDURE r_1();


CREATE OR REPLACE FUNCTION r_2()
RETURNS TRIGGER AS
$$
if(TD["event"] == "DELETE"):
	old_sid = TD["old"]["sid"]
	plpy.execute("DELETE FROM lb_m WHERE sid ="+ str(old_sid)+ ";")

if(TD["event"] == "INSERT"):
	new_sid = TD["new"]["sid"]
	res = plpy.execute("SELECT * FROM utm WHERE host2 = "+ str(new_sid)+ ";")
	count = res.nrows()
	plpy.execute("INSERT INTO lb_m VALUES(" + str(new_sid)+ ", " + str(count)+ ");")
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER lb_tb_1
	BEFORE INSERT OR DELETE ON lb_tb
	FOR EACH ROW
EXECUTE PROCEDURE r_2();



