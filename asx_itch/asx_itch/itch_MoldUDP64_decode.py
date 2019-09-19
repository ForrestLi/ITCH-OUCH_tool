import struct
import data_messages as dm

HEADER = struct.Struct('!10sQH')
MSG_BLOCK = struct.Struct('!Hc')


def decode_header(raw):
    d = HEADER.unpack_from(raw)
    return d


def decode_block(raw, offset=0):
    '''
        decode one block (length + message)
        return (dict, the offset after decoding)
    '''
    block_head = MSG_BLOCK.unpack_from(raw, offset)
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


def decode(raw):
    head = decode_header(raw)
    num_msgs = head[-1]
    if not num_msgs:
        yield {}
    for block in decode_iter_block(raw, num_msgs=num_msgs):
        yield block
