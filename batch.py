execfile("libRavel.py")
import libRavel

class Batch:
    import os
    logfile = os.getcwd ()+'/log.txt'
    username = 'mininet'

    def __init__(self, dbname, rounds):
        self.rounds = rounds
        self.profile = False 

        self.conn = psycopg2.connect(database= dbname, user= Batch.username)
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        self.max_fid = 0

        open(Batch.logfile, 'w').close()
        self.f = open(Batch.logfile, 'a')
        self.logdest = dbname + '.log'

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

    def add_profile_schema (self):
        cur = self.cur
        add_profile_schema (cur)
        self.profile = True

    def close (self):
        if self.conn: self.conn.close()
        self.f.close ()

    def init_acl (self):
        self.cur.execute ("select distinct host1, host2 from utm ;")
        cs = self.cur.fetchall ()
        t_ends = [[h['host1'], h['host2']] for h in cs]
        print "init_acl ends size: " + str (len (t_ends)) 
        if len (t_ends) > self.rounds:
            ends = t_ends[: self.rounds]
        else:
            ends = t_ends

        for i in range (len (ends)):
            [e1, e2] = ends[i]
            # is_inblacklist = random.choice([0,1])
            is_inblacklist = np.random.choice([0,1], 1, p=[0.8, 0.2])[0]
            self.cur.execute ("INSERT INTO acl_tb VALUES ("+ str (e1)+ ","+ str (e2) + "," + str (is_inblacklist) +");") 

    def init_lb (self):
        self.cur.execute ("select distinct host2 from utm ;")
        cs = self.cur.fetchall ()
        t_ends = [h['host2'] for h in cs]
        print "init_lb ends size: " + str (len (t_ends)) 
        if len (t_ends) > self.rounds:
            ends = t_ends[: self.rounds]
        else:
            ends = t_ends
        
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
            self.f.write ('#p----re_route: linkdown----' + str ((t2-t1)*1000) + '\n')
            self.f.flush ()
            self.cur.execute ("UPDATE tp SET isactive = 1 WHERE sid = %s AND nid = %s;",([link[0], link[1]]))

    def update_max_fid (self):
        self.cur.execute ("SELECT max(fid) FROM rtm;")
        cs = self.cur.fetchall ()
        if cs == [[None]]:
            self.max_fid = 0
        else:
            self.max_fid = cs[0]['max']

        self.cur.execute ("SELECT max(fid) FROM utm;")
        cs = self.cur.fetchall ()
        if cs[0]['max'] > self.max_fid:
            self.max_fid = cs[0]['max']


    def rtm_ins (self, rounds):
        self.f.write ("#rtm_ins----------------------------------------------\n")
        Batch.update_max_fid (self)
        max_fid = self.max_fid
        # self.cur.execute ("SELECT max(fid) FROM rtm;")
        # cs = self.cur.fetchall ()
        # if cs == [[None]]:
        #     max_fid = 0
        # else:
        #     max_fid = cs[0]['max']

        for r in range (max_fid+1, max_fid + rounds + 1):
            [h1, h2] = random.sample(self.uhosts, 2)

            self.f.write ("#round " + str (r-1) + '\n')
            self.f.flush ()
            t1 = time.time ()
            self.cur.execute ("INSERT INTO rtm values (%s,%s,%s);",([int (r),int (h1),int (h2)]))
            t2 = time.time ()
            self.f.write ('----rt: route ins----' + str ((t2-t1)*1000) + '\n')
            self.f.write ('#pi----rt: route ins----' + str ((t2-t1)*1000) + '\n')
            self.f.flush ()

    def rtm_del (self):
        self.f.write ("#rtm_del----------------------------------------------\n")
        self.cur.execute ("SELECT fid FROM rtm;")
        cs = self.cur.fetchall ()
        fids = [h['fid'] for h in cs]

        for r in range (0, self.rounds):
            self.f.write ("#round " + str (r) + '\n')
            self.f.flush ()
            t1 = time.time ()
            self.cur.execute ("DELETE FROM rtm WHERE fid =" +str (fids[r])+ ";")
            t2 = time.time ()
            self.f.write ('----rt: route del----' + str ((t2-t1)*1000) + '\n')
            self.f.write ('#pd----rt: route del----' + str ((t2-t1)*1000) + '\n')
            self.f.flush ()


    def op_lb (self):
        cur = self.cur
        f = self.f
        # try: # add comments here

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
        print "update lb set load = " +str (max_load - 1)+" where sid = "+str (s_id)+";"
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
        # except psycopg2.DatabaseError, e:
        #     print 'op_lb fail Error %s' % e

    def op_acl (self):
        cur = self.cur
        f = self.f

        t1 = time.time ()
        cur.execute ("select end1, end2 from acl limit 1;")
        t2 = time.time ()
        f.write ('----acl: check violation----' + str ((t2-t1)*1000) + '\n')
        f.flush ()
        t = cur.fetchall ()[0]
        e1 = t['end1']
        e2 = t['end2']

        t1 = time.time ()
        cur.execute ("update acl set isviolated = 0 where end1 = "+ str (e1) +" and end2 = "+str (e2)+";")
        t2 = time.time ()
        f.write ('----acl: fix violation----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

        t3 = time.time ()
        cur.execute("select max (counts) from clock;")
        ct = cur.fetchall () [0]['max'] 
        cur.execute ("INSERT INTO p_spv VALUES (" + str (ct+1) + ", 'on');")
        t4 = time.time ()
        f.write ('----acl+rt: fix violation (per rule)----' + str ((t2-t1 + t4-t3)*1000) + '\n')
        f.write ('----acl+rt: fix violation (absolute)----' + str ((t2-t1 + t4-t3)*1000) + '\n')
        f.flush ()


    def routing_ins_acl_lb (self, h1s, h2s):
        cur = self.cur
        f = self.f

        Batch.update_max_fid (self)
        fid = self.max_fid + 1

        h1 = random.sample(h1s, 1)[0]
        h2 = random.sample(h2s, 1)[0]

        t1 = time.time ()
        cur.execute ("INSERT INTO utm VALUES ("+str (fid) +"," +str (h1) + "," + str (h2)+");")
        cur.execute("select max (counts) from clock;")
        ct = cur.fetchall () [0]['max'] 
        cur.execute ("INSERT INTO p1 VALUES (" + str (ct+1) + ", 'on');")
        t2 = time.time ()
        f.write ('----acl+lb+rt: route ins----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

    def op_profile (self):

        Batch.rtm_ins (self, self.rounds)
        Batch.rtm_del (self)
        Batch.re_route (self)

    def op_primitive (self):
        cur = self.cur
        f = self.f

        f.write ("#primitive: op_lb ----------------------------------------------\n")
        for r in range (0, 20):
            Batch.op_lb (self)

        f.write ("#primitive: op_acl ----------------------------------------------\n")
        cur.execute("select count(*) from acl;")
        ct = cur.fetchall () [0]['count']
        if ct > 20:
            ct = 20
        for i in range (ct):
            Batch.op_acl (self)

        f.write ("#primitive: routing_ins_acl_lb ----------------------------------------------\n")
        capacity = Batch.init_acl_lb (self)
        cur.execute ("SELECT DISTINCT end1 FROM acl_tb;")
        cs = cur.fetchall ()
        h1s = [h['end1'] for h in cs]
        cur.execute ("SELECT DISTINCT end2 FROM acl_tb;")
        cs = cur.fetchall ()
        h2s = [h['end2'] for h in cs]
        if capacity > 20:
            capacity = 20
        for i in range (capacity):
            Batch.routing_ins_acl_lb (self, h1s, h2s)
