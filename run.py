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

l1 = ['fattree16', 'fattree32', 'fattree64']
l3 = ['isp4755_10', 'isp4755_100', 'isp4755_1000']
l4 = ['isp2914_10', 'isp4755_10', 'isp7018_10']


def profile (rounds):
        l = ['isp2914_'+str (rounds), 'isp2914_' + str (rounds*10), 'isp2914_' + str (rounds*100)] + ['isp4755_' + str (rounds), 'isp3356_' + str (rounds), 'isp7018_' + str (rounds)] + ['fattree16', 'fattree32', 'fattree64']

        for d in l:
            if d[:3] == 'isp':
                b = Batch_isp (d, rounds)
            else:
                b = Batch_fattree (d,rounds)
            b.add_profile_schema ()
            b.op_profile ()
            b.close ()

def scenario(rounds, t, s):
    if t == 'isp' and s == '3sizes':
        l = ['isp4755_' + str (rounds), 'isp3356_' + str (rounds), 'isp7018_' + str (rounds)]
        p = rPlot_primitive ('isp_3sizes')
        p.key_list.remove ('rt: route ins')

    elif t == 'isp' and s == '3ribs':
        l = ['isp2914_' + str (rounds), 'isp2914_' + str (rounds*10), 'isp2914_' + str (rounds*100)]
        p = rPlot_primitive ('isp2914_3ribs')
        p.key_list.remove ('rt: route ins')

    elif t == 'fat' and s == 'primitive': 
        l = ['fattree16', 'fattree32', 'fattree64']
        p = rPlot_primitive ('fattree')

    elif t == 'fat' and s == 'tenant': 
        l = ['fattree16', 'fattree32', 'fattree64']
        p = rPlot_tenant ('fattree')

    for db in l:

        if t == 'isp':
            b = Batch_isp (db, int (rounds))
        elif t == 'fat':
            b = Batch_fattree (db, int (rounds))

        if t == 'isp' or (t == 'fat' and s == 'primitive'):
            b.primitive ()
        elif t == 'fat' and s == 'tenant':
            b.tenant ()

        b.close ()
        p.add_log (b.logdest)

    p.gen_dat ()
    p.gen_plt ()

if __name__ == '__main__':

    while True:
        m = raw_input ("fat, isp, profile, batch, test, mininet, or exit? (f, i, p, b, t, m, e) \n")

        if m == 'f':

            scenario (100, 'fat', 'primitive')
            scenario (100, 'fat', 'tenant')

        elif m == 'i':

            t1 = time.time ()
            # scenario (100, 'isp', '3sizes')
            scenario (100, 'isp', '3ribs')
            t2 = time.time ()
            print ("time consumed: " + str ((t2-t1)))

        elif m == 'p':

            profile (100)

        elif m == 'b':

            scenario (100, 'fat', 'primitive')
            scenario (100, 'fat', 'tenant')

            scenario (100, 'isp', '3sizes')
            scenario (100, 'isp', '3ribs')

            profile (4)

        elif m == 't': 
            # profile (4)
            profile_dat ('/media/sf_share/ravel_plot/profile/log/fattree16.log')

        elif m == 'e':
            break


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

            # for d in l1[0]:
            #     b = Batch_fattree (d, 4)
            #     b.add_profile_schema ()
            #     b.op_profile ()
            #     b.close ()
            # p.add_log (b.logdest)
            # print p.log_file_list
