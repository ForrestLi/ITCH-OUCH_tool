#!/usr/bin/env python

""" ASX OUCH Message Module\n \
"""

from scapy.all import *
from scapy_utils import *
import time

    
class PriceField(IntField):

    def i2m(self, pkt, x):
        return IntField.i2m(self, pkt, int(round(x * 100.0)))
    
    def m2i(self, pkt, s):
        return IntField.m2i(self, pkt, s) / 100.0

WENUMS = {

        'Side':         { 
                          'Buy':       'B',
                          'Sell':      'S',
                          'SellShort': 'T',
                          'Combo':     'C',
                        },

        'TIF':          { 
                          'Day':           0,
                          'Fill and Kill': 3, 
                          'Fill or Kill':  4, 
                        },

        'OrdStatus':    { 
                          'On book':             '1',
                          'Not on book':         '2',
                          'OUCH ownership lost': '99',
                        },

        'CancelReason': { 
                          'Cancelled by user':                                      '1',
                          'Order inactivated due to connection loss':               '4',
                          'Fill and Kill order that was deleted in an auction':     '9',
                          'Order deleted by ASX on behalf of the participant':      '10',
                          'Deleted by system due to instrument session change':     '20',
                          'Inactivated by system due to instrument session change': '21',
                          'Inactivated Day order':                                  '24',
                        },

        'OrderType':    { 
                          'Limit order':                                              'Y',
                          'Centre Point Order (mid-point only)':                      'N',
                          'Center Point Order (dark limit)':                          'D',
                          'Sweep order':                                              'S',
                          'Sweep order (dual posted)':                                'P',
                          'Mid-point Centre Point Block Order with single fill MAQ':  'B',
                          'Dark limit Centre Point Block Order with single fill MAQ': 'F',
                          'Centre Point Sweep order with single fill MAQ':            'T',
                          'Any Price Block order':                                    'C',
                          'Any Price Block order with single fill MAQ':               'E',
                        },
                       
        'DealSource':   { 
                          'Single series to single series auto-matched during continuous trading':                 '1',
                          'Single series to single series auto-matched during an auction':                         '20',
                          'Tailor made combination match':                                                         '36',
                          'Combination matched outright legs':                                                     '43', 
                          'Booked transaction resulting from Unintentional Crossing Prevention':                   '44',
                          'Booked transaction resulting from Unintentional Crossing Prevention during an auction': '45',
                          'Centre Point Preference Matched trade':                                                 '46',
                          'Centre Point trade':                                                                    '47',
                          'Centre Point booked transaction resulting from Unintentional Crossing Prevention':      '48',
                          'Reserved for future use':                                                               '49',
                          'Block trade':                                                                           '50',
                          'Preference Block Trade':                                                                '51',
                        },

        'PassiveInd' :  { 
                          'Passive execution':    '0',
                          'Aggressive execution': '1',
                        },

        'CrossDealCap': { 
                          'Order Not Crossed':                                     '00',
                          'Orded crossed with a Principal order':                  '01',
                          'Order crossed with an Agency order':                    '10',
                          'Order crossed with a Mixed Agency and Principal order': '11',
                        },

        'RejectReasonCode':  { 
                          'Not Authorised. There was an invalid username and password combination in the Login Request Message.':          'A',
                          'Session not available. The Requested Session in the Login Request Packet was either invalid or not available.': 'S',
                        },

        'CancelReason': {
                        'Cancelled by user':          '1',
                        'Order inactivated due to connection loss': '4',
                        'Fill and Kill order that was deleted in an auction': '9',
                        'Order deleted by ASX on behalf of the customer': '10',
                        'Deleted by system due to instrument session change': '20',
                        'Inactivated by system due to instrument session change': '21',
                        'Inactivated Day order': '24',
                        },

        'PacketTypeUp':   { 
                          # ------------SoupBin-----------                        
                          # Client side                       
                          'LoginRequest':    'L',
                          'ClientHeartbeat': 'R',
                          'LogoutRequest':   'O',                         
                          'UnsequencedData': 'U',       
                        },
                        
        'PacketTypeDown':   { 
                          # ------------SoupBin-----------
                          # Server side
                          #'Debug':           '+',
                          'LoginAccept':     'A',
                          'LoginReject':     'J',
                          'ServerHeartbeat': 'H',
                          'EndOfSession':    'Z',
                          'SequencedData':   'S',                         
                        },

        'PacketType':   { 
                          # ------------SoupBin-----------
                          # Server side
                          #'Debug':           '+',
                          'Login Accepted':   'A',
                          'Login Rejected':   'J',
                          'Server Heartbeat': 'H',
                          'End Of Session':   'Z',
                          'Sequenced Data':   'S',                         
                          # Client side                       
                          'Login Request':    'L',
                          'Client Heartbeat': 'R',
                          'Logout Request':   'O',                         
                          'Unsequenced Data': 'U',       
                        },
  
        'RequestType':       {
                          # ------------OUCH Request----------- 
                          'Enter Order':      'O',
                          'Replace Order':    'U',
                          'Cancel Order':     'X',
                          'Cancel By Order ID': 'Y',
                         },

        'ResponseType':      {
                          # ------------OUCH Response-----------   
                          'Order Accepted':   'A',
                          'Order Replaced':   'U',
                          'Order Rejected':   'J',
                          'Order Cancelled':  'C',
                          'Order Executed':   'E',
                        },
}

