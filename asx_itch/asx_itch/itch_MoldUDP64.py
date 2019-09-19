import struct
import data_messages as dm


class Header:
    STRUCT = struct.Struct('!10sQH')
    FIELDS = ['Session', 'Sequence Number', 'Message Count']

    def __init__(self, arg_list, validate=True):
        assert len(self.FIELDS) == len(arg_list), \
            '3 arguments expected, given ' + len(arg_list)
        self.arg_list = arg_list
        if validate:
            self.pack()

    def pack(self):
        return self.STRUCT.pack(*self.arg_list)


MSG_BLOCK = struct.Struct('!H')
MSG_BLOCK_MT = struct.Struct('!Hc')


def decode_header(raw):
    d = Header.STRUCT.unpack_from(raw)
    return d


def decode_block(raw, offset=0):
    '''
        decode one block (length + message)
        return (dict, the offset after decoding)
    '''
    block_head = MSG_BLOCK_MT.unpack_from(raw, offset)
    block_len, msg_type = block_head
    offset += 2
    if block_len <= 0:
        raise ValueError('block len error')
    d = dm.decode_msg(raw, msg_type, offset)
    return d, offset + block_len


def decode_iter_block(raw, offset=20, num_msgs=0):
    for _ in range(num_msgs):
        d, offset = decode_block(raw, offset)
        yield d


def decode(raw, with_header=False):
    head = decode_header(raw)
    if with_header:
        yield dict(zip(Header.FIELDS, head))
    num_msgs = head[-1]
    if not num_msgs:
        yield {}
    for block in decode_iter_block(raw, num_msgs=num_msgs):
        yield block


def pack(header, market_msg):
    msg_bytes = market_msg.pack()
    msg_len_b = MSG_BLOCK.pack(len(msg_bytes))
    return header.pack() + msg_len_b + msg_bytes
