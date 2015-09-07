execfile("libRavel.py")
import libRavel
from batch import Batch

class Batch_isp (Batch):

    def __init__(self, dbname, rounds, logdest, isp):

        print "for database isp" + str (isp) + "--------------------"
        create_db (dbname, Batch.username)
        if database_exists == 0:
            add_pgrouting_plpy_plsh_extension (dbname, Batch.username)
            load_schema (dbname, Batch.username, "/home/mininet/ravel/sql_scripts/primitive.sql")
            Batch_isp.init_ISP_topo (self, dbname, isp)

        Batch.__init__(self,dbname, rounds, logdest)

    def primitive (self):
        Batch.rtm_ins (self, self.rounds)
        Batch.rtm_del (self)

    def close (self):
        os.system ("cp "+ Batch.logfile + ' ' + self.logdest)
        os.system ("sudo mv "+ self.logdest + ' ' + ' /media/sf_share/ravel_plot/isp/')
        Batch.close (self)

    def init_ISP_topo (self, dbname, isp):

        def init_topology (cursor):
            ISP_edges_file = os.getcwd () + '/ISP_topo/'+str (isp) +'_edges.txt'
            ISP_nodes_file = os.getcwd () + '/ISP_topo/'+str (isp)+'_nodes.txt'

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


