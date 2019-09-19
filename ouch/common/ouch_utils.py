from test_utils import *

class OUCHClientChecker(GenericChecker):
    tif2ouch={ None: None, 'Norm': b'0', 'IOC': b'3', 'FOK': b'4' }
    
    def __init__(self, **kwargs):
        super(OUCHClientChecker, self).__init__(**kwargs)
        self.ouch_client = kwargs['ouch_client']
        self.mxsim = kwargs['mxsim']
        
    @overrides
    def newOrder(self, order, **kwargs):
        if not kwargs.get('dk', False):
            kwargs['clOrdID'] = self.ouch_client.sendEnterOrder(
                orderToken=kwargs.get('clOrdID'),
                orderBookID=int(kwargs.get('security').symbol) if kwargs.get('security') is not None else None,
                side=kwargs.get('side'),
                quantity=kwargs.get('orderQty'),
                price=kwargs.get('orderPrice'),
                timeInForce=self.tif2ouch[kwargs.get('timeInForce')],
                )
        super(OUCHClientChecker, self).newOrder(order, **kwargs)
        return self
        
    @overrides
    def ordered(self, order, **kwargs):
        msg = self.ouch_client.receiveMsg()
        assert(self.ouch_client.ouch_msg.OrderAccepted in msg)
        ordered = msg[self.ouch_client.ouch_msg.OrderAccepted]
        if 'orderID2' not in kwargs:
            kwargs['orderID2'] = ordered.OrderID
        super(OUCHClientChecker, self).ordered(order, **kwargs)
        clOrdID = kwargs.get('clOrdID', order.clOrdID)
        orderID2 = kwargs.get('orderID2', order.orderID2)
        security = kwargs.get('security', order.security)
        side = kwargs.get('side', order.side)
        orderQty = kwargs.get('orderQty', order.orderQty)
        orderPrice = kwargs.get('orderPrice', order.orderPrice)
        timeInForce = kwargs.get('timeInForce', order.timeInForce)
        if clOrdID is not None:
            assert(ordered.OrderToken == clOrdID)
        if orderID2 is not None:
            assert(ordered.OrderID == orderID2)
        if security is not None:
            assert(str(ordered.OrderBookID) == security.symbol)
        if side is not None:
            assert(ordered.Side == side)
        if orderQty is not None:
            assert(ordered.Quantity == orderQty)
        if orderPrice is not None:
            assert(ordered.Price == orderPrice)
        if timeInForce is not None:
            assert(ordered.TimeInForce == self.tif2ouch[timeInForce])
        return self
            
    @overrides
    def reject(self, order, **kwargs):
        msg = self.ouch_client.receiveMsg()
        assert(self.ouch_client.ouch_msg.OrderRejected in msg)
        super(OUCHClientChecker, self).reject(order, **kwargs)
        reject = msg[self.ouch_client.ouch_msg.OrderRejected]
        clOrdID = kwargs.get('clOrdID', order.clOrdID)
        if clOrdID is not None:
            assert(reject.OrderToken == clOrdID)
        return self
            
    @overrides
    def modify(self, order, **kwargs):
        orderToken = self.ouch_client.sendReplaceOrder(
            existingOrderToken=kwargs.get('origClOrdID', order.clOrdID),
            replacementOrderToken=kwargs.get('clOrdID'),
            quantity=kwargs.get('orderQty'),
            price=kwargs['orderPrice'],
            )
        kwargs['clOrdID'] = orderToken
        super(OUCHClientChecker, self).modify(order, **kwargs)
        return self
        
    @overrides
    def modified(self, order, **kwargs):
        msg = self.ouch_client.receiveMsg()
        assert(self.ouch_client.ouch_msg.OrderReplaced in msg)
        origClOrdID = kwargs.get('origClOrdID', order.prevClOrdID)
        super(OUCHClientChecker, self).modified(order, **kwargs)
        modified = msg[self.ouch_client.ouch_msg.OrderReplaced]
        clOrdID = kwargs.get('clOrdID', order.clOrdID)
        orderID2 = kwargs.get('orderID2', order.orderID2)
        security = kwargs.get('security', order.security)
        side = kwargs.get('side', order.side)
        orderQty = kwargs.get('orderQty', order.orderQty)
        orderPrice = kwargs.get('orderPrice', order.orderPrice)
        timeInForce = kwargs.get('timeInForce', order.timeInForce)
        if origClOrdID is not None:
            assert(modified.PreviousOrderToken == origClOrdID)
        if clOrdID is not None:
            assert(modified.ReplacementOrderToken == clOrdID)
        if orderID2 is not None:
            assert(modified.OrderID == orderID2)
        if security is not None:
            assert(str(modified.OrderBookID) == security.symbol)
        if side is not None:
            assert(modified.Side == side)
        if orderQty is not None:
            assert(modified.Quantity == orderQty)
        if orderPrice is not None:
            assert(modified.Price == orderPrice)
        if timeInForce is not None:
            assert(modified.TimeInForce == self.tif2ouch[timeInForce])
        return self
            
    @overrides
    def modReject(self, order, **kwargs):
        super(OUCHClientChecker, self).modReject(order, **kwargs)
        msg = self.ouch_client.receiveMsg()
        assert(self.ouch_client.ouch_msg.OrderRejected in msg)
        modReject = msg[self.ouch_client.ouch_msg.OrderRejected]
        origClOrdID = kwargs.get('origClOrdID', order.clOrdID)
        if origClOrdID is not None:
            assert(modReject.OrderToken == origClOrdID)
        return self
            
    @overrides
    def cancel(self, order, **kwargs):
        self.ouch_client.sendCancelOrder(
            orderToken=kwargs.get('clOrdID', order.clOrdID),
            )
        super(OUCHClientChecker, self).cancel(order, **kwargs)
        return self
        
    @overrides
    def canceled(self, order, **kwargs):
        super(OUCHClientChecker, self).canceled(order, **kwargs)
        msg = self.ouch_client.receiveMsg()
        assert(self.ouch_client.ouch_msg.OrderCancelled in msg)
        canceled = msg[self.ouch_client.ouch_msg.OrderCancelled]
        assert(canceled.CancelReason == 1)
        clOrdID = kwargs.get('clOrdID', order.clOrdID)
        orderID2 = kwargs.get('orderID2', order.orderID2)
        security = kwargs.get('security', order.security)
        side = kwargs.get('side', order.side)
        if clOrdID is not None:
            assert(canceled.OrderToken == clOrdID)
        if orderID2 is not None:
            assert(canceled.OrderID == orderID2)
        if security is not None:
            assert(str(canceled.OrderBookID) == security.symbol)
        if side is not None:
            assert(canceled.Side == side)
        return self
            
    @overrides
    def cxlReject(self, order, **kwargs):
        super(OUCHClientChecker, self).cxlReject(order, **kwargs)
        msg = self.ouch_client.receiveMsg()
        assert(self.ouch_client.ouch_msg.OrderRejected in msg)
        cxlReject = msg[self.ouch_client.ouch_msg.OrderRejected]
        if kwargs.get('clOrdID', order.clOrdID) is not None:
            assert(cxlReject.OrderToken == kwargs.get('clOrdID', order.clOrdID))
        return self
            
    @overrides
    def fill(self, order, **kwargs):
        orderID2 = kwargs.get('orderID2', order.orderID2)
        self.mxsim.fill(orderID2, kwargs['execQty'], kwargs['execPrice'])
        super(OUCHClientChecker, self).fill(order, **kwargs)
        msg = self.ouch_client.receiveMsg()
        assert(self.ouch_client.ouch_msg.OrderExecuted in msg)
        fill = msg[self.ouch_client.ouch_msg.OrderExecuted]
        clOrdID = kwargs.get('clOrdID', order.clOrdID)
        security = kwargs.get('security', order.security)
        if clOrdID is not None:
            assert(fill.OrderToken == clOrdID)
        if security is not None:
            assert(str(fill.OrderBookID) == security.symbol)
        if kwargs.get('execQty', None) is not None:
            assert(fill.TradedQuantity == kwargs['execQty'])
        if kwargs.get('execPrice', None) is not None:
            assert(fill.TradePrice == kwargs['execPrice'])
        if kwargs.get('execID2', None) is not None:
            assert(fill.MatchID == kwargs['execID2'])
        return self
            
    @overrides
    def bust(self, order, **kwargs):
        raise OperationNotSupportedError()
            
    @overrides
    def expire(self, order, **kwargs):
        raise OperationNotSupportedError()
            
    @overrides
    def dfd(self, order, **kwargs):
        raise OperationNotSupportedError()

