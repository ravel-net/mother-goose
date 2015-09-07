execfile("libRavel.py")
import libRavel
from batch import Batch

class Batch_fattree (Batch):

    def __init__(self,dbname, rounds):
        gdb ([dbname], "/home/mininet/ravel/sql_scripts/primitive.sql")
        Batch.__init__(self,dbname, rounds)
        remove_profile_schema (self.cur)

    def close (self):
        os.system ("cp "+ Batch.logfile + ' ' + self.logdest)
        os.system ("sudo mv "+ self.logdest + ' ' + ' /media/sf_share/ravel_plot/fattree/')
        Batch.close (self)

    def primitive (self):
        size = 10
        Batch.rtm_ins (self, size)
        Batch.init_acl (self)
        Batch.init_lb (self)

        Batch.op_primitive (self)

    def tenant (self):
        size = 10
        Batch_fattree.init_tenant (self, size)
        Batch_fattree.init_tacl (self)
        Batch_fattree.init_tlb (self)

        for i in range (size*3):
            Batch_fattree.op_tlb (self)

        self.cur.execute("select count(*) from tacl;")
        ct = self.cur.fetchall () [0]['count']
        for i in range (ct):
            Batch_fattree.op_tacl (self)

        self.cur.execute ("select * from tenant_hosts ;")
        cs = self.cur.fetchall ()
        thosts = [h['hid'] for h in cs]
        for i in range (size):
            Batch_fattree.routing_ins_acl_lb_tenant (self,thosts)

    def routing_ins_acl_lb_tenant (self,hosts):
        cur = self.cur
        f = self.f
        
        [h1, h2] = random.sample(hosts, 2)

        Batch.update_max_fid (self)
        fid = self.max_fid + 1

        t1 = time.time ()
        cur.execute ("INSERT INTO tenant_policy VALUES ("+str (fid) +"," +str (h1) + "," + str (h2)+");")
        cur.execute("select max (counts) from clock;")
        ct = cur.fetchall () [0]['max'] 
        cur.execute ("INSERT INTO t1 VALUES (" + str (ct+1) + ", 'on');")
        t2 = time.time ()
        f.write ('----(acl+lb+rt)*tenant: route ins----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

    def init_tacl (self):
        cur = self.cur
        cur.execute ("select distinct host1, host2 from tenant_policy ;")
        cs = cur.fetchall ()
        ends = [[h['host1'], h['host2']] for h in cs]

        for i in range (len (ends)):
            [e1, e2] = ends[i]
            is_inblacklist = random.choice([0,1])
            cur.execute ("INSERT INTO tacl_tb VALUES ("+ str (e1)+ ","+ str (e2) + "," + str (is_inblacklist) +");") 

    def init_tlb (self):
        cur = self.cur
        cur.execute ("select distinct host2 from tenant_policy ;")
        cs = cur.fetchall ()
        ends = [h['host2'] for h in cs]
        print ends
        
        for e in ends:
            cur.execute ("INSERT INTO tlb_tb VALUES ("+ str (e)+ ");")

    def tenant_fullmesh (self, hosts):
        f = self.f
        cur = self.cur

        Batch.update_max_fid (self)
        fid = self.max_fid + 1

        cur.execute ("select max (counts) from clock;")
        ct = cur.fetchall ()[0]['max'] + 1

        for i in range (len (hosts)):
            for j in range (i+1,len (hosts)):
                print "tenant_fullmesh: [" + str (hosts[i]) + "," + str (hosts[j]) + "]"
                t1 = time.time ()
                cur.execute ("INSERT INTO tenant_policy values (%s,%s,%s);",([str (fid) ,int (hosts[i]), int (hosts[j])]))
                cur.execute ("INSERT INTO p_spv values (%s,'on');",([ct]))
                t2 = time.time ()
                f.write ('----rt*tenant: route ins----' + str ((t2-t1)*1000) + '\n')
                f.flush ()
                ct += 1
                fid += 1

    def init_tenant (self,size):
        cur = self.cur

        add_tenant_schema (cur)

        cur.execute ("SELECT * FROM uhosts;")
        cs = cur.fetchall ()
        hosts = [int (s['u_hid']) for s in cs]

        selected_hosts = [ hosts[i] for i in random.sample(xrange(len(hosts)), size) ]

        for h in selected_hosts:
            cur.execute ("insert into tenant_hosts values (" + str (h) + ");")

        print selected_hosts
        Batch_fattree.tenant_fullmesh (self, selected_hosts)

    def op_tlb (self):
        cur = self.cur
        f = self.f
        
        t1 = time.time ()
        cur.execute ("select * from tlb order by load DESC limit 1;")
        t2 = time.time ()
        f.write ('----lb*tenant: check max load----' + str ((t2-t1)*1000) + '\n')
        f.flush ()
        max_load = cur.fetchall ()[0]['load']

        cur.execute ("select sid from tlb where load = "+str (max_load)+" limit 1;")
        s_id = cur.fetchall ()[0]['sid']

        t1 = time.time ()
        cur.execute ("update tlb set load = " +str (max_load - 1)+" where sid = "+str (s_id)+";")
        t2 = time.time ()
        f.write ('----lb*tenant: re-balance----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

        t3 = time.time ()
        cur.execute("select max (counts) from clock;")
        ct = cur.fetchall () [0]['max'] 
        cur.execute ("INSERT INTO p_spv VALUES (" + str (ct+1) + ", 'on');")
        t4 = time.time ()
        f.write ('----(lb+rt)*tenant: re-balance----' + str ((t2-t1 + t4-t3)*1000) + '\n')
        # f.write ('----lb+rt: re-balance (absolute)----' + str ((t2-t1 + t4-t3)*1000) + '\n')
        f.flush ()

    def op_tacl (self):
        cur = self.cur
        f = self.f

        t1 = time.time ()
        cur.execute ("select end1, end2 from tacl limit 1;")
        t2 = time.time ()
        f.write ('----acl*tenant: check violation----' + str ((t2-t1)*1000) + '\n')
        f.flush ()
        t = cur.fetchall ()[0]
        e1 = t['end1']
        e2 = t['end2']

        t1 = time.time ()
        cur.execute ("update tacl set isviolated = 0 where end1 = "+ str (e1) +" and end2 = "+str (e2)+";")
        t2 = time.time ()
        f.write ('----acl*tenant: fix violation----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

        t3 = time.time ()
        cur.execute("select max (counts) from clock;")
        ct = cur.fetchall () [0]['max'] 
        cur.execute ("INSERT INTO p_spv VALUES (" + str (ct+1) + ", 'on');")
        t4 = time.time ()
        f.write ('----acl+rt*tenant: fix violation----' + str ((t2-t1 + t4-t3)*1000) + '\n')
        f.flush ()

