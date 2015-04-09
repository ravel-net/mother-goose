"""2015-04-08-16-25-51-217695
$ sudo mn --custom /home/mininet/ravel/topo/fattree_dtp.py --topo mytopo --test pingall
$ sudo mn --custom /home/mininet/ravel/topo/fattree_dtp.py --topo mytopo --mac --switch ovsk --controller remote
"""

from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )
    
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')
        h6 = self.addHost('h6')
        h7 = self.addHost('h7')

        s0 = self.addSwitch('s0')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')
        s6 = self.addSwitch('s6')
        s7 = self.addSwitch('s7')
        s8 = self.addSwitch('s8')
        s9 = self.addSwitch('s9')

        self.addLink(s3,h1)
        self.addLink(s4,h2)
        self.addLink(s5,h3)
        self.addLink(s6,h4)
        self.addLink(s7,h5)
        self.addLink(s8,h6)
        self.addLink(s9,h7)
        self.addLink(s0,s1)
        self.addLink(s0,s2)
        self.addLink(s0,s3)
        self.addLink(s1,s4)
        self.addLink(s1,s5)
        self.addLink(s1,s6)
        self.addLink(s2,s7)
        self.addLink(s2,s8)
        self.addLink(s2,s9)

topos = { 'mytopo': ( lambda: MyTopo() ) }
    
