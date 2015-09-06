class batch:
    import os
    logfile = os.getcwd ()+'/log.txt'
    username = 'mininet'

    def __init__(self, dbname, rounds, logdest):
        self.rounds = rounds

        self.conn = psycopg2.connect(database= dbname, user= batch.username)
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        open(batch.logfile, 'w').close()
        self.f = open(batch.logfile, 'a')
        self.logdest = logdest

        self.cur.execute ("SELECT * FROM uhosts;")
        cs = self.cur.fetchall ()
        self.hids = [h['hid'] for h in cs]

        self.cur.execute ("SELECT count(*) FROM switches;")
        self.switch_size = int (self.cur.fetchall ()[0]['count'])

        self.cur.execute ("SELECT u_hid FROM uhosts;")
        cs = self.cur.fetchall ()
        self.uhosts = [h['u_hid'] for h in cs]

        self.cur.execute ("SELECT * FROM hosts;")
        cs = self.cur.fetchall ()
        self.hosts = [h['hid'] for h in cs]

        self.cur.execute ("SELECT * FROM switches;")
        cs = self.cur.fetchall ()
        self.switches = [h['sid'] for h in cs]

        self.cur.execute ("SELECT sid,nid FROM tp where ishost = 0;")
        cs = self.cur.fetchall ()
        self.links = [[h['sid'], h['nid']] for h in cs]

    def close (self):
        if self.conn: self.conn.close()
        self.f.close ()

    def init_acl (self):
        self.cur.execute ("select distinct host1, host2 from utm ;")
        cs = self.cur.fetchall ()
        ends = [[h['host1'], h['host2']] for h in cs]
        
        foo = [0, 1]
        for i in range (len (ends)):
            [e1, e2] = ends[i]
            is_inblacklist = random.choice(foo)
            self.cur.execute ("INSERT INTO acl_tb VALUES ("+ str (e1)+ ","+ str (e2) + "," + str (is_inblacklist) +");") 

    def init_lb (self):
        self.cur.execute ("select distinct host2 from utm ;")
        cs = self.cur.fetchall ()
        ends = [h['host2'] for h in cs]
        
        for i in range (len (ends)):
            e = ends[i]
            self.cur.execute ("INSERT INTO lb_tb VALUES ("+ str (e)+ ");")

    def init_acl_lb (self):
        self.cur.execute ("select sum(load) from lb ;")
        agg_load = self.cur.fetchall ()[0]['sum']

        self.cur.execute ("select count(*) from lb ;")
        switch_size = self.cur.fetchall ()[0]['count']

        self.cur.execute ("select max(load) from lb;")
        max_load = self.cur.fetchall ()[0]['max']

        self.cur.execute (""" 
        CREATE OR REPLACE RULE lb_constraint AS
        ON INSERT TO p1
        WHERE (NEW.status = 'on')
        DO ALSO (
            UPDATE lb SET load = """ +str (max_load+1)+ """ WHERE load > """ +str (max_load+1)+""";
	    UPDATE p1 SET status = 'off' WHERE counts = NEW.counts;
	   );        
""")
        
        residual_load = switch_size * max_load - agg_load
        return residual_load

    def re_route (self):
        self.f.write ("#re_route----------------------------------------------\n")
        for r in range (0, self.rounds):
            link = random.sample(self.links, 1)[0]
            # print link
            t1 = time.time ()
            self.cur.execute ("UPDATE tp SET isactive = 0 WHERE sid = %s AND nid = %s;",([link[0], link[1]]))
            t2 = time.time ()
            self.f.write ('----re_route: linkdown----' + str ((t2-t1)*1000) + '\n')
            self.f.flush ()
            self.cur.execute ("UPDATE tp SET isactive = 1 WHERE sid = %s AND nid = %s;",([link[0], link[1]]))

    def rtm_ins (self):
        self.f.write ("#rtm_ins----------------------------------------------\n")
        self.cur.execute ("SELECT max(fid) FROM rtm;")
        cs = self.cur.fetchall ()
        if cs == [[None]]:
            max_fid = 0
        else:
            max_fid = cs[0]['max']

        for r in range (max_fid+1, max_fid + self.rounds + 1):
            [h1, h2] = random.sample(self.uhosts, 2)

            self.f.write ("round " + str (r-1) + '\n')
            self.f.flush ()
            t1 = time.time ()
            self.cur.execute ("INSERT INTO rtm values (%s,%s,%s);",([int (r),int (h1),int (h2)]))
            t2 = time.time ()
            self.f.write ('----rt: route ins----' + str ((t2-t1)*1000) + '\n')
            self.f.flush ()

    def rtm_del (self):
        self.f.write ("#rtm_del----------------------------------------------\n")
        self.cur.execute ("SELECT fid FROM rtm;")
        cs = self.cur.fetchall ()
        fids = [h['fid'] for h in cs]

        for r in range (0, self.rounds):
            self.f.write ("round " + str (r) + '\n')
            self.f.flush ()
            t1 = time.time ()
            self.cur.execute ("DELETE FROM rtm WHERE fid =" +str (fids[r])+ ";")
            t2 = time.time ()
            self.f.write ('----rt: route del----' + str ((t2-t1)*1000) + '\n')
            self.f.flush ()

