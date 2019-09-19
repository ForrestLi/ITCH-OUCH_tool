import argparse
import socket
import traceback
import itch_SoupBinTCP_messages as im
import pcap_glimpse_extract


def run(ip, port, buffer_size=1024):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((ip, port))
    server.listen(1)
    with server:
        client_sock, address = server.accept()
        print(f'Accepted connection from {address[0]}:{address[1]}')
        it = pcap_glimpse_extract.iter_msgs()
        print(next(it))  # skip the login request
        # for d, raw_msg, ip_src, ip_dst in iter_msgs():
        #     print(f'(src, dst): ({ip_src}, {ip_dst}); decode: {d}')
        #     print('-' * 20)
        sent = False
        with client_sock as s:
            try:
                while True:
                    data = s.recv(buffer_size)
                    if data:
                        d = im.decode(data)
                        print('<<', data)
                        print('decode:', d)
                        if not sent:
                            sent = True
                            for d, raw_msg, *_ in it:
                                print('>>', raw_msg)
                                print('decode', d)
                                s.send(raw_msg)
                            break
                        print('-' * 20)
            except Exception as e:
                print(e)
                print(traceback.print_exc())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', default='192.168.56.102',
                        help='TCP IP to send data to (TCP server IP)')
    parser.add_argument('--port', type=int, default=21800,
                        help='TCP port to send data to (TCP server port)')
    args = parser.parse_args()
    run(args.ip, args.port)
