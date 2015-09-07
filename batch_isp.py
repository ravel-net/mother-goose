execfile("libRavel.py")
import libRavel
from batch import Batch

class Batch_isp (Batch):

    def __init__(self, dbname, rounds, logdest, isp):

        print "for database isp" + str (isp) + "--------------------"
        create_db (dbname, 'mininet')
        if database_exists == 0:
            add_pgrouting_plpy_plsh_extension (dbname, 'mininet')
            load_schema (dbname, 'mininet', "/home/mininet/ravel/sql_scripts/primitive.sql")
        Batch_isp.init_ISP_topo (self, isp)

        Batch.__init__(self,dbname, rounds, logdest)
        print Batch.links[1:4]


    def primitive (self):
        Batch.rtm_ins (self, self.rounds)
        Batch.rtm_del (self)

    def close (self):
        os.system ("cp "+ Batch.logfile + ' ' + self.logdest)
        os.system ("sudo mv "+ self.logdest + ' ' + ' /media/sf_share/ravel_plot/profile/')
        Batch.close (self)

    def init_ISP_topo (self,isp):

        def init_topology (cursor):
            ISP_edges_file = os.getcwd () + '/ISP_topo/'+str (isp) +'_edges.txt'
            ISP_nodes_file = os.getcwd () + '/ISP_topo/'+str (isp)+'_nodes.txt'

            f = open (ISP_edges_file, "r").readlines ()

            for edge in f:
                ed = edge[:-1].split()
                try:
                    cursor.execute("""INSERT INTO tp(sid, nid, isactive) VALUES (%s, %s,1);""", (int(ed[0]), int(ed[1])))
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
                    cursor.execute ("""INSERT INTO tp(sid, nid, isactive) VALUES (%s, %s,1);""",(int(nd)+1000,int(nd)))
                except psycopg2.DatabaseError, e:
                    print "Unable to insert into hosts table: %s" % str(e)
            print "Initialize topology table with edges in " + ISP_edges_file


        init_topology (self)
        print "--------------------> load_ISP_topo_fewer_hosts successful"

