"""2016-01-16-00-28-13-099279
$ sudo mn --custom /home/mininet/ravel/topo/toy_dtp.py --topo mytopo --test pingall
$ sudo mn --custom /home/mininet/ravel/topo/toy_dtp.py --topo mytopo --mac --switch ovsk --controller remote
"""

from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )
    
        h4 = self.addHost('h4')
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')

        self.addLink(s1,h1)
        self.addLink(s2,h2)
        self.addLink(s3,h3)
        self.addLink(s4,h4)
        self.addLink(s1,s2)
        self.addLink(s2,s3)
        self.addLink(s3,s4)
        self.addLink(s4,s1)

topos = { 'mytopo': ( lambda: MyTopo() ) }
    
