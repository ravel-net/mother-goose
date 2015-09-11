execfile("libRavel.py")
import libRavel
from batch import Batch

class Batch_isp (Batch):

    def __init__(self, dbname, rounds):

        isp = dbname[3:7]
        self.isp = isp
        self.ISP_edges_file = os.getcwd () + '/ISP_topo/'+str (isp) +'_edges.txt'
        self.ISP_nodes_file = os.getcwd () + '/ISP_topo/'+str (isp)+'_nodes.txt'
        self.rib_prefixes_file = os.getcwd() + '/rib_feeds/' + "rib20011204_prefixes.txt"
        self.rib_peerIPs_file = os.getcwd() + '/rib_feeds/' + "rib20011204_nodes.txt"

        print "for database " + dbname + "--------------------"
        create_db (dbname, Batch.username) # add comments

        if database_exists == 0:
            add_pgrouting_plpy_plsh_extension (dbname, Batch.username)
            load_schema (dbname, Batch.username, "/home/mininet/ravel/sql_scripts/primitive.sql")
            Batch_isp.init_ISP_topo (self, dbname)

        Batch.__init__(self,dbname, rounds)
        remove_profile_schema (self.cur)

        rib_feeds_all = os.getcwd() + '/rib_feeds/rib20011204_edges.txt'
        if database_exists == 0:
            feeds = dbname[8:]
            self.rib_edges_file = os.getcwd() + '/rib_feeds/rib20011204_edges_' + str (feeds) + '.txt'
            os.system ("head -n " + str(feeds) + " " + rib_feeds_all + " > " + self.rib_edges_file)

        elif database_exists == 1:
            cur = Batch.self.cur
            t_feeds = cur.execute ("SELECT count (*) FROM utm;").fetchall ()[0]['count']
            feeds = int (dbname[8:]) - int (t_feeds)

            Batch.update_max_fid (self)
            fid = self.max_fid + 1



        Batch_isp.init_rib (self)

    def close (self):
        os.system ("cp "+ Batch.logfile + ' ' + self.logdest)

        if self.isp == '4755' or self.isp == '3356' or self.isp == '7018':
            t = 'isp_3sizes'
        elif self.isp == '2914':
            t = 'isp' + self.isp + '_3ribs'

        if self.profile == True:
            os.system ("sudo mv "+ self.logdest + ' ' + ' /media/sf_share/ravel_plot/profile/log/')
        else:
            os.system ("sudo mv "+ self.logdest + ' ' + ' /media/sf_share/ravel_plot/' + t + '/log/')

        Batch.close (self)

    def primitive (self):
        Batch.init_acl (self)
        Batch.init_lb (self)
        Batch.op_primitive (self)

    def init_ISP_topo (self, dbname):

        def init_topology (cursor):
            ISP_edges_file = self.ISP_edges_file
            ISP_nodes_file = self.ISP_nodes_file
            f = open (ISP_edges_file, "r").readlines ()

            for edge in f:
                ed = edge[:-1].split()
                try:
                    cursor.execute("""INSERT INTO tp(sid, nid, ishost,isactive) VALUES (%s, %s,0,1);""", (int(ed[0]), int(ed[1])))
                except psycopg2.DatabaseError, e:
                    print "Unable to insert into topology table: %s" % str(e)

            f = open (ISP_nodes_file, "r").readlines ()
            for node in f:
                nd = node[:-1]
                try:
                    cursor.execute ("""INSERT INTO switches VALUES (%s);""", ([int (nd)]))
                except psycopg2.DatabaseError, e:
                    print "Unable to insert into switches table: %s" % str(e)

            for node in f:
                nd = node[:-1]
                try:
                    cursor.execute ("""INSERT INTO hosts VALUES (%s);""", ([int (nd)+1000]))
                    cursor.execute ("""INSERT INTO tp(sid, nid, ishost, isactive) VALUES (%s, %s,1,1);""",(int(nd)+1000,int(nd)))
                except psycopg2.DatabaseError, e:
                    print "Unable to insert into hosts table: %s" % str(e)

            cursor.execute (""" 
DROP TABLE IF EXISTS ports CASCADE;
CREATE UNLOGGED TABLE ports AS
       SELECT switches.sid, t.nid, t.port
       FROM switches, get_port(switches.sid) t ;
CREATE INDEX ON ports(sid, nid);
""")

            print "Initialize topology table with edges in " + ISP_edges_file

        conn = psycopg2.connect(database= dbname, user= Batch.username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        init_topology (cur)
        if conn: conn.close()
        print "--------------------> load_ISP_topo_fewer_hosts successful"

    def init_rib (self):
        cursor = self.cur
        ISP_edges_file = self.ISP_edges_file
        ISP_nodes_file = self.ISP_nodes_file
        rib_prefixes_file = self.rib_prefixes_file
        rib_peerIPs_file = self.rib_peerIPs_file 
        rib_edges_file = self.rib_edges_file

        def peerIP_ISP_map (peerIP_nodes_file, ISP_nodes_file):
            pf = open (peerIP_nodes_file, "r").readlines ()
            ispf = open (ISP_nodes_file, "r").readlines ()

            node_map = {}
            for pn in pf:
                ISP_node = random.choice (ispf)
                ispf.remove (ISP_node)
                node_map[pn[:-1]] = int (ISP_node[:-1]) 
            return node_map

        # map (randomly picked) ISP nodes (switch nodes in tp table)
        # to peer IPs in rib feeds
        nm = peerIP_ISP_map (rib_peerIPs_file, ISP_nodes_file)
        ISP_borders = nm.values ()

        cursor.execute ("""
DROP TABLE IF EXISTS borders CASCADE;
CREATE UNLOGGED TABLE borders (
       sid     integer,
       peerip  text
);
""")
        # set up borders table, randomly pick 21 switches, and assign
        # each switch a unique peer IP
        for key in nm.keys():
            cursor.execute ("""INSERT INTO borders (sid, peerip) VALUES (%s,  %s)""", (nm[key], key))

        cursor.execute (""" 
SELECT *
FROM uhosts, borders WHERE
hid = 1000 + sid;
""")
        cs = self.cur.fetchall ()
        sid2u_hid = {h['sid']: int (h['u_hid']) for h in cs}
        # print len (sid2u_hid)

        ribs = open (rib_edges_file, "r").readlines ()

        Batch.update_max_fid (self)
        fid = self.max_fid + 1
        
        for r in ribs:
            switch_id = int (nm [r.split ()[0]]) 
            random_border = int(random.choice (ISP_borders))

            if random_border != switch_id:
                cursor.execute ("INSERT INTO rtm VALUES (%s,%s,%s);", (fid, sid2u_hid[switch_id], sid2u_hid[random_border]))
                fid += 1