RENUMS = {}
for tag, vals in WENUMS.items():
    cur = RENUMS.setdefault(tag, {})
    for k, v in vals.items():
        cur[v] = k
                
################## Soupbin layer #################

class SoupBinCommon(Packet):
    name = 'SoupBinCommon'
    fields_desc = [
        ShortField('PacketLength', None ),                            #Integer Big Endian
        CharEnumField('PacketType', ' ', RENUMS['PacketType'])     #ASCII Character
        ]
    
    # calc and insert data len
    def post_build(self, p, payload):                             #Data length first field
        if self.PacketLength is None:
            l = len(p)+len(payload)-2
            p = struct.pack(">H", l ) + p[2:]                     #>H = Integer Big Endian format
        return p+payload

class LoginRequest(Packet):
    name = 'LoginRequest'
    fields_desc = [
        RPaddedStrFixedLenField('Username', None, 6),                   #ASCII Alphanumeric
        RPaddedStrFixedLenField('Password', None, 10),                 #ASCII Alphanumeric
        RPaddedStrFixedLenField('RequestedSession', None, 10),         #ASCII Alphanumeric
        LPaddedAsciiIntFixedLenField('RequestedSequenceNumber', None, 20)   #Numeric encoded as ASCII 
        ]

class LogoutRequest(Packet):
    name = 'LogoutRequest'

class LoginAccepted(Packet):
    name = 'LoginAccepted'
    fields_desc = [
        RPaddedStrFixedLenField('Session', None, 10),                  #ASCII Alphanumeric
        LPaddedAsciiIntFixedLenField('SequenceNumber', None, 20)            #Numeric   
        ]

class LoginRejected(Packet):
    name = 'LoginRejected'
    fields_desc = [
        CharEnumField('RejectReasonCode', ' ', RENUMS['RejectReasonCode'])          #ASCII Alphanumeric   
        ]

class ServerHeartbeat(Packet):
    name = 'ServerHeartbeat'

class ClientHeartbeat(Packet):
    name = 'ClientHeartbeat'
    
class EndOfSession(Packet):
    name = 'EndOfSession'

class SequencedData(Packet):
    name = 'SequencedData'	
    fields_desc = [
        CharEnumField('MessageType', ' ', RENUMS['ResponseType']),
        ]	
class UnsequencedData(Packet):
    name = 'UnsequencedData'
    fields_desc = [
        CharEnumField('MessageType', ' ', RENUMS['RequestType']),
        ]
	
################## Ouch payload #################

class EnterOrder(Packet):
    name = 'EnterOrder'
    fields_desc = [
        StrFixedLenField('OrderToken', ' '*14, 14),
        IntField('OrderBookID', 0 ),
        CharEnumField('Side', 'B', RENUMS['Side']),
        LongField('Quantity', 0),
        PriceField('Price', 0),
        ByteEnumField('TimeInForce', 0, RENUMS['TIF']),
        ByteField('OpenClose', 0),
        RPaddedStrFixedLenField('ClientAccount', None, 10),	
        RPaddedStrFixedLenField('CustomerInfo', None, 15),	
        RPaddedStrFixedLenField('ExchangeInfo', None, 32),
        RPaddedStrFixedLenField('ClearingParticipant', ' ', 1),	
        IntField('CrossingKey', 0),
        StrFixedLenField('CapacityOfParticipant', 'A', 1),
        StrFixedLenField('DirectedWholesale', 'N', 1),
        RPaddedStrFixedLenField('ExecutionVenue', None, 4),	
        RPaddedStrFixedLenField('IntermediaryID', None, 10),			
        RPaddedStrFixedLenField('OrderOrigin', None, 20),
        RPaddedStrFixedLenField('Filler', None, 8),		
        CharEnumField('OUCHOrderType', 'Y', RENUMS['OrderType']),
        LongField('ShortSellQuantity', 0),		
        LongField('MinimumAcceptableQuantity', 0),	
        ]

