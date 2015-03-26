"""2015-03-26-06-47-45-950664
$ sudo mn --custom /home/mininet/ravel/isp_dtp.py --topo mytopo --test pingall
$ sudo mn --custom /home/mininet/ravel/isp_dtp.py --topo mytopo --mac --switch ovsk --controller remote
"""

from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )
    
        h1060 = self.addHost('h1060')
        h1034 = self.addHost('h1034')
        h1112 = self.addHost('h1112')
        h1141 = self.addHost('h1141')
        h1193 = self.addHost('h1193')
        h1238 = self.addHost('h1238')
        h1028 = self.addHost('h1028')
        h1089 = self.addHost('h1089')
        h1091 = self.addHost('h1091')
        h1253 = self.addHost('h1253')
        h1472 = self.addHost('h1472')

        s216 = self.addSwitch('s216')
        s213 = self.addSwitch('s213')
        s91 = self.addSwitch('s91')
        s498 = self.addSwitch('s498')
        s499 = self.addSwitch('s499')
        s135 = self.addSwitch('s135')
        s494 = self.addSwitch('s494')
        s495 = self.addSwitch('s495')
        s496 = self.addSwitch('s496')
        s497 = self.addSwitch('s497')
        s490 = self.addSwitch('s490')
        s491 = self.addSwitch('s491')
        s492 = self.addSwitch('s492')
        s493 = self.addSwitch('s493')
        s28 = self.addSwitch('s28')
        s289 = self.addSwitch('s289')
        s288 = self.addSwitch('s288')
        s346 = self.addSwitch('s346')
        s281 = self.addSwitch('s281')
        s220 = self.addSwitch('s220')
        s349 = self.addSwitch('s349')
        s227 = self.addSwitch('s227')
        s262 = self.addSwitch('s262')
        s260 = self.addSwitch('s260')
        s266 = self.addSwitch('s266')
        s126 = self.addSwitch('s126')
        s127 = self.addSwitch('s127')
        s128 = self.addSwitch('s128')
        s269 = self.addSwitch('s269')
        s378 = self.addSwitch('s378')
        s416 = self.addSwitch('s416')
        s417 = self.addSwitch('s417')
        s531 = self.addSwitch('s531')
        s530 = self.addSwitch('s530')
        s273 = self.addSwitch('s273')
        s375 = self.addSwitch('s375')
        s591 = self.addSwitch('s591')
        s592 = self.addSwitch('s592')
        s313 = self.addSwitch('s313')
        s194 = self.addSwitch('s194')
        s191 = self.addSwitch('s191')
        s190 = self.addSwitch('s190')
        s193 = self.addSwitch('s193')
        s192 = self.addSwitch('s192')
        s115 = self.addSwitch('s115')
        s392 = self.addSwitch('s392')
        s89 = self.addSwitch('s89')
        s397 = self.addSwitch('s397')
        s113 = self.addSwitch('s113')
        s112 = self.addSwitch('s112')
        s279 = self.addSwitch('s279')
        s86 = self.addSwitch('s86')
        s118 = self.addSwitch('s118')
        s138 = self.addSwitch('s138')
        s369 = self.addSwitch('s369')
        s423 = self.addSwitch('s423')
        s528 = self.addSwitch('s528')
        s529 = self.addSwitch('s529')
        s443 = self.addSwitch('s443')
        s301 = self.addSwitch('s301')
        s299 = self.addSwitch('s299')
        s447 = self.addSwitch('s447')
        s108 = self.addSwitch('s108')
        s109 = self.addSwitch('s109')
        s241 = self.addSwitch('s241')
        s388 = self.addSwitch('s388')
        s249 = self.addSwitch('s249')
        s34 = self.addSwitch('s34')
        s438 = self.addSwitch('s438')
        s434 = self.addSwitch('s434')
        s435 = self.addSwitch('s435')
        s432 = self.addSwitch('s432')
        s252 = self.addSwitch('s252')
        s458 = self.addSwitch('s458')
        s489 = self.addSwitch('s489')
        s176 = self.addSwitch('s176')
        s456 = self.addSwitch('s456')
        s60 = self.addSwitch('s60')
        s102 = self.addSwitch('s102')
        s64 = self.addSwitch('s64')
        s67 = self.addSwitch('s67')
        s177 = self.addSwitch('s177')
        s253 = self.addSwitch('s253')
        s173 = self.addSwitch('s173')
        s171 = self.addSwitch('s171')
        s344 = self.addSwitch('s344')
        s502 = self.addSwitch('s502')
        s500 = self.addSwitch('s500')
        s469 = self.addSwitch('s469')
        s468 = self.addSwitch('s468')
        s465 = self.addSwitch('s465')
        s464 = self.addSwitch('s464')
        s467 = self.addSwitch('s467')
        s466 = self.addSwitch('s466')
        s463 = self.addSwitch('s463')
        s462 = self.addSwitch('s462')
        s98 = self.addSwitch('s98')
        s228 = self.addSwitch('s228')
        s164 = self.addSwitch('s164')
        s160 = self.addSwitch('s160')
        s96 = self.addSwitch('s96')
        s270 = self.addSwitch('s270')
        s19 = self.addSwitch('s19')
        s116 = self.addSwitch('s116')
        s152 = self.addSwitch('s152')
        s155 = self.addSwitch('s155')
        s555 = self.addSwitch('s555')
        s554 = self.addSwitch('s554')
        s557 = self.addSwitch('s557')
        s556 = self.addSwitch('s556')
        s553 = self.addSwitch('s553')
        s552 = self.addSwitch('s552')
        s238 = self.addSwitch('s238')
        s235 = self.addSwitch('s235')
        s236 = self.addSwitch('s236')
        s230 = self.addSwitch('s230')
        s232 = self.addSwitch('s232')
        s233 = self.addSwitch('s233')
        s47 = self.addSwitch('s47')
        s329 = self.addSwitch('s329')
        s277 = self.addSwitch('s277')
        s146 = self.addSwitch('s146')
        s141 = self.addSwitch('s141')
        s149 = self.addSwitch('s149')
        s71 = self.addSwitch('s71')
        s487 = self.addSwitch('s487')
        s486 = self.addSwitch('s486')
        s485 = self.addSwitch('s485')
        s484 = self.addSwitch('s484')
        s483 = self.addSwitch('s483')
        s482 = self.addSwitch('s482')
        s480 = self.addSwitch('s480')
        s472 = self.addSwitch('s472')
        s473 = self.addSwitch('s473')
        s470 = self.addSwitch('s470')
        s471 = self.addSwitch('s471')
        s476 = self.addSwitch('s476')
        s477 = self.addSwitch('s477')
        s474 = self.addSwitch('s474')
        s475 = self.addSwitch('s475')
        s478 = self.addSwitch('s478')
        s479 = self.addSwitch('s479')

        self.addLink(s60,s34)
        self.addLink(s60,s112)
        self.addLink(s60,s141)
        self.addLink(s60,s193)
        self.addLink(s60,s238)
        self.addLink(s60,s253)
        self.addLink(s60,s472)
        self.addLink(s91,s28)
        self.addLink(s91,s34)
        self.addLink(s91,s89)
        self.addLink(s91,s112)
        self.addLink(s91,s116)
        self.addLink(s91,s138)
        self.addLink(s91,s155)
        self.addLink(s91,s173)
        self.addLink(s91,s236)
        self.addLink(s91,s241)
        self.addLink(s91,s262)
        self.addLink(s91,s266)
        self.addLink(s91,s346)
        self.addLink(s91,s417)
        self.addLink(s91,s432)
        self.addLink(s91,s447)
        self.addLink(s91,s472)
        self.addLink(s108,s67)
        self.addLink(s108,s86)
        self.addLink(s108,s98)
        self.addLink(s108,s112)
        self.addLink(s108,s127)
        self.addLink(s108,s146)
        self.addLink(s108,s194)
        self.addLink(s108,s216)
        self.addLink(s108,s228)
        self.addLink(s108,s233)
        self.addLink(s108,s270)
        self.addLink(s108,s299)
        self.addLink(s108,s375)
        self.addLink(s108,s388)
        self.addLink(s108,s392)
        self.addLink(s108,s423)
        self.addLink(s108,s434)
        self.addLink(s108,s435)
        self.addLink(s108,s472)
        self.addLink(s109,s19)
        self.addLink(s109,s64)
        self.addLink(s109,s112)
        self.addLink(s109,s164)
        self.addLink(s109,s253)
        self.addLink(s109,s378)
        self.addLink(s109,s397)
        self.addLink(s109,s438)
        self.addLink(s109,s472)
        self.addLink(s112,s60)
        self.addLink(s112,s91)
        self.addLink(s112,s108)
        self.addLink(s112,s109)
        self.addLink(s112,s113)
        self.addLink(s112,s115)
        self.addLink(s112,s118)
        self.addLink(s112,s190)
        self.addLink(s112,s191)
        self.addLink(s112,s230)
        self.addLink(s112,s466)
        self.addLink(s112,s468)
        self.addLink(s112,s471)
        self.addLink(s112,s472)
        self.addLink(s113,s71)
        self.addLink(s113,s112)
        self.addLink(s113,s126)
        self.addLink(s113,s176)
        self.addLink(s113,s177)
        self.addLink(s113,s252)
        self.addLink(s113,s262)
        self.addLink(s113,s269)
        self.addLink(s113,s273)
        self.addLink(s113,s277)
        self.addLink(s113,s288)
        self.addLink(s113,s289)
        self.addLink(s113,s313)
        self.addLink(s113,s416)
        self.addLink(s113,s443)
        self.addLink(s113,s472)
        self.addLink(s115,s47)
        self.addLink(s115,s96)
        self.addLink(s115,s102)
        self.addLink(s115,s112)
        self.addLink(s115,s152)
        self.addLink(s115,s171)
        self.addLink(s115,s192)
        self.addLink(s115,s213)
        self.addLink(s115,s235)
        self.addLink(s115,s281)
        self.addLink(s115,s301)
        self.addLink(s115,s329)
        self.addLink(s115,s349)
        self.addLink(s115,s369)
        self.addLink(s115,s417)
        self.addLink(s115,s472)
        self.addLink(s118,s34)
        self.addLink(s118,s112)
        self.addLink(s190,s86)
        self.addLink(s190,s98)
        self.addLink(s190,s112)
        self.addLink(s190,s127)
        self.addLink(s190,s146)
        self.addLink(s190,s194)
        self.addLink(s190,s216)
        self.addLink(s190,s227)
        self.addLink(s190,s228)
        self.addLink(s190,s232)
        self.addLink(s190,s270)
        self.addLink(s190,s279)
        self.addLink(s190,s299)
        self.addLink(s190,s344)
        self.addLink(s190,s375)
        self.addLink(s190,s388)
        self.addLink(s190,s392)
        self.addLink(s190,s423)
        self.addLink(s190,s434)
        self.addLink(s190,s435)
        self.addLink(s190,s472)
        self.addLink(s191,s112)
        self.addLink(s191,s127)
        self.addLink(s191,s135)
        self.addLink(s191,s149)
        self.addLink(s191,s160)
        self.addLink(s191,s177)
        self.addLink(s191,s220)
        self.addLink(s191,s260)
        self.addLink(s191,s472)
        self.addLink(s230,s112)
        self.addLink(s230,s249)
        self.addLink(s230,s456)
        self.addLink(s230,s467)
        self.addLink(s230,s471)
        self.addLink(s230,s552)
        self.addLink(s230,s553)
        self.addLink(s230,s554)
        self.addLink(s249,s230)
        self.addLink(s249,s472)
        self.addLink(s262,s91)
        self.addLink(s262,s113)
        self.addLink(s262,s466)
        self.addLink(s262,s471)
        self.addLink(s262,s591)
        self.addLink(s262,s592)
        self.addLink(s456,s230)
        self.addLink(s456,s463)
        self.addLink(s456,s465)
        self.addLink(s456,s471)
        self.addLink(s456,s472)
        self.addLink(s456,s473)
        self.addLink(s456,s480)
        self.addLink(s456,s482)
        self.addLink(s462,s463)
        self.addLink(s462,s490)
        self.addLink(s462,s496)
        self.addLink(s462,s497)
        self.addLink(s462,s498)
        self.addLink(s462,s530)
        self.addLink(s463,s456)
        self.addLink(s463,s462)
        self.addLink(s463,s473)
        self.addLink(s463,s483)
        self.addLink(s463,s493)
        self.addLink(s463,s500)
        self.addLink(s463,s530)
        self.addLink(s464,s493)
        self.addLink(s465,s456)
        self.addLink(s465,s474)
        self.addLink(s465,s475)
        self.addLink(s465,s476)
        self.addLink(s465,s477)
        self.addLink(s465,s478)
        self.addLink(s465,s479)
        self.addLink(s466,s112)
        self.addLink(s466,s262)
        self.addLink(s466,s469)
        self.addLink(s466,s470)
        self.addLink(s466,s472)
        self.addLink(s467,s230)
        self.addLink(s467,s472)
        self.addLink(s468,s112)
        self.addLink(s469,s466)
        self.addLink(s469,s471)
        self.addLink(s470,s466)
        self.addLink(s470,s471)
        self.addLink(s471,s112)
        self.addLink(s471,s230)
        self.addLink(s471,s262)
        self.addLink(s471,s456)
        self.addLink(s471,s469)
        self.addLink(s471,s470)
        self.addLink(s472,s60)
        self.addLink(s472,s91)
        self.addLink(s472,s108)
        self.addLink(s472,s109)
        self.addLink(s472,s112)
        self.addLink(s472,s113)
        self.addLink(s472,s115)
        self.addLink(s472,s190)
        self.addLink(s472,s191)
        self.addLink(s472,s249)
        self.addLink(s472,s456)
        self.addLink(s472,s466)
        self.addLink(s472,s467)
        self.addLink(s472,s552)
        self.addLink(s472,s553)
        self.addLink(s472,s554)
        self.addLink(s472,s556)
        self.addLink(s472,s557)
        self.addLink(s473,s456)
        self.addLink(s473,s463)
        self.addLink(s480,s456)
        self.addLink(s482,s456)
        self.addLink(s482,s458)
        self.addLink(s483,s463)
        self.addLink(s490,s462)
        self.addLink(s490,s498)
        self.addLink(s493,s463)
        self.addLink(s493,s464)
        self.addLink(s493,s496)
        self.addLink(s493,s497)
        self.addLink(s493,s498)
        self.addLink(s493,s499)
        self.addLink(s496,s462)
        self.addLink(s496,s493)
        self.addLink(s496,s502)
        self.addLink(s497,s462)
        self.addLink(s497,s485)
        self.addLink(s497,s493)
        self.addLink(s497,s528)
        self.addLink(s497,s529)
        self.addLink(s498,s128)
        self.addLink(s498,s462)
        self.addLink(s498,s484)
        self.addLink(s498,s486)
        self.addLink(s498,s487)
        self.addLink(s498,s489)
        self.addLink(s498,s490)
        self.addLink(s498,s491)
        self.addLink(s498,s493)
        self.addLink(s498,s494)
        self.addLink(s498,s531)
        self.addLink(s500,s463)
        self.addLink(s500,s492)
        self.addLink(s500,s495)
        self.addLink(s530,s462)
        self.addLink(s530,s463)
        self.addLink(s552,s230)
        self.addLink(s552,s472)
        self.addLink(s553,s230)
        self.addLink(s553,s472)
        self.addLink(s554,s230)
        self.addLink(s554,s472)
        self.addLink(s556,s472)
        self.addLink(s556,s555)
        self.addLink(s557,s472)
        self.addLink(h1060,s60)
        self.addLink(h1034,s34)
        self.addLink(h1112,s112)
        self.addLink(h1141,s141)
        self.addLink(h1193,s193)
        self.addLink(h1238,s238)
        self.addLink(h1028,s28)
        self.addLink(h1089,s89)
        self.addLink(h1091,s91)
        self.addLink(h1253,s253)
        self.addLink(h1472,s472)

topos = { 'mytopo': ( lambda: MyTopo() ) }
    
