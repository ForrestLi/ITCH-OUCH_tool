import socket
import argparse
import pack


def create_sock(mcast_if=None):
    MULTICAST_TTL = 20
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)
    if mcast_if:
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(mcast_if))
    return sock


def run(group, port, mcast_if=None):
    sock = create_sock()

    def seqno_gen(from_x):
        while True:
            yield from_x
            from_x += 2
    gen = seqno_gen(74978)

    c1, c2, orderID = pack.genAdd(seqNo=next(gen))
    sock.sendto(c1, (group, port))
    sock.sendto(c2, (group, port))
    c1, c2 = pack.delAdd(seqNo=next(gen), orderID=orderID)
    sock.sendto(c1, (group, port))
    sock.sendto(c2, (group, port))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mcast-group', default='239.1.1.1')
    parser.add_argument('--port', type=int, default=19900)
    parser.add_argument('--mcast-if', default=None)
    args = parser.parse_args()
    run(args.mcast_group, args.port, args.mcast_if)
