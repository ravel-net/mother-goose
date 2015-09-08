execfile("libRavel.py")
import libRavel
from batch import Batch

class Batch_isp (Batch):

    def __init__(self, dbname, rounds):

        self.ISP_edges_file = os.getcwd () + '/ISP_topo/'+str (isp) +'_edges.txt'
        self.ISP_nodes_file = os.getcwd () + '/ISP_topo/'+str (isp)+'_nodes.txt'
        self.rib_prefixes_file = os.getcwd() + '/rib_feeds/' + "rib20011204_prefixes.txt"
        self.rib_peerIPs_file = os.getcwd() + '/rib_feeds/' + "rib20011204_nodes.txt"

        isp = dbname[3:]
        self.isp = isp
        print "for database isp" + str (isp) + "--------------------"

        create_db (dbname, Batch.username)
        if database_exists == 0:
            add_pgrouting_plpy_plsh_extension (dbname, Batch.username)
            load_schema (dbname, Batch.username, "/home/mininet/ravel/sql_scripts/primitive.sql")
            Batch_isp.init_ISP_topo (self, dbname, isp)

        Batch.__init__(self,dbname, rounds)


    def close (self):
        os.system ("cp "+ Batch.logfile + ' ' + self.logdest)
        os.system ("sudo mv "+ self.logdest + ' ' + ' /media/sf_share/ravel_plot/isp/')
        Batch.close (self)

    def init_ISP_topo (self, dbname, isp):

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

            f = ['60\n','34\n','112\n','141\n','193\n','238\n','28\n','89\n','91\n','253\n','472\n']
            for node in f:
                nd = node[:-1]
                try:
                    cursor.execute ("""INSERT INTO hosts VALUES (%s);""", ([int (nd)+1000]))
                    cursor.execute ("""INSERT INTO tp(sid, nid, ishost, isactive) VALUES (%s, %s,1,1);""",(int(nd)+1000,int(nd)))
                except psycopg2.DatabaseError, e:
                    print "Unable to insert into hosts table: %s" % str(e)
            print "Initialize topology table with edges in " + ISP_edges_file

        conn = psycopg2.connect(database= dbname, user= Batch.username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        init_topology (cur)
        if conn: conn.close()
        print "--------------------> load_ISP_topo_fewer_hosts successful"


    def init_rib (self, rib_edges_file):

        cursor = self.cur
        ISP_edges_file = self.ISP_edges_file
        ISP_nodes_file = self.ISP_nodes_file
        rib_prefixes_file = self.rib_prefixes 
        rib_peerIPs_file = self.rib_peerIPs 

        def peerIP_ISP_map (peerIP_nodes_file, ISP_nodes_file):
            pf = open (peerIP_nodes_file, "r").readlines ()
            ispf = open (ISP_nodes_file, "r").readlines ()

            node_map = {}
            for pn in pf:
                ISP_node = random.choice (ispf)
                ispf.remove (ISP_node)
                node_map[pn[:-1]] = ISP_node[:-1]
            return node_map

        global ISP_graph

        nm = peerIP_ISP_map (rib_peerIPs_file, ISP_nodes_file)
        ISP_borders = nm.values ()

        for key in nm.keys():
            try: 
                cursor.execute ("""INSERT INTO borders (switch_id, peerip) VALUES (%s,  %s)""", (nm[key], key))
            except psycopg2.DatabaseError, e:
                print "Unable to insert into borders "
                print 'Warning %s' % e

        prefixes_id_map = {}
        def set_prefixes_id_map ():
            pre = open (rib_prefixes_file, "r").readlines ()
            cid = 0
            for p in pre:
                cid = cid + 1
                prefixes_id_map[p[:-1]] = cid

        set_prefixes_id_map ()

        time_lapse = 0

        ribs = open (rib_edges_file, "r").readlines ()
        for r in ribs:
            switch_id = int (nm [r.split ()[0]]) 
            prefix = r.split ()[1]
            random_border = int(random.choice (ISP_borders))

            for n in [random_border]:
                if n != switch_id:
                    path_list = ISP_graph.get_shortest_paths (switch_id, n)[0]
                    path_edges = path_to_edge (path_list)

                    start_t = time.time ()

                    try: 
                        cursor.execute ("""SELECT flow_id from flow_constraints WHERE flow_id = %s""", ([prefixes_id_map[prefix]]))
                        c = cursor.fetchall ()

                        if c == []:
                            try: 
                                cursor.execute ("""INSERT INTO flow_constraints (flow_id, flow_name) VALUES (%s,  %s)""", (prefixes_id_map[prefix], prefix))
                            except psycopg2.DatabaseError, e:
                                logging.warning (e)

                        for ed in path_edges:                            
                            cursor.execute ("""INSERT INTO configuration (flow_id, switch_id, next_id) VALUES (%s,%s,%s)""", (prefixes_id_map[prefix], ed[0], ed[1]))

                    except psycopg2.DatabaseError, e:
                        pass

                    end_t = time.time ()
                    time_lapse = time_lapse + end_t - start_t

        cursor.execute ("""SELECT count (*) FROM configuration""")
        c = cursor.fetchall ()

        logging.info ("Load configuration " + str (tf (time_lapse)) + " " + str (tfm (time_lapse)))
        logging.info ("Load configuration (" + str (c[0][0]) + " rows) average " + tf (time_lapse / int(c[0][0])))
        print "Load configuration table with edges\n"
