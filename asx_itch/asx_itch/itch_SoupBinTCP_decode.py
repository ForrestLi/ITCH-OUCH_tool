import itch_SoupBinTCP_messages as im


def decode_iter_msg(raw):
    raw_len = len(raw)
    offset = 0
    while offset < raw_len:
        d, msg_len = im.decode(raw, offset)
        if msg_len == -1:
            return
        offset += msg_len
        yield d, msg_len


def decode(raw):
    '''
        yield (dict, message length including the packet length field)
    '''
    for d, msg_len in decode_iter_msg(raw):
        yield d, msg_len
