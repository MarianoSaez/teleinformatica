#!/usr/bin_/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    info( '*** Add switches\n')
    s1_lan = net.addSwitch('s1_lan', failMode='standalone')
    s1_wan = net.addSwitch('s1_wan', failMode='standalone')
    s2_lan = net.addSwitch('s2_lan', failMode='standalone')
    s2_wan = net.addSwitch('s2_wan', failMode='standalone')

    r_central = net.addHost('r_central', cls=Node, ip='')
    r1 = net.addHost('r1', cls=Node, ip='')
    r2 = net.addHost('r2', cls=Node, ip='')

    r_central.cmd('sysctl -w net.ipv4.ip_forward=1')
    r1.cmd('sysctl -w net.ipv4.ip_forward=1')
    r2.cmd('sysctl -w net.ipv4.ip_forward=1')

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='10.0.1.254/24', defaultRoute=None)
    h2 = net.addHost('h2', cls=Host, ip='10.0.2.254/24', defaultRoute=None)

    info( '*** Add links\n')
    net.addLink(r_central, s1_wan, intfName1='r_central-eth0', params1={ 'ip' : '192.168.100.6/29' })
    net.addLink(r_central, s2_wan, intfName1='r_central-eth1', params1={ 'ip' : '192.168.100.14/29' })
    net.addLink(r1, s1_wan, intfName1='r1-eth0', params1={ 'ip' : '192.168.100.1/29' })
    net.addLink(r2, s2_wan, intfName1='r2-eth0', params1={ 'ip' : '192.168.100.9/29' })
    net.addLink(r1, s1_lan, intfName1='r1-eth1', params1={ 'ip' : '10.0.1.1/24' })
    net.addLink(r2, s2_lan, intfName1='r2-eth1', params1={ 'ip' : '10.0.2.1/24' })

    net.addLink(h1, s1_lan)
    net.addLink(h2, s2_lan)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s2_wan').start([])
    net.get('s2_lan').start([])
    net.get('s1_lan').start([])
    net.get('s1_wan').start([])

    info( '*** Post configure switches and hosts\n')
    net['r_central'].cmd('ip route add 10.0.1.0/24 via 192.168.100.1')
    net['r_central'].cmd('ip route add 10.0.2.0/24 via 192.168.100.9')

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()