class batch_profile (batch):

    def __init__(self,dbname, rounds, logdest):
        gdb ([dbname], "/home/mininet/ravel/sql_scripts/primitive.sql")
        batch.__init__(self,dbname, rounds, logdest)
        add_profile_schema (self.cur, '/home/mininet/ravel/sql_scripts/add_profile.sql')

    def close (self):
        os.system ("cp "+ batch.logfile + ' ' + self.logdest)
        os.system ("sudo mv "+ self.logdest + ' ' + ' /media/sf_share/ravel_plot/profile/')
        batch.close (self)
    
class batch_fattree (batch):

    def __init__(self,dbname, rounds, logdest):
        gdb ([dbname], "/home/mininet/ravel/sql_scripts/primitive.sql")
        batch.__init__(self,dbname, rounds, logdest)
        remove_profile_schema (self.cur, '/home/mininet/ravel/sql_scripts/remove_profile.sql')
        batch.rtm_ins (self)
        batch.init_acl (self)
        batch.init_lb (self)
        self.capacity = batch.init_acl_lb (self)

    def op_lb (self):
        cur = self.cur
        f = self.f

        t1 = time.time ()
        cur.execute ("select max(load) from lb ;")
        t2 = time.time ()
        f.write ('----lb: check max load----' + str ((t2-t1)*1000) + '\n')
        f.flush ()
        max_load = cur.fetchall ()[0]['max']

        cur.execute ("select sid from lb where load = "+str (max_load)+" limit 1;")
        s_id = cur.fetchall ()[0]['sid']
        t1 = time.time ()
        cur.execute ("update lb set load = " +str (max_load - 1)+" where sid = "+str (s_id)+";")
        t2 = time.time ()
        f.write ('----lb: re-balance (absolute)----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

        t3 = time.time ()
        cur.execute("select max (counts) from clock;")
        ct = cur.fetchall () [0]['max']
        cur.execute ("INSERT INTO p_spv VALUES (" + str (ct+1) + ", 'on');")
        t4 = time.time ()
        f.write ('----lb+rt: re-balance (per rule)----' + str ((t2-t1 + t4-t3)*1000) + '\n')
        f.write ('----lb+rt: re-balance (absolute)----' + str ((t2-t1 + t4-t3)*1000) + '\n')
        f.flush ()

    def primitive (self):
        cur = self.cur
        f = self.f

        f.write ("#primitive: op_lb----------------------------------------------\n")
        for r in range (0, self.rounds):
            batch_fattree.op_lb (self)

    def close (self):
        os.system ("cp "+ batch.logfile + ' ' + self.logdest)
        os.system ("sudo mv "+ self.logdest + ' ' + ' /media/sf_share/ravel_plot/fattree/')
        batch.close (self)
