class NSDI:
    import os
    logfile = os.getcwd ()+'/log.txt'
    username = 'mininet'

    def __init__(self, dbname, rounds, logdest):
        self.rounds = rounds

        self.conn = psycopg2.connect(database= dbname, user= NSDI.username)
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        open(NSDI.logfile, 'w').close()
        self.f = open(NSDI.logfile, 'a')
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

    def re_route (self):
        self.f.write ("re_route----------------------------------------------\n")
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
        self.f.write ("rtm_ins----------------------------------------------\n")
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
        self.f.write ("rtm_del----------------------------------------------\n")
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


    def close (self):
        # os.system ("cp "+ NSDI.logfile + ' ' + self.logdest)
        # os.system ("sudo mv "+ self.logdest + ' ' + ' /media/sf_share/ravel_plot/profile/')
        if self.conn: self.conn.close()
        self.f.close ()


class NSDI_profile (NSDI):

    def __init__(self,dbname, rounds, logdest):
        gdb ([dbname], "/home/mininet/ravel/sql_scripts/primitive.sql")
        NSDI.__init__(self,dbname, rounds, logdest)
        add_profile_schema (self.cur, '/home/mininet/ravel/sql_scripts/add_profile.sql')

    def close (self):
        os.system ("cp "+ NSDI.logfile + ' ' + self.logdest)
        os.system ("sudo mv "+ self.logdest + ' ' + ' /media/sf_share/ravel_plot/profile/')
        NSDI.close (self)
    
class NSDI_fattree (NSDI):

    def __init__(self,dbname, rounds, logdest):
        gdb ([dbname], "/home/mininet/ravel/sql_scripts/primitive.sql")
        NSDI.__init__(self,dbname, rounds, logdest)
        remove_profile_schema (self.cur, '/home/mininet/ravel/sql_scripts/remove_profile.sql')

    def close (self):
        os.system ("cp "+ NSDI.logfile + ' ' + self.logdest)
        os.system ("sudo mv "+ self.logdest + ' ' + ' /media/sf_share/ravel_plot/fattree/')
        NSDI.close (self)
