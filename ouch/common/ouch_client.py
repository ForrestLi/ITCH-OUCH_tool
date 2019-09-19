from __future__ import print_function
from collections import OrderedDict
from six.moves.queue import SimpleQueue as Queue
from six.moves.queue import Empty
import threading
import socket
import struct
import string
from ouch_msg import *
import time

def lowerName(name):
    """
    Turns UpperCamelCase to lowerCamelCase. If `name` starts with
    more than one upper case letter then these are considered
    an acronym.

    For example:
    > lowerName("OrderType")
    'orderType'
    > lowerName("OUCHOrderType")
    'ouchOrderType'
    """
    l = 0
    while l < len(name):
        if name[l] not in string.ascii_uppercase:
            break
        l += 1
    if l > 1:
        l -= 1
    return name[:l].lower() + name[l:]

class OUCHClient(object):
    ouch_msg = __import__('ouch_msg')
    scapy = __import__('scapy')

    common_argument_defaults = OrderedDict([
        ('Quantity', 1),
        ('Price', 1.0),
        ('ClientAccount', ''),
        ('CustomerInfo', ''),
        ('ExchangeInfo', ''),
        ('CapacityOfParticipant', 'A'),
        ('DirectedWholesale', 'N'),
        ('IntermediaryID', ''),
        ('OrderOrigin', ''),
        ('ShortSellQuantity', 1),
        ])
    enter_order_argument_defaults = OrderedDict(list(common_argument_defaults.items()) + [
        ('OrderBookID', 12345),
        ('Side', 'B'),
        ('TimeInForce', 0),
        ('ClearingParticipant', ''),
        ('CrossingKey', 1),
        ('OUCHOrderType', 'Y'),
        ('MinimumAcceptableQuantity', 0), # last because default depends on other fields
        ])
    replace_order_argument_defaults = OrderedDict(list(common_argument_defaults.items()) + [
        ('MinimumAcceptableQuantity', 0),
        ])
    all_argument_defaults = OrderedDict(enter_order_argument_defaults)

    def __init__(self, remoteIP, remotePort, localIP, localPort,
                 username, password, session, lastQuerySeqNo=0, lastNoticeSeqNo=0):
        self.remoteIP = remoteIP
        self.remotePort = remotePort
        self.localIP = localIP
        self.localPort = localPort
        self.username = username
        self.password = password
        self.session = session
        self.lastQuerySeqNo = lastQuerySeqNo
        self.lastNoticeSeqNo = lastNoticeSeqNo
        self.heartbeatTimeout = 1 # zero means no client heartbeats
        self.handleHeartbeats = True # filter server heartbeats from receiveMsg
        self.handlers = [self.defaultHandler] # functions to handle messages before receiveMsg
        self.prefix = 'OUCH' # auto order token prefix
        self.nextOrderToken = 1 # auto order token number
        for arg, default in self.all_argument_defaults.items():
            setattr(self, 'default' + arg, default)

    def start(self):
        print("Starting OUCH client %s:%d -> %s:%d" % \
              (self.localIP, self.localPort, self.remoteIP, self.remotePort))
        self.sendQueue = Queue()
        self.receiveQueue = Queue()
        self.heartbeatsStop = False
        self.lastSend = time.time()
        self.socket = socket.socket()
        self.sendThread = threading.Thread(target=self.sendThreadFunc)
        self.sendThread.daemon = True
        self.receiveThread = threading.Thread(target=self.receiveThreadFunc)
        self.receiveThread.daemon = True
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.localIP, self.localPort))
        for _ in range(13):
            try:
                self.socket.connect((self.remoteIP, self.remotePort))
                break
            except socket.error as e:
                if e.errno == 99:
                    print("Cannot connect: address taken")
                    time.sleep(10)
                    continue
                else: 
                    raise
        self.sendThread.start()
        self.receiveThread.start()

    def stop(self):
        print("Stopping OUCH client %s:%d -> %s:%d" % \
              (self.localIP, self.localPort, self.remoteIP, self.remotePort))
        self.sendQueue.put(None)
        if self.sendThread.is_alive():
            self.sendThread.join(1)
        self.socket.close()
        if self.receiveThread.is_alive():
            self.receiveThread.join(1)
