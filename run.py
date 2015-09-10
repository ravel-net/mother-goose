execfile("libRavel.py")
execfile("plot.py")
execfile("batch.py")
execfile("batch_profile.py")
execfile("batch_fattree.py")
execfile("batch_isp.py")

import libRavel
import batch
import batch_profile
import batch_fattree
import batch_isp
import plot

switch_size = 0
fanout_size = 0
monitor_mininet = 0
k_size = 0 # number of pods of the fat tree

username = 'mininet'
sql_profile = "/home/mininet/ravel/sql_scripts/primitive_profile.sql"
sql_script1 = "/home/mininet/ravel/sql_scripts/base_and_routing_w.sql"
sql_script2 = "/home/mininet/ravel/sql_scripts/obs_app.sql"
sql_script3 = "/home/mininet/ravel/sql_scripts/base_and_routing_wo_optimized.sql"
primitive = "/home/mininet/ravel/sql_scripts/primitive.sql"
tenant = "/home/mininet/ravel/sql_scripts/tenant.sql"
# without mininet operation, that is, no actual add_flow / del_flow,
# just absolute value of postgres time

def scenario(rounds, t, s):
    if t == 'isp' and s == '3sizes':
        l = ['isp4755_' + str (rounds), 'isp3356_' + str (rounds), 'isp7018_'+str (rounds)]
        p = rPlot_primitive ('isp_3sizes')

    elif t == 'isp' and s == '3ribs':
        l = ['isp2914_10', 'isp2914_100', 'isp2914_1000']
        p = rPlot_primitive ('isp2914_3ribs')

    elif t == 'fat' and s == 'primitive': 
        l = ['fattree16', 'fattree32', 'fattree64']
        p = rPlot_primitive ('fattree')

    elif t == 'fat' and s == 'tenant': 
        l = ['fattree16', 'fattree32', 'fattree64']
        p = rPlot_tenant ('fattree')

    for db in l:

        if t == 'isp' and s = '3sizes':
            b = Batch_isp (db, int (rounds))
        elif t == 'fat':
            b = Batch_fattree (db, int (rounds))

        if t == 'isp' or (t == 'fat' and s == 'primitive'):
            b.primitive ()
        elif t == 'fat' and s == 'tenant':
            b.tenant ()

        b.close ()

        p.add_log (t.logdest)

    p.key_list.remove ('rt: route ins')
    p.gen_dat ()
    p.gen_plt ()

if __name__ == '__main__':
    l1 = ['fattree16', 'fattree32', 'fattree64']
    l2 = ['fattree4', 'fattree8', 'fattree16']

    while True:
        m = raw_input ("batch, test, interactive, mininet, or exit? (b, t, i, m, e) \n")

        if m == 'b':

            scenario (10, 'isp', '3sizes')
            scenario (10, 'isp', '3ribs')

            # primitive = rPlot_primitive ('fattree')
            # for db in l1:
            #     t2 = Batch_fattree (db, 50)
            #     t2.primitive ()
            #     t2.close ()
            #     primitive.add_log (t2.logdest)
            # primitive.gen_dat ()
            # primitive.gen_plt ()

            # tenant = rPlot_tenant ('fattree')
            # for db in l1:
            #     t3 = Batch_fattree (db, 50)
            #     t3.tenant ()
            #     t3.close ()
            #     tenant.add_log (t3.logdest)
            # tenant.gen_dat ()
            # tenant.gen_plt ()

            # isp = rPlot_primitive ('isp')
            # for db in l4:
            #     t4 = Batch_isp (db, 4)
            #     t4.primitive ()
            #     t4.close ()
            #     isp.add_log (t4.logdest)
            # isp.gen_dat ()
            # isp.gen_plt ()

                # t = Batch_profile (db, 4)
                # t.primitive ()
                # t.close ()

        elif m == 't':

            primitive = rPlot_primitive ('fattree')
            for db in l1:
                t2 = Batch_fattree (db, 10)
                t2.primitive ()
                t2.close ()
                primitive.add_log (t2.logdest)
            primitive.gen_dat ()
            primitive.gen_plt ()

            tenant = rPlot_tenant ('fattree')
            for db in l1:
                t3 = Batch_fattree (db, 10)
                t3.tenant ()
                t3.close ()
                tenant.add_log (t3.logdest)
            tenant.gen_dat ()
            tenant.gen_plt ()

        elif m == 't2':

            isp = rPlot_primitive ('isp')
            for db in l3:
                t4 = Batch_isp (db, 30)
                t4.primitive ()
                t4.close ()
                isp.add_log (t4.logdest)
            isp.key_list.remove ('rt: route ins')
            isp.gen_dat ()
            isp.gen_plt ()

        elif m == 'm':
            mininet_interactive ()

        # if m == 'p':
        #     profile (l1[:1], username, 30)

        elif m == 'e':
            break
