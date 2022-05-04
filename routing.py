from mininet.topo import Topo
from mininet.node import Node
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.node import OVSController

SUCNO = 6   # Nro. de sucursales

class Router(Node):
    """
    Un router no es mas que un host con el forwarding de paquetes ip
    activado.
    """

    def config(self, **params):
        super(Router, self).config(**params)
        self.cmd("sysctl net.ipv4.ip_forward=1") # Activar el forwarding del nodo

    def terminate(self):
        self.cmd("sysctl net.ipv4.ip_forward=0")
        super(Router, self).terminate()


class NetworkTopo(Topo):
    """
    Topologia para una red de sucursales con redes privadas
    para cada una. El nro. de sucursales es variable.
    """

    def build(self, **_opts):

        WANIP = "192.168.100.{}"    # La red dispuesta es 192.168.100.0/24
        WANMASK = "/24"
        SUCRANGE = range(SUCNO) # Puede salir mal. Cambiar por list-comp en todo caso

        SUCIP = "10.0.{}.{}"

        # Crear elementos de la red
        central_router = self.addNode("r0", cls=Router, ip=WANIP.format())
        self["r0"].cmd("ip address del 10.0.0.7/8 dev r0-eth0")
        wan_switch_list = [self.addSwitch(f"ws{s + 1}") for s in SUCRANGE]
        lan_switch_list = [self.addSwitch(f"ls{s + 1}") for s in SUCRANGE]
        router_list = [self.addNode(f"r{suc + 1}", cls=Router) for suc in SUCRANGE]
        host_list = [
            self.addHost(
                f"h{suc + 1}",
                ip=SUCIP.format(suc + 1, 254) + "/24",  # ip address add 10.0.{suc}.254/24 dev h{suc}-eth0 brd +
                defaultRoute="via " + SUCIP.format(suc + 1, 1) # ip route add default via 10.0.{suc}.1
            )
            for suc in SUCRANGE
        ]

        # Conectar los elementos entre si
        # Conectorizar los switches con el router central
        for suc in SUCRANGE:
            self.addLink(
                wan_switch_list[suc],
                central_router,
                intfName2=f"r0-eth{suc}",
                params2={
                    "ip": WANIP.format(8*(suc + 1) - 2) + "/29"
                }
            )


        # Conectar los routers de sucursales a los switches
        for suc in SUCRANGE:
            self.addLink(
                router_list[suc],
                wan_switch_list[suc],
                intfName1=f"r{suc + 1}-eth0",
                params1={
                    "ip": WANIP.format(8*(suc + 1) - 7) + "/29"
                }
            )

        # Contectar los routers de sucursales a los switches de sucursales
        for suc in SUCRANGE:
            self.addLink(
                lan_switch_list[suc],
                router_list[suc],
                intfName2=f"r{suc + 1}-eth1",
                params2={
                    "ip": SUCIP.format(suc + 1, 1) + "/24"  # ip address add 10.0.{suc}.1/24 dev r{suc}-eth1 brd +
                }
            )

        # Conectar los switches de sucursales a los host
        for suc in SUCRANGE:
            self.addLink(
                host_list[suc],
                lan_switch_list[suc],
                intfName1=f"h{suc + 1}-eth0",
                params1={
                    "ip": SUCIP.format(suc + 1, 254) + "/24"
                }
            )


class Main:
    def main():
        topo = NetworkTopo()
        net = Mininet(
            topo=topo,
            waitConnected=True,
            controller=OVSController
        )

        net.start()
        info("*** Tabla de ruteo en Router Central ***\n")
        info(net["r0"].cmd("route"))
        CLI(net)
        net.stop()


if __name__ == "__main__":
    setLogLevel('info')
    Main.main()

