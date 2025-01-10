# Left Path Routing (LPR)：所有的流都从最左边的路径到达目的地，如H3到H8的路径为H3->S2->S9->S17->S11->S4->H8
from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
# 'CONFIG_DISPATCHER’: 协商版本并发送功能请求消息
# 'MAIN_DISPATCHER’  : 接收交换机功能信息并发送set-config消息
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import ether_types
from ryu.lib import mac, ip
from ryu.topology import event
from collections import defaultdict


class ProjectController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	# 初始化，定义我们实验要求的网络拓扑
    def __init__(self, *args, **kwargs):
        super(ProjectController, self).__init__(*args, **kwargs)
        self.datapath_list = {}
        self.switches = []
        self.adjacency = defaultdict(dict)
        self.totalpath = defaultdict(list)

        self.hosts = {'10.0.0.1' : (1, 1), '10.0.0.2' : (1, 2), '10.0.0.3' : (2, 1), '10.0.0.4' : (2, 2),
                      '10.0.0.5' : (3, 1), '10.0.0.6' : (3, 2), '10.0.0.7' : (4, 1), '10.0.0.8' : (4, 2),
                      '10.0.0.9' : (5, 1), '10.0.0.10': (5, 2), '10.0.0.11': (6, 1), '10.0.0.12': (6, 2),
                      '10.0.0.13': (7, 1), '10.0.0.14': (7, 2), '10.0.0.15': (8, 1), '10.0.0.16': (8, 2)}
        self.parent = {1:(9,10),  2:(9,10),   3:(11,12),  4:(11,12),  5:(13,14),  6:(13,14),  7:(15,16),  8:(15,16),
        			   9:(17,18), 10:(19,20), 11:(17,18), 12:(19,20), 13:(17,18), 14:(19,20), 15:(17,18), 16:(19,20)}
        self.son = {
            9 :{'10.0.0.1':1,'10.0.0.2':1,'10.0.0.3':2,'10.0.0.4':2},
            10:{'10.0.0.1':1,'10.0.0.2':1,'10.0.0.3':2,'10.0.0.4':2},
            11:{'10.0.0.5':3,'10.0.0.6':3,'10.0.0.7':4,'10.0.0.8':4},
            12:{'10.0.0.5':3,'10.0.0.6':3,'10.0.0.7':4,'10.0.0.8':4},
            13:{'10.0.0.9':5,'10.0.0.10':5,'10.0.0.11':6,'10.0.0.12':6},
            14:{'10.0.0.9':5,'10.0.0.10':5,'10.0.0.11':6,'10.0.0.12':6},
            15:{'10.0.0.13':7,'10.0.0.14':7,'10.0.0.15':8,'10.0.0.16':8},
            16:{'10.0.0.13':7,'10.0.0.14':7,'10.0.0.15':8,'10.0.0.16':8},
            17:{'10.0.0.1':9,'10.0.0.2':9,'10.0.0.3':9,'10.0.0.4':9,'10.0.0.5':11,'10.0.0.6':11,'10.0.0.7':11,'10.0.0.8':11,
            '10.0.0.9':13,'10.0.0.10':13,'10.0.0.11':13,'10.0.0.12':13,'10.0.0.13':15,'10.0.0.14':15,'10.0.0.15':15,'10.0.0.16':15},
            18:{'10.0.0.1':9,'10.0.0.2':9,'10.0.0.3':9,'10.0.0.4':9,'10.0.0.5':11,'10.0.0.6':11,'10.0.0.7':11,'10.0.0.8':11,
            '10.0.0.9':13,'10.0.0.10':13,'10.0.0.11':13,'10.0.0.12':13,'10.0.0.13':15,'10.0.0.14':15,'10.0.0.15':15,'10.0.0.16':15},
            19:{'10.0.0.1':10,'10.0.0.2':10,'10.0.0.3':10,'10.0.0.4':10,'10.0.0.5':12,'10.0.0.6':12,
            '10.0.0.7':12,'10.0.0.8':12,'10.0.0.9':14,'10.0.0.10':14,'10.0.0.11':14,'10.0.0.12':14,
            '10.0.0.13':16,'10.0.0.14':16,'10.0.0.15':16,'10.0.0.16':16},
            20:{'10.0.0.1':10,'10.0.0.2':10,'10.0.0.3':10,'10.0.0.4':10,'10.0.0.5':12,'10.0.0.6':12,
            '10.0.0.7':12,'10.0.0.8':12,'10.0.0.9':14,'10.0.0.10':14,'10.0.0.11':14,'10.0.0.12':14,
            '10.0.0.13':16,'10.0.0.14':16,'10.0.0.15':16,'10.0.0.16':16},
        }

        # LPR/RSR下输出H{x%16}→ H{(x+4)%16}及H{x%16} → H{(x+5)%16}的路径，其中x为学号的后两位 (22307110187)
        self.key = [('10.0.0.7','10.0.0.11'), ('10.0.0.7','10.0.0.12')]


    # 在流表中增添表项
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # instruction是当包满足match时要执行的动作
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        # FlowMod可以让我们向switch内写入定义的flow entry
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)  # 把flow entry发给交换机

    def calculate(self, src, dst):
        dpid = self.hosts[src][0]  # 直接获取src host的父亲交换机
        while True:
            self.totalpath[(src, dst)].append(dpid)
            if self.hosts[dst][0] == dpid:  # 如果当前dpid已经是目标host的所属交换机，则退出
                break
            if dst not in self.son[dpid]:  # 如果dst不在当前dpid的子节点中
                dpid = self.parent[dpid][0]  # 往上走，选择父亲交换机的左节点
            else:
                dpid = self.son[dpid][dst]  # dst在子节点中，往下走

        # 找到任务要求的src--dst的路径，打印出来路径信息
        if (src,dst) in self.key:
            print("h%d ->" % (int(src.split('.')[-1])), end=" ")
            for i in self.totalpath[(src, dst)]:
                print("s%d ->" % (i), end=" ")
            print("h%d" % (int(dst.split('.')[-1])))

    def get_outport(self, dpid, src, dst):
        if (src, dst) not in self.totalpath:  # 开始规划路径
            self.calculate(src, dst)
        pth = self.totalpath[(src,dst)]
        for i in range(len(pth)):
            if pth[i] == dpid:  # 找到要求的dpid，如果下一条是dst host，返回dst host，否则按adjacency矩阵返回
                return (i == len(pth)-1) ? self.hosts[dst][1] : self.adjacency[dpid][pth[i+1]]


    # 处理未命中表项
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        print("switch_features_handler is called")
        datapath = ev.msg.datapath  # openflow交换机实例
        ofproto = datapath.ofproto  # 协商的openflow协议版本
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()  # 无参数意味着match任意一个包
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)  # 向流表下发一条表项

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg  # switch送来的事件ev, ev.msg是表示packet_in数据结构的一个对象
        datapath = msg.datapath  # msg.datapath是switch Datapath的一个对象，是哪个switch发来的消息
        ofproto = datapath.ofproto  # 协商的版本
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet) # 获取二层包头信息
        dpid = datapath.id
        src = None
        dst = None
        match = None
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
            src = ipv4_pkt.src
            dst = ipv4_pkt.dst
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, in_port=in_port, ipv4_src=src, ipv4_dst=dst)
        elif eth.ethertype == ether_types.ETH_TYPE_ARP:
            arp_pkt = pkt.get_protocol(arp.arp)
            src = arp_pkt.src_ip
            dst = arp_pkt.dst_ip
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_ARP, in_port=in_port, arp_spa=src, arp_tpa=dst)
        else:  # 包括lldp情况，忽略lldp packet
            return

        out_port = self.get_outport(dpid, src, dst)  # 获得dpid在src-dst路径上的的outport
        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:  # 把包送往该去的端口
            data = msg.data
        out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)


    @set_ev_cls(event.EventSwitchEnter)
    def switch_enter_handler(self, ev):
        print(ev)
        switch = ev.switch.dp
        if switch.id not in self.switches:
            self.switches.append(switch.id)
            self.datapath_list[switch.id] = switch

    @set_ev_cls(event.EventSwitchLeave, MAIN_DISPATCHER)
    def switch_leave_handler(self, ev):
        print(ev)
        switch = ev.switch.dp.id
        if switch in self.switches:
            self.switches.remove(switch)
            del self.datapath_list[switch]
            del self.adjacency[switch]

    #get adjacency matrix of fattree
    @set_ev_cls(event.EventLinkAdd, MAIN_DISPATCHER)
    def link_add_handler(self, ev):
        s1 = ev.link.src
        s2 = ev.link.dst
        self.adjacency[s1.dpid][s2.dpid] = s1.port_no
        self.adjacency[s2.dpid][s1.dpid] = s2.port_no

    @set_ev_cls(event.EventLinkDelete, MAIN_DISPATCHER)
    def link_delete_handler(self, ev):
        pass