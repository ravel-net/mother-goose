execfile("libRavel.py")
import libRavel
from batch import Batch

class Batch_profile (Batch):

    def __init__(self,dbname, rounds, logdest):
        gdb ([dbname], "/home/mininet/ravel/sql_scripts/primitive.sql")

        Batch.__init__(self,dbname, rounds, logdest)

        add_profile_schema (self.cur)

    def primitive (self):

        Batch.rtm_ins (self, self.rounds)

        Batch.rtm_del (self)

    def close (self):
        os.system ("cp "+ Batch.logfile + ' ' + self.logdest)
        os.system ("sudo mv "+ self.logdest + ' ' + ' /media/sf_share/ravel_plot/profile/')
        Batch.close (self)
    