#         if self.sendThread.isAlive or self.receiveThread.isAlive:
#             ts = (["send thread"] if self.sendThread.isAlive else []) + \
#                 (["receive thread"] if self.receiveThread.isAlive else [])
#             raise Exception("OUCH client %s:%d -> %s:%d: %s didn't terminate" % \
#               (self.localIP, self.localPort, self.remoteIP, self.remotePort,
#                ", ".join(ts)))

    def sendThreadFunc(self):
        lastSend = time.time()
        while True:
            try:
                msg = self.sendQueue.get(True, 1)
            except Empty:
                if self.heartbeatTimeout and \
                    time.time() > lastSend + self.heartbeatTimeout:
                    msg = SoupBinCommon()/ClientHeartbeat()
                else:
                    continue
            if msg is None:
                return
            msg = six.binary_type(msg)
            msgLen = len(msg)
            while msgLen:
                sent = self.socket.send(msg)
                lastSend = time.time()
                if sent == 0:
                    raise Exception("Socket closed unexpectedly")
                msgLen -= sent
                msg = msg[sent:]

    def sendMsg(self, msg):
        if SoupBinCommon not in msg:
            if all(layer not in msg for layer in (LoginRequest, LogoutRequest,
                  LoginAccepted, LoginRejected, ServerHeartbeat,
                  ClientHeartbeat, EndOfSession, SequencedData,
                  UnsequencedData)):
                if any(layer in msg for layer in (EnterOrder,
                      ReplaceOrder, CancelOrder, CancelByOrderID)):
                    msg = UnsequencedData()/msg
                else:
                    msg = SequencedData()/msg
            msg = SoupBinCommon()/msg
        #print('Sending {0!r}'.format(msg))
        self.sendQueue.put(msg)
        if UnsequencedData in msg:
            self.lastQuerySeqNo += 1

    def receiveThreadFunc(self):
        def receiveRaw(bytes):
            buf = six.binary_type()
            while len(buf) < bytes:
                chunk = self.socket.recv(bytes - len(buf))
                if len(chunk) == 0:
                    return None
                buf += chunk
            return buf

        hdrSize = len(SoupBinCommon())
        while True:
            buf = receiveRaw(hdrSize)
            if buf is None:
                return
            hdr = SoupBinCommon(buf)
            buf2 = receiveRaw(hdr.PacketLength - 1)
            if buf2 is None:
                self.socket.close()
                return
            msg = SoupBinCommon(buf + buf2)
            #print('Received {0!r}'.format(msg))
            for h in self.handlers:
                if h(msg):
                    break
            else:
                self.receiveQueue.put(msg)

    def defaultHandler(self, msg):
        if msg.PacketType == 'H':
            return self.handleHeartbeats
        return False

    def receiveMsg(self, timeout=10):
        msg = self.receiveQueue.get(True, timeout)
        if SequencedData in msg:
            self.lastNoticeSeqNo += 1
        return msg

    def sendLoginRequest(self):
        self.sendMsg(LoginRequest(
            Username=self.username,
            Password=self.password,
            RequestedSequenceNumber=self.lastNoticeSeqNo + 1))

    def sendLogoutRequest(self):
        self.sendMsg(LogoutRequest())

    def sendEnterOrder(self, orderToken=None, orderBookID=None, side=None,
                       quantity=None, price=None, timeInForce=None,
                       clientAccount=None, customerInfo=None, exchangeInfo=None,
                       clearingParticipant=None, crossingKey=None,
                       capacityOfParticipant=None, directedWholesale=None,
                       intermediaryID=None, orderOrigin=None,
                       ouchOrderType=None, shortSellQuantity=None,
                       minimumAcceptableQuantity=None):
        fields = {}
        if orderToken is None:
            orderToken = self.prefix + '{{0:0{0}d}}'.format(14 - len(self.prefix)).format(self.nextOrderToken)
            self.nextOrderToken += 1
        fields['OrderToken'] = orderToken
        for arg in self.enter_order_argument_defaults:
            if locals()[lowerName(arg)] is None:
                if arg == 'ShortSellQuantity' and side in ('B', 'S'):
                    fields[arg] = 0
                elif arg == 'MinimumAcceptableQuantity' and fields['TimeInForce'] == 4 and \
                     fields['OUCHOrderType'] in 'BC':
                    fields[arg] = fields['Quantity']
                else:
                    fields[arg] = getattr(self, 'default' + arg)
            else:
                fields[arg] = locals()[lowerName(arg)]
        self.sendMsg(EnterOrder(**fields))
        return fields['OrderToken']

    def sendReplaceOrder(self, existingOrderToken,
                         replacementOrderToken=None,
                         quantity=None, price=None,
                         clientAccount=None, customerInfo=None,
                         exchangeInfo=None, capacityOfParticipant=None,
                         directedWholesale=None, intermediaryID=None,
                         orderOrigin=None, shortSellQuantity=None,
                         minimumAcceptableQuantity=None):
        fields = {
            'ExistingOrderToken': existingOrderToken
        }
        if replacementOrderToken is None:
            replacementOrderToken = self.prefix + '{{0:0{0}d}}'.format(14 - len(self.prefix)).format(self.nextOrderToken)
            self.nextOrderToken += 1
        fields['ReplacementOrderToken'] = replacementOrderToken
        for arg in self.replace_order_argument_defaults:
            if locals()[lowerName(arg)] is None:
#                 if arg == 'ShortSellQuantity' and side in ('B', 'S'):
#                     fields[arg] = 0
#                 else:
                    fields[arg] = getattr(self, 'default' + arg)
            else:
                fields[arg] = locals()[lowerName(arg)]
        self.sendMsg(ReplaceOrder(**fields))
        return fields['ReplacementOrderToken']

    def sendCancelOrder(self, orderToken):
        self.sendMsg(CancelOrder(OrderToken=orderToken))

    def sendCancelByOrderID(self, orderID, orderBookID=None, side=None):
        if orderBookID is None:
            orderBookID = self.defaultOrderBookID
        if side is None:
            side = self.defaultSide
        self.sendMsg(CancelByOrderID(OrderBookID=orderBookID,
                                     Side=side,
                                     OrderID=orderID))
