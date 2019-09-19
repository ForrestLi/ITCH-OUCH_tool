import struct
import data_messages as dm


MSG_BLOCK = struct.Struct('!Hc')


class SoupBinTCPMsg:
    @classmethod
    def decode_zip_name(cls, raw, offset=0):
        d = cls.STRUCT.unpack_from(raw, offset)
        return dict(zip(cls.FIELDS, d))

    @staticmethod
    def decode_seq_num(raw):
        raw = raw.lstrip(b' ')
        return int.from_bytes(raw, byteorder='big')


class ServerHeartBeatPktMsg(SoupBinTCPMsg):
    STRUCT = struct.Struct('!c')
    FIELDS = ['Packet Type']


class LoginRequestPktMsg(SoupBinTCPMsg):
    STRUCT = struct.Struct('!c6s10s10s20s')
    FIELDS = [
        'Packet Type',
        'Username',
        'Password',
        'Requested Session',
        'Requested Sequence Number']


class LoginAcceptedPktMsg(SoupBinTCPMsg):
    STRUCT = struct.Struct('!c10s20s')
    FIELDS = ['Packet Type', 'Session', 'Sequence Number']


MSG_TYPE_STRUCT_MAP = {
    b'H': ServerHeartBeatPktMsg,
    b'A': LoginAcceptedPktMsg,
    b'L': LoginRequestPktMsg}


def decode(raw, offset=0):
    '''
        decode one message
        return (dict, the message len including the header packet length)
    '''
    block_len, msg_type = MSG_BLOCK.unpack_from(raw, offset)
    offset += 2
    if block_len <= 0:
        raise ValueError(
            'block len error: ',
            'raw',
            raw,
            'block len',
            block_len,
            'msg type',
            msg_type,
            'offset',
            offset)
    if offset + block_len > len(raw):
        return {'Not enough len, len=': block_len, 'offset': offset,
                'raw len': len(raw),
                'remain': raw[offset:offset+block_len]}, -1
    if msg_type == b'S':
        data_msg_type = raw[offset + 1:offset+2]
        d_decoded = dm.decode_msg(raw, data_msg_type, offset+1)
        return {'Message Type:': b'S', 'len': block_len,
                'decode': d_decoded}, block_len + 2
    elif msg_type in MSG_TYPE_STRUCT_MAP:
        struct_ = MSG_TYPE_STRUCT_MAP[msg_type]
        try:
            d = struct_.decode_zip_name(raw, offset)
            if hasattr(struct_, 'POST_PROCESSING'):
                for k, xform in struct_.POST_PROCESSING.items():
                    d[k] = xform(d[k])
            return d, block_len + 2
        except struct.error as e:
            raise Exception(
                'raw:', raw[offset:],
                ', raw len', len(raw[offset:])) from e
    else:
        return {'unknown': '', 'offset': offset, 'block_len': block_len,
                'msg_type': msg_type, 'raw_len': len(raw),
                'try': raw[offset:offset+block_len]}, block_len + 2