class ReplaceOrder(Packet):
    name = 'ReplaceOrder'
    fields_desc = [
        RPaddedStrFixedLenField('ExistingOrderToken', None, 14),
        RPaddedStrFixedLenField('ReplacementOrderToken', None, 14),
        LongField('Quantity', 0),
        PriceField('Price', 0),
        ByteField('OpenClose', 0),
        RPaddedStrFixedLenField('ClientAccount', None, 10,'\00'),	
        RPaddedStrFixedLenField('CustomerInfo', None, 15,'\00'),	
        RPaddedStrFixedLenField('ExchangeInfo', None, 32,'\00'),
        StrFixedLenField('CapacityOfParticipant', 'A', 1),
        StrFixedLenField('DirectedWholesale', 'N', 1),
        RPaddedStrFixedLenField('ExecutionVenue', None, 4),    
        RPaddedStrFixedLenField('IntermediaryID', None, 10),            
        RPaddedStrFixedLenField('OrderOrigin', None, 20),
        RPaddedStrFixedLenField('Filler', None, 8),        
        LongField('ShortSellQuantity', 0),        
        LongField('MinimumAcceptableQuantity', 0),    
        ]

class CancelOrder(Packet):
    name = 'CancelOrder'
    fields_desc = [
        RPaddedStrFixedLenField('OrderToken', None, 14),
        ]		

class CancelByOrderID(Packet):
    name = 'CancelByOrderID'
    fields_desc = [
        IntField('OrderBookID', 0),
        StrFixedLenField('Side', 'B', 1),
        LongField('OrderID', 0),
        ]


#################### Responses  ##################

class OrderAccepted(Packet):
    name = 'OrderAccepted'
    fields_desc = [
        LongField('Timestamp', 0),
        RPaddedStrFixedLenField('OrderToken', None, 14),
        IntField('OrderBookID', 0),
        StrFixedLenField('Side', 'B', 1),
        LongField('OrderID', 0),   
        LongField('Quantity', 0),
        PriceField('Price', 0),
        ByteField('TimeInForce', 0),
        ByteField('OpenClose', 0),
        RPaddedStrFixedLenField('ClientAccount', None, 10),
        ByteField('OrderState', 0),
        RPaddedStrFixedLenField('CustomerInfo', None, 15),
        RPaddedStrFixedLenField('ExchangeInfo', None, 32),
        RPaddedStrFixedLenField('ClearingParticipant', ' ', 1),
        IntField('CrossingKey', 0),
        RPaddedStrFixedLenField('CapacityOfParticipant', 'A', 1),
        RPaddedStrFixedLenField('DirectedWholesale', 'N', 1),
        RPaddedStrFixedLenField('ExecutionVenue', None, 4),    
        RPaddedStrFixedLenField('IntermediaryID', None, 10),            
        RPaddedStrFixedLenField('OrderOrigin', None, 20),
        RPaddedStrFixedLenField('Filler', None, 8),        
        CharEnumField('OUCHOrderType', 'Y', RENUMS['OrderType']),
        LongField('ShortSellQuantity', 0),        
        LongField('MinumAcceptableQuantity', 0),    
        ]

