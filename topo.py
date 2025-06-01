#!/usr/bin/python


from mininet.net import Containernet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
import sys
import socket

setLogLevel('info')

net = Containernet()
info('*** Adding controller\n')
c1 = RemoteController( 'c1' , ip=socket.gethostbyname("onos"), port=6633)
net.addController(c1)


info('*** Adding docker containers\n')
h1 = net.addDocker('h1', ip='10.10.1.1', mac='9a:d8:73:d8:90:6a', dimage="ubuntu:trusty")
info('*** Adding hosts\n')
h2 = net.addHost('h2',  ip='10.10.2.1', mac='9a:d8:73:d8:90:6b')
h3 = net.addHost('h3',  ip='10.10.2.2', mac='9a:d8:73:d8:90:6c')

info('*** Adding gateway container\n')
gateway = net.addDocker('gateway', ip='10.10.0.1', mac='9a:d8:73:d8:90:6d', dimage="gateway")


info('*** Adding switches\n')
s1 = net.addSwitch('s1')
s2 = net.addSwitch('s2')
s3 = net.addSwitch('s3')
s4 = net.addSwitch('s4')
s5 = net.addSwitch('s5')

info('*** Creating links\n')

# switch1 links:
net.addLink(s1, s2, port=1, port=1)
net.addLink(s1, s3, port=2, port=1)
net.addLink(s1, s4, port=3, port=1)
net.addLink(s1, s5, port=4, port=1)

# switch2 links:
net.addLink(s2, gateway, port=2, port=1)
net.addLink(s2, s3, port=3, port=2)
net.addLink(s2, s4, port=4, port=2)
net.addLink(s2, s5, port=5, port=2)

# switch3 links:
net.addLink(s3, s4, port=5, port=3)
net.addLink(s3, h1, port=6, port=1)

# switch4 links:
net.addLink(s4, s5, port=6, port=3)
net.addLink(s4, h2, port=7, port=1)
net.addLink(s4, h3, port=8, port=1)



info('*** Starting network\n')
net.start()

gateway.cmd("iptables --table nat -A POSTROUTING -o eth0 -j MASQUERADE")
gateway.cmd("echo 1 > /proc/sys/net/ipv4/ip_forward")


h1.cmd("ip route del default")
h1.cmd("ip route add default via 10.10.0.1")
h2.cmd("ip route add default via 10.10.0.1")
h3.cmd("ip route add default via 10.10.0.1")

info('*** Running CLI\n')
CLI(net)
net.stop()
