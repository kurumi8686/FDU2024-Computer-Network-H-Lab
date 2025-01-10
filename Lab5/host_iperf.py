from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import OVSController
import time
import threading


class MyTopo(Topo):
    def __init__(self):
        super(MyTopo, self).__init__()
        h1 = self.addHost("H1", ip="10.0.0.1", mac="00:00:00:00:ff:01")
        h2 = self.addHost("H2", ip="10.0.0.2", mac="00:00:00:00:ff:02")
        h3 = self.addHost("H3", ip="10.0.0.3", mac="00:00:00:00:ff:03")
        h4 = self.addHost("H4", ip="10.0.0.4", mac="00:00:00:00:ff:04")
        s1 = self.addSwitch("S1")
        s2 = self.addSwitch("S2")
        self.addLink(h1, s1, bw=10, delay="2ms")
        self.addLink(h2, s1, bw=20, delay="10ms")
        self.addLink(h3, s2, bw=10, delay="2ms")
        self.addLink(h4, s2, bw=20, delay="10ms")
        self.addLink(s1, s2, bw=20, delay="2ms", loss=10)


def test1(h1, h3):  # 0--20s
    r3 = h3.cmd('iperf -s -p 5001 & ')
    print(r3)
    r1 = h1.cmd('iperf -c 10.0.0.3 -p 5001 -t 20 -i 0.5')
    print(r1)


def test2(h2, h4):
    time.sleep(10)  # stop 10s  10--30s
    r4 = h4.cmd('iperf -s -p 5002 & ')
    print(r4)
    r2 = h2.cmd('iperf -c 10.0.0.4 -p 5002 -t 20 -i 0.5 ')
    print(r2)


if __name__ == '__main__':
    setLogLevel('info')
    topo = MyTopo()
    net = Mininet(topo=topo, link=TCLink, controller=OVSController)
    net.start()
    dumpNodeConnections(net.hosts)
    h1, h2, h3, h4 = net.get('H1', 'H2', 'H3', 'H4')
    thread1 = threading.Thread(group=None, target=test1, args=(h1, h3))
    thread2 = threading.Thread(group=None, target=test2, args=(h2, h4))
    thread1.start()
    thread2.start()
    time.sleep(40)
    net.stop()