class OrderReplaced(Packet):
    name = 'OrderReplaced'
    fields_desc = [
        LongField('Timestamp', 0),
        RPaddedStrFixedLenField('ReplacementOrderToken', None, 14),
        RPaddedStrFixedLenField('PreviousOrderToken', None, 14),
        IntField('OrderBookID', 0 ),
        StrFixedLenField('Side', 'B', 1),
        LongField('OrderID', 0),
        LongField('Quantity', 0),
        PriceField('Price', 0),
        ByteField('TimeInForce', 0),
        ByteField('OpenClose', 0),
        RPaddedStrFixedLenField('ClientAccount', None, 10),
        ByteField('OrderState', 0),
        RPaddedStrFixedLenField('CustomerInfo', None, 15),
        RPaddedStrFixedLenField('ExchangeInfo', None, 32),
        RPaddedStrFixedLenField('ClearingParticipant', ' ', 1),
        IntField('CrossingKey', 0),
        RPaddedStrFixedLenField('CapacityOfParticipant', 'A', 1),
        RPaddedStrFixedLenField('DirectedWholesale', 'N', 1),
        RPaddedStrFixedLenField('ExecutionVenue', None, 4),    
        RPaddedStrFixedLenField('IntermediaryID', None, 10),            
        RPaddedStrFixedLenField('OrderOrigin', None, 20),
        RPaddedStrFixedLenField('Filler', None, 8),        
        CharEnumField('OUCHOrderType', 'Y', RENUMS['OrderType']),
        LongField('ShortSellQuantity', 0),        
        LongField('MinumAcceptableQuantity', 0),    
        ]

class OrderCancelled(Packet):
    name = 'OrderCancelled'
    fields_desc = [
        LongField('Timestamp', 0),
        RPaddedStrFixedLenField('OrderToken', None, 14),
        IntField('OrderBookID', 0),
        StrFixedLenField('Side', 'B', 1),
        LongField('OrderID', 0),
        ByteField('CancelReason', 0),        
        ]
		
class OrderRejected(Packet):
    name = 'Rejected'
    fields_desc = [
        LongField('Timestamp', 0),
        RPaddedStrFixedLenField('OrderToken', None, 14),
        IntField('RejectCode', 0),    
        ]

class OrderExecuted(Packet):
    name = 'OrderExecuted'
    fields_desc = [
        LongField('Timestamp', 0),
        RPaddedStrFixedLenField('OrderToken', None, 14),
        IntField('OrderBookID', 0),
        LongField('TradedQuantity', 0),
        PriceField('TradePrice', 0),
        StrFixedLenField('MatchID', ' '*12, 12), #12 byte numeric	- need to determine a method to handle this...
        ShortField('DealSource', 0),
        ByteField('MatchAttributes', 0),		
        ]

# bindings to payload type for proper dissection

#SoupBin
#bind_layers(SoupBinCommon, 'Debug', PacketType='+')
bind_layers(SoupBinCommon, LoginAccepted, PacketType=b'A')
bind_layers(SoupBinCommon, LoginRejected, PacketType=b'J')
bind_layers(SoupBinCommon, ServerHeartbeat, PacketType=b'H')
bind_layers(SoupBinCommon, EndOfSession, PacketType=b'Z')
bind_layers(SoupBinCommon, SequencedData, PacketType=b'S')

bind_layers(SoupBinCommon, LoginRequest, PacketType=b'L')
bind_layers(SoupBinCommon, ClientHeartbeat, PacketType=b'R')
bind_layers(SoupBinCommon, LogoutRequest, PacketType=b'O')
bind_layers(SoupBinCommon, UnsequencedData, PacketType=b'U')

#OUCH
#Requests
bind_layers(UnsequencedData, EnterOrder, MessageType=b'O')
bind_layers(UnsequencedData, ReplaceOrder, MessageType=b'U')
bind_layers(UnsequencedData, CancelOrder, MessageType=b'X')
bind_layers(UnsequencedData, CancelByOrderID, MessageType=b'Y')

#Responses
bind_layers(SequencedData, OrderAccepted, MessageType=b'A')
bind_layers(SequencedData, OrderReplaced, MessageType=b'U')
bind_layers(SequencedData, OrderCancelled, MessageType=b'C')
bind_layers(SequencedData, OrderRejected, MessageType=b'J')
bind_layers(SequencedData, OrderExecuted, MessageType=b'E')

# Raptor log parser
if __name__ == '__main__':
    from struct import *
    import sys

    lines = sys.stdin.readlines()
    p = lines[0].rstrip()
    n = len(p)
    
    headerfmt = '<iiIHH'
    k = 0 # index (pointer)
    j = calcsize(headerfmt) #size of header
    result = ''
    print("log checking routine") 
    while k<n:
        header = p[k:k+j]
        s = unpack(headerfmt, header) #s[0] is the datalen after header of size j
        # extract OUCH message
        msg = p[k+j: k+j+abs(s[0])]
        k = k+j+abs(s[0])

        x.show()
