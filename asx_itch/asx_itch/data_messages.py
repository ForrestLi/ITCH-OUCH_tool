import struct


class MarketMsg:
    @classmethod
    def decode_zip_name(cls, raw, offset=0):
        d = cls.STRUCT.unpack_from(raw, offset)
        return dict(zip(cls.FIELDS, d))

    @staticmethod
    def decode_matchID(raw):
        return int.from_bytes(raw, byteorder='big')

    def __init__(self, arg_list, validate=True):
        self.arg_list = arg_list
        if validate:
            self.pack()

    def pack(self, with_mt=True):
        if with_mt:
            return self.STRUCT.pack(self.MT, *self.arg_list)
        else:
            return self.STRUCT.pack(*self.arg_list)


class TradeMsg(MarketMsg):
    MT = b'P'
    STRUCT = struct.Struct('!cl12scQLl7s7scc')
    FIELDS = [
        'Message Type',
        'Timestamp Nanoseconds',
        'Match ID',
        'Side',
        'Quantity',
        'Order Book ID',
        'Trade Price',
        'Participant ID, owner',
        'Participant ID, counterparty',
        'Printable',
        'Occurred at Cross']
    POST_PROCESSING = {'Match ID': MarketMsg.decode_matchID}


class OrderExecutedMsg(MarketMsg):
    MT = b'E'
    STRUCT = struct.Struct('!cLQLcQ12s7s7s')
    FIELDS = [
        'Message Type',
        'Timestamp Nanoseconds',
        'Order ID',
        'Order Book ID',
        'Side',
        'Executed Quantity',
        'Match ID',
        'Participant ID, owner',
        'Participant ID, counterparty']
    POST_PROCESSING = {'Match ID': MarketMsg.decode_matchID}


class OrderExecutedWithPriceMsg(MarketMsg):
    MT = b'C'
    STRUCT = struct.Struct('!cLQLcQ12s7s7slcc')
    FIELDS = [
        'Message Type',
        'Timestamp Nanoseconds',
        'Order ID',
        'Order Book ID',
        'Side',
        'Executed Quantity',
        'Match ID',
        'Participant ID, owner',
        'Participant ID, counterparty',
        'Trade Price',
        'Occurred at Cross',
        'Printable']
    POST_PROCESSING = {'Match ID': MarketMsg.decode_matchID}


class AuctionEquilibriumPriceUpdateMsg(MarketMsg):
    MT = b'Z'
    STRUCT = struct.Struct('!cLLQQlllQQ')
    FIELDS = [
        'Message Type',
        'Timestamp Nanoseconds',
        'Order Book ID',
        'Bid Quantity',
        'Ask Quantity',
        'Equilibrium Price',
        'Best Bid Price',
        'Best Ask Price',
        'Best Bid Quantity',
        'Best Ask Quantity']


class OrderDeleteMsg(MarketMsg):
    MT = b'D'
    STRUCT = struct.Struct('!cLQLc')
    FIELDS = [
        'Message Type',
        'Timestamp Nanoseconds',
        'Order ID',
        'Order Book ID',
        'Side']


class SecondsMsg(MarketMsg):
    MT = b'T'
    STRUCT = struct.Struct('!cL')
    FIELDS = ['Message Type', 'Second']


class OrderBookDirectoryMsg(MarketMsg):
    MT = b'R'
    STRUCT = struct.Struct('!cLL32s32s12sB3sHHLLLQ')
    FIELDS = [
        'Message Type',
        'Timestamp Nanoseconds',
        'Order Book ID',
        'Symbol',
        'Long Name',
        'ISIN',
        'Financial Product',
        'Trading Currency',
        'Number of decimals in Price',
        'Number of decimals in Nominal Value',
        'Odd Lot Size',
        'Round Lot Size',
        'Block Lot Size',
        'Nominal Value']


class AddOrderNoPIDMsg(MarketMsg):
    MT = b'A'
    STRUCT = struct.Struct('!cLQLcLQlHB')
    FIELDS = [
        'Message Type',
        'Timestamp Nanoseconds',
        'Order ID',
        'Order Book ID',
        'Side',
        'Order Book Position',
        'Quantity',
        'Price',
        'Exchange Order Type',
        'Lot Type'
        ]


class AddOrderWithPIDMsg(MarketMsg):
    MT = b'F'
    STRUCT = struct.Struct('!cLQLcLQlHB7s')
    FIELDS = [
        'Message Type',
        'Timestamp Nanoseconds',
        'Order ID',
        'Order Book ID',
        'Side',
        'Order Book Position',
        'Quantity',
        'Price',
        'Exchange Order Type',
        'Lot Type',
        'Participant ID'
        ]


class OrderReplaceMsg(MarketMsg):
    MT = b'U'
    STRUCT = struct.Struct('!cLQLcLQlH')
    FIELDS = [
        'Message Type',
        'Timestamp Nanoseconds',
        'Order ID',
        'Order Book ID',
        'Side',
        'Order Book Position',
        'Quantity',
        'Price',
        'Exchange Order Type'
        ]


class OrderBookStateMsg(MarketMsg):
    MT = b'O'
    STRUCT = struct.Struct('!cLL20s')
    FIELDS = [
        'Message Types',
        'Timestamp Nanoseconds',
        'Order Book ID',
        'State Name']


class TickSizeTableEntryMsg(MarketMsg):
    MT = b'L'
    STRUCT = struct.Struct('!cLLQll')
    FIELDS = [
        'Message Type',
        'Timestamp Nanoseconds',
        'Order Book ID',
        'Tick Size',
        'Price From',
        'Price To']


class EndOfSnapshotMsg(MarketMsg):
    MT = b'G'
    STRUCT = struct.Struct('!c20s')
    FIELDS = [
        'Message Type',
        'Sequence Number']


MSG_TYPE_STRUCT_MAP = {msg_cls.MT: msg_cls
                       for msg_cls in MarketMsg.__subclasses__()}


def decode_msg(raw, msg_type, offset=0):
    '''
        decode one message (starting with the message type)
    '''
    if msg_type in MSG_TYPE_STRUCT_MAP:
        struct_ = MSG_TYPE_STRUCT_MAP[msg_type]
        try:
            d = struct_.decode_zip_name(raw, offset)
            if hasattr(struct_, 'POST_PROCESSING'):
                for k, xform in struct_.POST_PROCESSING.items():
                    d[k] = xform(d[k])
            return d
        except struct.error as e:
            raise Exception(
                'raw:', raw[offset:],
                ', raw len', len(raw[offset:])) from e
    else:
        return {'error': f'offset = {offset}, msg_type={msg_type}, raw={raw}'}
