import scapy.all as sa
import scapy
import itch_SoupBinTCP_decode
from pprint import pprint
from collections import defaultdict
import argparse

pkt_types_in = {b'S', b'+', b'A', b'J', b'H', b'Z'}


def iter_msgs(pcap_file='./tcp_partition4.pcap',
              dst_addr=('10.31.38.4', 45793),
              src_addr=('203.0.119.230', 21804),
              debug=False):
    pcap = sa.rdpcap(pcap_file)

    remain = b''
    for pkt in pcap:
        if not (sa.TCP in pkt and sa.Raw in pkt and sa.IP in pkt):
            if debug:
                print('Not TCP/IP or no payload in pkt')
            continue
        assert isinstance(pkt, scapy.layers.l2.Ether)
        if debug:
            print('pkt.time', pkt.time)
        ip_src = pkt[sa.IP].src
        ip_dst = pkt[sa.IP].dst
        raw = bytes(pkt[sa.Raw])
        if ip_src == src_addr[0]:
            raw = remain + raw
            if debug and remain:
                print('remain = ', remain)
            if debug and raw[2:3] not in pkt_types_in:
                print('not a proper message type: ',
                      raw[2:3], 'raw_len', len(raw), 'raw', raw)
                continue
        try:
            off = 0
            for d, msg_len in itch_SoupBinTCP_decode.decode(raw):
                yield d, raw[off:off+msg_len], ip_src, ip_dst
                off += msg_len
                assert off <= len(raw), 'unexpected: offset > len(raw)'
            remain = raw[off:]
        except Exception as e:
            print(e, 'error decoding payload of packet:', pkt.time)
        if debug:
            print('*' * 20)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pcap-file', default='./tcp_partition4.pcap')
    parser.add_argument('--src-ip', default='203.0.119.230')
    parser.add_argument('--src-port', type=int, default=21804)
    parser.add_argument('--dst-ip', default='10.31.38.4')
    parser.add_argument('--dst-port', type=int, default=45793)
    args = parser.parse_args()

    obid_str = 'Order Book ID'
    oid_str = 'Order ID'
    obp_str = 'Order Book Position'
    q_str = 'Quantity'
    p_str = 'Price'
    s_str = 'Side'
    kws = [obid_str, obp_str, q_str, p_str, s_str, oid_str]
    dls = defaultdict(list)
    for d, raw_msg, ip_src, ip_dst in iter_msgs(
            pcap_file=args.pcap_file,
            src_addr=(args.src_ip, args.src_port),
            dst_addr=(args.dst_ip, args.dst_port)):
        if 'decode' not in d:
            d['decode'] = {}
        dd = d['decode']
        if obp_str in dd:
            dls[dd[obid_str]].append({k: v for k, v in dd.items() if k in kws})
        print(f'(src, dst): ({ip_src}, {ip_dst}); decode: {d}')
        print('-' * 20)
    for k in dls:
        dls[k].sort(key=lambda x: (x[s_str], x[obp_str]))
    pprint(dls)
