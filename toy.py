execfile("libRavel.py")
import libRavel
from batch import Batch

class Toy (Batch):

    def __init__(self,dbname, rounds):

        sql_script = "/home/mininet/ravel/sql_scripts/primitive.sql"
        topology = 'toy'

        self.dbname = dbname
        self.create_db (sql_script)
        Batch.connect (self)

        self.load_schema (sql_script)        
        self.load_sig_example_schema ()
        self.load_topo ()

        Batch.__init__(self, dbname, rounds, sql_script, topology)

        self.profile = False

    def fetch (self):
        Batch.fetch (self)

        self.cur.execute ("SELECT * FROM tm;")
        cs = self.cur.fetchall ()
        self.tm = [[h['fid'], h['src'], h['dst'], h['vol'], h['FW'], h['LB']] for h in cs]

        
    def add_flow (self, src, dst):
        Batch.update_max_fid(self)

        self.cur.execute ("INSERT INTO tm(fid,src,dst,vol,FW,LB) VALUES (%s,%s,%s,%s,%s,%s);", 
                          ([self.max_fid +1, src, dst, 1, 0, 0]))

    def del_flow (self, fid):
        self.cur.execute ("DELETE FROM tm WHERE fid = %s;", ([fid]))

    def load_topo (self):
        self.cur.execute ("""
            TRUNCATE TABLE tp cascade;
            TRUNCATE TABLE cf cascade;
            TRUNCATE TABLE tm cascade;
            INSERT INTO switches(sid) VALUES (1),(2),(3),(4);
            INSERT INTO hosts(hid) VALUES (5),(6),(7),(8);
            INSERT INTO tp(sid, nid, ishost, isactive) VALUES (1,5,1,1), (2,6,1,1), (3,7,1,1), (4,8,1,1);
            INSERT INTO tp(sid, nid, ishost, isactive) VALUES (1,2,0,1), (2,3,0,1), (3,4,0,1),(4,1,0,1);
    """)

        self.cur.execute ("UPDATE tp SET bw = 5;")

        # self.cur.
#         self.cur.execute ("""
# INSERT INTO PGA_policy (gid1, gid2, MB)
# VALUES (1,2,'FW'),
#        (4,3,'LB');

# INSERT INTO PGA_group 
#        (gid, sid_array)
# VALUES
# 	(1, ARRAY[5]),
# 	(2, ARRAY[6]),
# 	(3, ARRAY[6,7]),
# 	(4, ARRAY[5,8]);
#         """)
        
        self.database_new = 0
        print "--------------------> load_topo4switch successful"

    def load_sig_example_schema (self):
        sql_script = '/home/mininet/ravel/sql_scripts/sigcomm_example.sql'
        Batch.load_schema(self, sql_script)

    def close (self):
        Batch.close (self)

