from distutils.util import run_2to3
from uuid import RFC_4122
from mininet.topo import Topo
from mininet.node import Node
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.node import OVSController

SUCNO = 2   # Nro. de sucursales
WANIP = "192.168.100.{}"    # La red dispuesta es 192.168.100.0/24
WANMASK = "/24"
SUCRANGE = range(SUCNO) # Puede salir mal. Cambiar por list-comp en todo caso
SUCIP = "10.0.{}.{}"


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

        # Crear elementos de la red
        central_router = self.addNode("r0", cls=Router, ip=WANIP.format(6) + "29")

        wan_switch_list = [self.addSwitch(f"ws{s + 1}") for s in SUCRANGE]
        lan_switch_list = [self.addSwitch(f"ls{s + 1}") for s in SUCRANGE]
        router_list = [self.addNode(f"r{suc + 1}", cls=Router, ip=WANIP.format(8*(suc + 1) - 7) + "/29") for suc in SUCRANGE]
        host_list = [
            self.addHost(
                f"h{suc + 1}",
                ip=SUCIP.format(suc + 1, 254) + "/24",  # ip address add 10.0.{suc}.254/24 dev h{suc}-eth0 brd +
                defaultRoute="via " + SUCIP.format(suc + 1, 1) # ip route add default via 10.0.{suc}.1
            )
            for suc in SUCRANGE
        ]

        # Conectar los elementos de la red
        # Conectar los switches con el router central
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
            self.addLink(
                router_list[suc],
                wan_switch_list[suc],
                intfName1=f"r{suc + 1}-eth0",
                params1={
                    "ip": WANIP.format(8*(suc + 1) - 7) + "/29"
                }
            )

        # Contectar los routers de sucursales a los switches de sucursales
            self.addLink(
                lan_switch_list[suc],
                router_list[suc],
                intfName2=f"r{suc + 1}-eth1",
                params2={
                    "ip": SUCIP.format(suc + 1, 1) + "/24"  # ip address add 10.0.{suc}.1/24 dev r{suc}-eth1 brd +
                }
            )

        # Conectar los switches de sucursales a los host
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

        print(net.keys())
        # Configurar tablas de ruteo a cada nodo intermedio
        for suc in SUCRANGE:
            print(f"===============R{suc}=================")
            # Regla de ruteo para ir de Central a Sucursales
            net["r0"].cmd(f"ip route add {SUCIP.format(suc + 1, 0)}/24 via {WANIP.format(8*(suc + 1) - 7)}")

            for i in range(1, SUCNO + 1):
                # Regla de ruteo para ir desde Sucursal hacia otras sucursales
                print(f"ip route add {SUCIP.format(i + 1, 0)}/24 via {WANIP.format(8 * (suc + 1) - 2)}")
                net[f"r{suc + 1}"].cmd(f"ip route add {SUCIP.format(i + 1, 0)}/24 via {WANIP.format(8 * (suc + 1) - 2)}")
                # Regla de ruteo para ir desde router de Sucursal hacia routers de sucursales
                net[f"r{suc + 1}"].cmd(f"ip route add {WANIP.format(8*i)}/29 via {WANIP.format(8 * (suc + 1) - 2)}")

        
        info("*** Tabla de ruteo en Router Central ***\n")
        info(net["r0"].cmd("route"))

        CLI(net)
        net.stop()


if __name__ == "__main__":
    setLogLevel('info')
    Main.main()

