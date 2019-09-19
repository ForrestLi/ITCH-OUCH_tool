import data_messages as dm
import itch_MoldUDP64 as im
import datetime as dt

orderIDgen = iter(range(77, 10000000000))
orderBookID = 126690
side = b'B'
orderBookPos = 1
qty = 2222
price = 3333
etype = 4
lottype = 0
matchID = b'987654321012'


def genAdd(*, seqNo):
    now = dt.datetime.now().timestamp()
    now_sec = int(now)
    now_nsec = int((now - now_sec) * 1000000000)

    orderID = next(orderIDgen)
    c1 = im.pack(im.Header([b'0123456789', seqNo, 1]),
                 dm.SecondsMsg([now_sec]))
    c2 = im.pack(
        im.Header([b'0123456789', seqNo + 1, 1]),
        dm.AddOrderNoPIDMsg(
            [now_nsec, orderID,
             orderBookID, side, orderBookPos, qty, price, etype, lottype]))
    return c1, c2, orderID


def genDel(*, seqNo, orderID):
    now = dt.datetime.now().timestamp()
    now_sec = int(now)
    now_nsec = int((now - now_sec) * 1000000000)

    c1 = im.pack(im.Header([b'0123456789', seqNo, 1]),
                 dm.SecondsMsg([now_sec]))
    c2 = im.pack(
        im.Header([b'0123456789', seqNo + 1, 1]),
        dm.OrderDeleteMsg(
            [now_nsec, orderID, orderBookID, side]))
    return c1, c2


def genMod(*, price=999, qty=888, seqNo, orderID):
    now = dt.datetime.now().timestamp()
    now_sec = int(now)
    now_nsec = int((now - now_sec) * 1000000000)

    c1 = im.pack(im.Header([b'0123456789', seqNo, 1]),
                 dm.SecondsMsg([now_sec]))
    c2 = im.pack(
        im.Header([b'0123456789', seqNo + 1, 1]),
        dm.OrderReplaceMsg(
            [now_nsec, orderID, orderBookID, side, 7, qty, price, 4]))
    return c1, c2


def genFill(*, seqNo, orderID):
    now = dt.datetime.now().timestamp()
    now_sec = int(now)
    now_nsec = int((now - now_sec) * 1000000000)

    c1 = im.pack(im.Header([b'0123456789', seqNo, 1]),
                 dm.SecondsMsg([now_sec]))
    c2 = im.pack(
        im.Header([b'0123456789', seqNo + 1, 1]),
        dm.OrderExecutedMsg(
            [now_nsec, orderID, orderBookID, side, qty, matchID,
             b'AAAAAAA', b'BBBBBBB']))
    return c1, c2


def genTrade(*, price=545, qty=454, seqNo):
    now = dt.datetime.now().timestamp()
    now_sec = int(now)
    now_nsec = int((now - now_sec) * 1000000000)

    c1 = im.pack(im.Header([b'0123456789', seqNo, 1]),
                 dm.SecondsMsg([now_sec]))
    c2 = im.pack(
        im.Header([b'0123456789', seqNo + 1, 1]),
        dm.TradeMsg(
            [now_nsec, matchID, side, qty, orderBookID, price,
             b'AAAAAAA', b'BBBBBBB', b'Y', b'N']))
    return c1, c2


def genAuctionUpdate(*, bid=987, bidQty=876, ask=998, askQty=997,
                     lastBidQty=876, lastAskQty=877, eq_price=222, seqNo):
    now = dt.datetime.now().timestamp()
    now_sec = int(now)
    now_nsec = int((now - now_sec) * 1000000000)

    c1 = im.pack(im.Header([b'0123456789', seqNo, 1]),
                 dm.SecondsMsg([now_sec]))
    c2 = im.pack(
        im.Header([b'0123456789', seqNo + 1, 1]),
        dm.AuctionEquilibriumPriceUpdateMsg(
            [now_nsec, orderBookID, lastBidQty, lastAskQty, eq_price, bid,
             ask, bidQty, askQty]))
    return c1, c2


def debug(c):
    print('len', len(c), ':', c)
    d = im.decode(c, with_header=True)
    for k in d:
        print(k)
    print('-'*20)


# c1, c2 = genAdd(seqNo=74978)
#
# debug(c1)
# debug(c2)
