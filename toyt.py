execfile("libRavel.py")
import libRavel
from batch import Batch

class Toyt (Batch):

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

    def protocol (self):
        
        self.cur.execute ("select max (counts) from clock;")
        ct = self.cur.fetchall () [0]['max']
        print 'clock tick now: ' + str (ct) 
        self.cur.execute ("INSERT INTO p_PGA VALUES (" + str (ct+1) + ", 'on');")

    def fetch (self):
        Batch.fetch (self)

        self.cur.execute ("SELECT * FROM tm;")
        cs = self.cur.fetchall ()
        self.tm = [[h['fid'], h['src'], h['dst'], h['vol'], h['fw'], h['lb']] for h in cs]

        
    def add_flow (self, src, dst):
        Batch.update_max_fid(self)

        self.cur.execute ("INSERT INTO tm(fid,src,dst,vol,FW,LB) VALUES (%s,%s,%s,%s,%s,%s);", 
                          ([self.max_fid +1, src, dst, 0, 0, 0]))

    def add_flow_orchestrated (self, src, dst):
        self.add_flow (src, dst)
        self.protocol ()
        
    def del_flow (self, fid):
        self.cur.execute ("DELETE FROM tm WHERE fid = %s;", ([fid]))

    def del_flow_orchestrated (self, fid):
        self.del_flow (fid)
        self.protocol ()

    def load_topo (self):
        self.cur.execute ("""
            TRUNCATE TABLE tp cascade;
            TRUNCATE TABLE cf cascade;
            TRUNCATE TABLE tm cascade;
            INSERT INTO switches(sid) VALUES (1),(2),(3),(4);
            INSERT INTO hosts(hid) VALUES (5),(6),(7),(8);
            INSERT INTO tp(sid, nid, ishost, isactive, bw) VALUES (1,5,1,1,5), (2,6,1,1,5), (3,7,1,1,5), (4,8,1,1,5);
            INSERT INTO tp(sid, nid, ishost, isactive, bw) VALUES (1,2,0,1,5), (2,3,0,1,5), (3,4,0,1,5),(4,1,0,1,5);
    """)

        # self.cur.execute ("UPDATE tp SET bw = 5;")
        
        self.database_new = 0
        print "--------------------> load_topo4switch successful"

    def load_sig_example_schema (self):
        sql_script = '/home/mininet/ravel/xym/sigcomm_with_trg.sql'
        Batch.load_schema(self, sql_script)

    def close (self):
        Batch.close (self)


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
