import itertools
import math
import quickfix
from overrides import overrides
import pytest
from hamcrest import *
from hamcrest_utils import *



def validateTimestamps(tslist):
    """
    Asserts that all time stamps in `tslist` are within 30 seconds from now.
    """
#     for i, ts in enumerate(tslist):
#         assert timeStampDeltaNow(ts) <= 30
    pass


class Order(object):
    """
    Stores information about an order. Default attributes are `checker`, `orderStatus`, 
    `side`, `security`, `orderQty`, `execQty`, (read-only) `openQty`, `orderPrice`, 
    (optional) `clOrdID`, (optional) `orderID2` and (optional) `timeInForce`.
    The checker may add additional properties.

    For certain attributes a modifcation history is kept. These attributes are
    defined in ``self.checker._modifyAttributes``. For these attributes the oldest,
    non-acknowledged version is available as `old<name>` (for example `oldOrderQty`,
    `oldOrderPrice`, `oldClOrdID`), the previous version is available as `prev<name>`
    (for example `prevOrderQty`, `prevOrderPrice`, `prevClOrdID`).

    Usual usage:

    1. Send an order with your actual test client.
    2. Create the order instance with a given checker instance.
    3. Perform some actions with your actual test client.
    4. Call the corresponding method(s) to tell the checker what was supposed to
       happen.
    5. Call `verify`.

    .. note: All methods return the order object. So multiple calls can be 
             chained together.

    .. warning: All methods and the constructor must be called with keyword
               arguments only. This ensures easy extensibilty.

               Checkers can be composed by multiple inheritance. Arguments
               are treated as a dictionary and simply passed from one class
               to the next. Constructors have to be called with named
               arguments for the same reason. 

    Example::

        client.sendOrder(qty=10, price=100, symbol=..., ...)
        o = Order(checker, orderQty=10, orderPrice=100, security=..., ...).verify()
        client.sendModify(...)
        o.modify(...).modifed().verify()
        mxsim.fill(...)
        o.fill(...).verify()
    """

    def __init__(self, checker, **kwargs):
        """
        Creates a new order object and calls ``checker.newOrder`` to initialize it.

        :param order: the order object
        :type order: Order
        :param security: The security to be traded.
        :type security: a security object from the `securities` fixture
        :param side: Buy or sell.
        :type side: ``'B'`` or ``'S'``
        :param orderQty: The quantity to be traded.
        :type orderQty: int
        :param orderPrice: Trade price for limit orders, ``None`` for market orders.
        :type orderPrice: float or ``None``
        :param clOrdID: (optional) Client order id.
        :type clOrdID: str
        :param destClOrdID: (optional) Market client order id.
        :type destClOrdID: str
        :param timeInForce: (optional) Time in force of the order.
        :type timeInForce: one of ``"Norm"``, ``"IOC"``, ``"FOK"``, ``"AtOpn"``, 
                           ``"AtCls"``, ``"GTC"``, ``"GTD"``, ``"GTX"``, 
                           ``"GTHX"``, ``"AtX"`` or ``"Session"``
        :param dk: dk order, in which case all arguments are optional. Default ``False``.
        :type dk: bool
        :param clientID: (optional) Raptor client name
        :type clientID: str
        :param accountID: (optional) Raptor account name
        :type accountID: str

        .. warning: Arguments, except `checker`, must be given as keyword arguments.
        """
        self.checker = checker
        self.queue = [{}]  # modify/modReject queue
        checker.newOrder(self, **kwargs)

    def __str__(self):
        if hasattr(self, 'orderStatus'):
            return "<%s %s %d %s at %f%s%s>" % (
                self.orderStatus,
                "sell" if self.side == 'S' else 
                "buy" if self.side == 'B' else repr(self.side),
                self.orderQty if self.orderQty is not None else 0,
                self.security.symbol if self.security is not None else repr(None),
                self.orderPrice if self.orderPrice is not None else 0.0,
                " clOrdID=%s" % self.clOrdID if self.clOrdID is not None else "",
                " orderID2=%s" % self.orderID2 if self.orderID2 is not None else ""
            )
        else:
            return "<new order>"

    def __repr__(self):
        return self.__class__.__name__ + repr(self.__dict__)

    def verify(self):
        """
        Verify by calling ``self.checker.verify()``.
        
        :returns: self
        """
        self.checker.verify()
        return self

    def ordering(self, **kwargs):
        """
        Expect this order is pending by calling ``self.checker.ordering``.

        :param orderQty: (optional) The new order quantity after the creation. 
                         ``None`` means no change.
        :type orderQty: int
        :param orderPrice: (optional) New trade price after the creation for limit 
                           orders. ``None`` means no change. N/A for market orders.
        :type orderPrice: float
        :param clOrdID: (optional) New client order id.
        :type clOrdID: str
        :param destClOrdID: (optional) Market client order id.
        :type destClOrdID: str
        :param orderID2: (optional) Market order id.
        :type orderID2: str
        :param timeInForce: (optional) Time in force of the order.
        :type timeInForce: one of ``"Norm"``, ``"IOC"``, ``"FOK"``, ``"AtOpn"``, 
                           ``"AtCls"``, ``"GTC"``, ``"GTD"``, ``"GTX"``, 
                           ``"GTHX"``, ``"AtX"`` or ``"Session"``
        :param clientID: (optional) Raptor client name
        :type clientID: str
        :param accountID: (optional) Raptor account name
        :type accountID: str
        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        """
        self.checker.ordering(self, **kwargs)
        return self

    def ordered(self, **kwargs):
        """
        Expect this order was confirmed by calling ``self.checker.ordered``.

        :param orderQty: (optional) The new order quantity after the creation. 
                         ``None`` means no change.
        :type orderQty: int
        :param orderPrice: (optional) New trade price after the creation for limit 
                           orders. ``None`` means no change. N/A for market orders.
        :type orderPrice: float
        :param clOrdID: (optional) New client order id.
        :type clOrdID: str
        :param destClOrdID: (optional) Market client order id.
        :type destClOrdID: str
        :param orderID2: (optional) Market order id.
        :type orderID2: str
        :param timeInForce: (optional) Time in force of the order.
        :type timeInForce: one of ``"Norm"``, ``"IOC"``, ``"FOK"``, ``"AtOpn"``, 
                           ``"AtCls"``, ``"GTC"``, ``"GTD"``, ``"GTX"``, 
                           ``"GTHX"``, ``"AtX"`` or ``"Session"``
        :param clientID: (optional) Raptor client name
        :type clientID: str
        :param accountID: (optional) Raptor account name
        :type accountID: str
        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        """
        self.checker.ordered(self, **kwargs)
        return self

    def reject(self, **kwargs):
        """
        Expect this order was rejected by calling ``self.checker.reject``.

        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        """
        self.checker.reject(self, **kwargs)
        return self

    def modify(self, **kwargs):
        """
        Expect an order modification for this order was sent 
        by calling ``self.checker.modify``.

        :param orderQty: (optional) The new order quantity after the modification. 
                         ``None`` means no change.
        :type orderQty: int
        :param dOrderQty: (optional) The difference to the new order quantity 
                          after the modification. ``None`` means no change.
        :type dOrderQty: int
        :param orderPrice: (optional) New trade price after the modification for limit 
                           orders. ``None`` means no change. N/A for market orders.
        :type orderPrice: float
        :param dOrderPrice: (optional) The difference to the new trade price after 
                            the modification for limit orders. ``None`` means no 
                            change. N/A for market orders.
        :type dOrderPrice: float
        :param clOrdID: (optional) New client order id.
        :type clOrdID: str
        :param destClOrdID: (optional) Market client order id.
        :type destClOrdID: str
        :param origClOrdID: (optional) Current client order id. Default is order's clOrdID.
        :type origClOrdID: str
        :param timeInForce: (optional) Time in force of the order.
        :type timeInForce: one of ``"Norm"``, ``"IOC"``, ``"FOK"``, ``"AtOpn"``, 
                           ``"AtCls"``, ``"GTC"``, ``"GTD"``, ``"GTX"``, 
                           ``"GTHX"``, ``"AtX"`` or ``"Session"``
        :param clientID: (optional) Raptor client name
        :type clientID: str
        :param accountID: (optional) Raptor account name
        :type accountID: str
        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        """
        self.checker.modify(self, **kwargs)
        return self

    def modifying(self, **kwargs):
        """
        Expect an order modification for this order is pending 
        by calling ``self.checker.modifying``.

        :param orderQty: (optional) The new order quantity after the modification. 
                         ``None`` means no change.
        :type orderQty: int
        :param orderPrice: (optional) New trade price after the modification for limit 
                           orders. ``None`` means no change. N/A for market orders.
        :type orderPrice: float
        :param clOrdID: (optional) New client order id.
        :type clOrdID: str
        :param destClOrdID: (optional) Market client order id.
        :type destClOrdID: str
        :param origClOrdID: (optional) Current client order id. Default is order's prevClOrdID.
        :type origClOrdID: str
        :param timeInForce: (optional) Time in force of the order.
        :type timeInForce: one of ``"Norm"``, ``"IOC"``, ``"FOK"``, ``"AtOpn"``, 
                           ``"AtCls"``, ``"GTC"``, ``"GTD"``, ``"GTX"``, 
                           ``"GTHX"``, ``"AtX"`` or ``"Session"``
        :param clientID: (optional) Raptor client name
        :type clientID: str
        :param accountID: (optional) Raptor account name
        :type accountID: str
        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        """
        self.checker.modifying(self, **kwargs)
        return self

    def modified(self, **kwargs):
        """
        Expect an order modification for this order was confirmed 
        by calling ``self.checker.modified``.

        :param orderQty: (optional) The new order quantity after the modification. 
                         ``None`` means no change.
        :type orderQty: int
        :param orderPrice: (optional) New trade price after the modification for limit 
                           orders. ``None`` means no change. N/A for market orders.
        :type orderPrice: float
        :param clOrdID: (optional) New client order id.
        :type clOrdID: str
        :param destClOrdID: (optional) Market client order id.
        :type destClOrdID: str
        :param origClOrdID: (optional) Current client order id. Default is order's prevClOrdID.
        :type origClOrdID: str
        :param timeInForce: (optional) Time in force of the order.
        :type timeInForce: one of ``"Norm"``, ``"IOC"``, ``"FOK"``, ``"AtOpn"``, 
                           ``"AtCls"``, ``"GTC"``, ``"GTD"``, ``"GTX"``, 
                           ``"GTHX"``, ``"AtX"`` or ``"Session"``
        :param clientID: (optional) Raptor client name
        :type clientID: str
        :param accountID: (optional) Raptor account name
        :type accountID: str
        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        """
        self.checker.modified(self, **kwargs)
        return self

    def modReject(self, **kwargs):
        """
        Expect an order modification for this order was rejected 
        by calling ``self.checker.modReject``.

        :param orderQty: (optional) The new order quantity after the modification. 
                         ``None`` means no change.
        :type orderQty: int
        :param orderPrice: (optional) New trade price after the modification for limit 
                           orders. ``None`` means no change. N/A for market orders.
        :type orderPrice: float
        :param clOrdID: (optional) New client order id.
        :type clOrdID: str
        :param destClOrdID: (optional) Market client order id.
        :type destClOrdID: str
        :param origClOrdID: (optional) Current client order id. Default is order's prevClOrdID.
        :type origClOrdID: str
        :param timeInForce: (optional) Time in force of the order.
        :type timeInForce: one of ``"Norm"``, ``"IOC"``, ``"FOK"``, ``"AtOpn"``, 
                           ``"AtCls"``, ``"GTC"``, ``"GTD"``, ``"GTX"``, 
                           ``"GTHX"``, ``"AtX"`` or ``"Session"``
        :param clientID: (optional) Raptor client name
        :type clientID: str
        :param accountID: (optional) Raptor account name
        :type accountID: str
        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        """
        self.checker.modReject(self, **kwargs)
        return self

    def cancel(self, **kwargs):
        """
        Expect an order cancellation for this order was sent 
        by calling ``self.checker.cancel``.

        :param clOrdID: (optional) New client order id. Default is order's clOrdID.
        :type clOrdID: str
        :param destClOrdID: (optional) Market client order id.
        :type destClOrdID: str
        :param clientID: (optional) Raptor client name
        :type clientID: str
        :param accountID: (optional) Raptor account name
        :type accountID: str
        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        """
        self.checker.cancel(self, **kwargs)
        return self

    def canceling(self, **kwargs):
        """
        Expect an order cancellation for this order is pending 
        by calling ``self.checker.canceling``.

        :param clOrdID: (optional) New client order id. Default is order's clOrdID.
        :type clOrdID: str
        :param destClOrdID: (optional) Market client order id.
        :type destClOrdID: str
        :param clientID: (optional) Raptor client name
        :type clientID: str
        :param accountID: (optional) Raptor account name
        :type accountID: str
        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        """
        self.checker.canceling(self, **kwargs)
        return self

    def canceled(self, **kwargs):
        """
        Expect an order cancellation for this order was confirmed 
        by calling ``self.checker.canceled``.

        :param clOrdID: (optional) New client order id. Default is order's clOrdID.
        :type clOrdID: str
        :param destClOrdID: (optional) Market client order id.
        :type destClOrdID: str
        :param clientID: (optional) Raptor client name
        :type clientID: str
        :param accountID: (optional) Raptor account name
        :type accountID: str
        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        """
        self.checker.canceled(self, **kwargs)
        return self

    def cxlReject(self, **kwargs):
        """
        Expect an order cancellation for this order was rejected 
        by calling ``self.checker.cxlReject``.

        :param clOrdID: (optional) New client order id. Default is order's clOrdID.
        :type clOrdID: str
        :param destClOrdID: (optional) Market client order id.
        :type destClOrdID: str
        :param clientID: (optional) Raptor client name
        :type clientID: str
        :param accountID: (optional) Raptor account name
        :type accountID: str
        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        """
        self.checker.cxlReject(self, **kwargs)
        return self

    def expire(self, **kwargs):
        """
        Expect an order expiration for this order was sent by the market
        by calling ``self.checker.expire``.

        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        """
        self.checker.expire(self, **kwargs)
        return self

    def dfd(self, **kwargs):
        """
        Expect a 'done for day' for this order was sent by the market
        by calling ``self.checker.dfd``.

        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        """
        self.checker.dfd(self, **kwargs)
        return self

    def fill(self, **kwargs):
        """
        Expect this order was (possibly partially) filled
        by calling ``self.checker.fill``.

        :param execQty: The quantity that was filled.
        :type execQty: int
        :param execPrice: The executed price.
        :type execPrice: float
        :param execID2: (optional) Market execution id.
        :type execID2: str
        :param transactTime: (optional) Market execution time.
        :type transactTime: time
        :param tradeDate: (optional) Market execution date.
        :type tradeDate: date
        :param clientID: (optional) Raptor client name
        :type clientID: str
        :param accountID: (optional) Raptor account name
        :type accountID: str
        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        .. seealso:: `Order.fillRepeatTicks`
        """
        self.checker.fill(self, **kwargs)
        return self

    def fillRepeatTicks(self, **kwargs):
        """
        fillRepeatTicks(self, ticks, execQty, dExecQty, execPrice, dExecPrice, clOrdIDs=None, orderID2s=None, transactTimes=None, tradeDates=None)

        Expect multiple fills for this order as generated by the simulator when 
        configured with ``--repeatPriceTicks``.

        :param ticks: The number of fills.
        :type ticks: int
        :param execQty: The quantity that was filled by the first tick.
        :type execQty: int
        :param dExecQty: (optional) The quantity difference per tick. Default 0.
        :type dExecQty: int
        :param execPrice: The executed price of the first tick for sell orders 
                            and last tick for buy orders.
        :type execPrice: float
        :param dExecPrice: (optional) The price difference per tick. Default 0.
        :type dExecPrice: float
        :param clOrdID: (optional) Client order id.
        :type clOrdID: str
        :param orderID2: (optional) Market order id.
        :type orderID2: str
        :param execID2s: (optional) Market execution ids. If given, must contain 
                         exactly `ticks` items.
        :type execID2s: list of str
        :param transactTimes: (optional) Market execution times. If given, must contain 
                              exactly `ticks` items.
        :type transactTimes: list of time
        :param tradeDates: (optional) Market execution dates. If given, must contain 
                           exactly `ticks` items.
        :type tradeDates: list of date
        :param clientID: (optional) Raptor client name
        :type clientID: str
        :param accountID: (optional) Raptor account name
        :type accountID: str
        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        .. seealso:: `Order.fill`
        """
        ticks = kwargs.pop('ticks')
        execQty = kwargs.pop('execQty')
        dExecQty = kwargs.pop('dExecQty', 0.0)
        execPrice = kwargs.pop('execPrice')
        dExecPrice = kwargs.pop('dExecPrice', 0.0)
        listkwargs = [{} for i in range(ticks)]
        for kw in self.checker._fillRepeatTicks_listKwArgs:
            if (kw + 's') in kwargs:
                assert kw not in kwargs
                vs = kwargs.pop(kw + 's')
                assert(len(vs) == ticks)
                for i in range(ticks):
                    listkwargs[i][kw] = vs[i]
        if self.side == 'B':
            execPrice -= dExecPrice * (ticks - 1)
        else:
            execPrice += dExecPrice * (ticks - 1)
            dExecPrice *= -1
        for i in range(ticks):
            self.fill(execQty=execQty + i * dExecQty,
                      execPrice=execPrice + i * dExecPrice,
                      **dict(kwargs, **listkwargs[i]))
        return self

    def bust(self, **kwargs):
        """
        Expect an order execution for this order was busted
        by calling ``self.checker.bust``.

        :param execQty: The quantity that was filled.
        :type execQty: int
        :param execPrice: The executed price.
        :type execPrice: float
        :param execID2: (optional) Market execution id.
        :type execID2: str
        :param clientID: (optional) Raptor client name
        :type clientID: str
        :param accountID: (optional) Raptor account name
        :type accountID: str
        :returns: `self`

        .. warning: Arguments must be given as keyword arguments.
        """
        self.checker.bust(self, **kwargs)
        return self

    @property
    def openQty(self):
        if getattr(self, 'orderQty', None) is None or \
           getattr(self, 'execQty', None) is None:
            return None
        elif self.orderStatus == 'closed':
            return 0
        else:
            return self.orderQty - self.execQty

    @property
    def oldOpenQty(self):
        if getattr(self, 'oldOrderQty', None) is None or \
           getattr(self, 'execQty', None) is None:
            return None
        else:
            return self.oldOrderQty - self.execQty

    @property
    def prevOpenQty(self):
        if getattr(self, 'prevOrderQty', None) is None or \
           getattr(self, 'execQty', None) is None:
            return None
        else:
            return self.prevOrderQty - self.execQty

    _prefix_re = re.compile('old|prev')

    def __getattr__(self, name):
        prefix = self._prefix_re.match(name)
        if prefix:
            first = ''.join(list(itertools.takewhile(
                lambda c: c.isupper(), name[prefix.end():])))
            realName = first.lower() + name[prefix.end() + len(first):]
            if realName not in object.__getattribute__(self, 'checker')._modifyAttributes:
                raise AttributeError("%s doesn't have modify queue attribute %r" % (
                    self.__class__.__name__, realName))
            else:
                try:
                    if prefix.group() == 'old':
                        return self.queue[0][realName]
                    else:
                        return self.queue[-2][realName]
                except KeyError:
                    raise AttributeError("%s doesn't have modify queue attribute %r set" % (
                        self.__class__.__name__, name))
        elif name in object.__getattribute__(self, 'checker')._modifyAttributes:
            try:
                return self.queue[-1][name]
            except KeyError:
                raise AttributeError("%s doesn't have modify queue attribute %r set" % (
                    self.__class__.__name__, name))
        else:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name not in ('checker', 'queue'):
            # update hash tables
            if name in self.checker.orderHashes and getattr(self, name, None) is not None:
                del self.checker.orderHashes[name][getattr(self, name)]
            if name in self.checker._modifyAttributes:
                # update modify queue
                self.queue[-1][name] = value
            else:
                object.__setattr__(self, name, value)
            # update hash tables
            if name in self.checker.orderHashes and value is not None:
                del self.checker.orderHashes[name][value]
        else:
            object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name not in ('checker', 'queue'):
            # update hash tables
            if name in self.checker.orderHashes and getattr(self, name, None) is not None:
                del self.checker.orderHashes[name][getattr(self, name)]
        if name in checker._modifyAttributes:
            del self.queue[0][name]
        else:
            object.__delattr__(self, name)

    def pushModify(self):
        self.queue.append(dict(self.queue[-1]))

    def popModify(self, restore):
        oldOld = self.queue.pop(0)
        if restore:
            for attr in set(oldOld) | set(self.queue[0]):
                if attr not in oldOld:
                    del self.queue[0][attr]
                elif attr in self.checker._modifyDeltaAttributes and \
                    oldOld[attr] is not None and \
                    attr in self.queue[0] and self.queue[0][attr] is not None:
                    # adjust numeric values through whole history
                    diff = self.queue[0][attr] - oldOld[attr]
                    for i in range(len(self.queue)):
                        self.queue[i][attr] -= diff
                else:
                    # push other values to the front of the queue
                    self.queue[0][attr] = oldOld[attr]

    def _newOrder(self, **kwargs):
        self.checker.orders.append(self)
        self.dk = kwargs.get('dk', False)
        self.orderStatus = 'new'
        self.security = kwargs.get('security', None)
        self.side = kwargs.get('side', None)
        self.orderQty = kwargs.get('orderQty', None)
        self.execQty = 0 if not self.dk else None
        self.orderPrice = kwargs.get('orderPrice', None)
        self.clOrdID = kwargs.get('clOrdID', None)
        self.destClOrdID = kwargs.get('destClOrdID', None)
        self.orderID2 = kwargs.get('orderID2', None)
        self.timeInForce = kwargs.get('timeInForce', None)
        self.clientID = kwargs.get('clientID', None)
        self.accountID = kwargs.get('accountID', None)

    def _ordering(self, **kwargs):
        if kwargs.get('orderQty', None) is not None:
            self.orderQty = kwargs['orderQty']
        if kwargs.get('orderPrice', None) is not None:
            self.orderPrice = kwargs['orderPrice']
        if kwargs.get('clOrdID', None) is not None:
            self.clOrdID = kwargs['clOrdID']
        if kwargs.get('destClOrdID', None) is not None:
            self.destClOrdID = kwargs['destClOrdID']
        if kwargs.get('orderID2', None) is not None:
            self.orderID2 = kwargs['orderID2']
        if kwargs.get('timeInForce', None) is not None:
            self.timeInForce = kwargs['timeInForce']
        if kwargs.get('clientID', None) is not None:
            self.clientID = kwargs['clientID']
        if kwargs.get('accountID', None) is not None:
            self.accountID = kwargs['accountID']

    def _ordered(self, **kwargs):
        self.orderStatus = 'open'
        if kwargs.get('orderQty', None) is not None:
            self.orderQty = kwargs['orderQty']
        if kwargs.get('orderPrice', None) is not None:
            self.orderPrice = kwargs['orderPrice']
        if kwargs.get('clOrdID', None) is not None:
            self.clOrdID = kwargs['clOrdID']
        if kwargs.get('destClOrdID', None) is not None:
            self.destClOrdID = kwargs['destClOrdID']
        if kwargs.get('orderID2', None) is not None:
            self.orderID2 = kwargs['orderID2']
        if kwargs.get('timeInForce', None) is not None:
            self.timeInForce = kwargs['timeInForce']
        if kwargs.get('clientID', None) is not None:
            self.clientID = kwargs['clientID']
        if kwargs.get('accountID', None) is not None:
            self.accountID = kwargs['accountID']

    def _reject(self, **kwargs):
        self.orderStatus = 'closed'

    def _modify(self, **kwargs):
        self.pushModify()
        if kwargs.get('orderQty', None) is not None:
            self.orderQty = max(kwargs['orderQty'], 0)
        if kwargs.get('dOrderQty', None) is not None:
            self.orderQty += max(kwargs['dOrderQty'], -(self.openQty or 0))
        if kwargs.get('orderPrice', None) is not None:
            self.orderPrice = kwargs['orderPrice']
        if kwargs.get('dOrderPrice', None) is not None:
            self.orderPrice += kwargs['dOrderPrice']
        if kwargs.get('clOrdID', None) is not None:
            self.clOrdID = kwargs['clOrdID']
        if kwargs.get('destClOrdID', None) is not None:
            self.destClOrdID = kwargs['destClOrdID']
        if kwargs.get('timeInForce', None) is not None:
            self.timeInForce = kwargs['timeInForce']
        if kwargs.get('clientID', None) is not None:
            self.clientID = kwargs['clientID']
        if kwargs.get('accountID', None) is not None:
            self.accountID = kwargs['accountID']
            
    def _modifying(self, **kwargs):
        if kwargs.get('orderQty', None) is not None:
            self.orderQty = kwargs['orderQty']
        if kwargs.get('orderPrice', None) is not None:
            self.orderPrice = kwargs['orderPrice']
        if kwargs.get('clOrdID', None) is not None:
            self.clOrdID = kwargs['clOrdID']
        if kwargs.get('destClOrdID', None) is not None:
            self.destClOrdID = kwargs['destClOrdID']
        if kwargs.get('timeInForce', None) is not None:
            self.timeInForce = kwargs['timeInForce']
        if kwargs.get('clientID', None) is not None:
            self.clientID = kwargs['clientID']
        if kwargs.get('accountID', None) is not None:
            self.accountID = kwargs['accountID']

    def _modified(self, **kwargs):
        self.popModify(False)
        if kwargs.get('orderQty', None) is not None:
            self.orderQty = kwargs['orderQty']
        if kwargs.get('orderPrice', None) is not None:
            self.orderPrice = kwargs['orderPrice']
        if kwargs.get('clOrdID', None) is not None:
            self.clOrdID = kwargs['clOrdID']
        if kwargs.get('destClOrdID', None) is not None:
            self.destClOrdID = kwargs['destClOrdID']
        if kwargs.get('timeInForce', None) is not None:
            self.timeInForce = kwargs['timeInForce']
        if kwargs.get('clientID', None) is not None:
            self.clientID = kwargs['clientID']
        if kwargs.get('accountID', None) is not None:
            self.accountID = kwargs['accountID']
        if self.openQty <= 0:
            self.orderStatus = 'closed'

    def _modReject(self, **kwargs):
        self.popModify(True)

    def _cancel(self, **kwargs):
        self.pushModify()
        if kwargs.get('clOrdID', None) is not None:
            self.clOrdID = kwargs['clOrdID']
        if kwargs.get('destClOrdID', None) is not None:
            self.destClOrdID = kwargs['destClOrdID']
        if kwargs.get('clientID', None) is not None:
            self.clientID = kwargs['clientID']
        if kwargs.get('accountID', None) is not None:
            self.accountID = kwargs['accountID']

    def _canceling(self, **kwargs):
        if kwargs.get('clOrdID', None) is not None:
            self.clOrdID = kwargs['clOrdID']
        if kwargs.get('destClOrdID', None) is not None:
            self.destClOrdID = kwargs['destClOrdID']
        if kwargs.get('clientID', None) is not None:
            self.clientID = kwargs['clientID']
        if kwargs.get('accountID', None) is not None:
            self.accountID = kwargs['accountID']

    def _canceled(self, **kwargs):
        self.popModify(False)
        if kwargs.get('clOrdID', None) is not None:
            self.clOrdID = kwargs['clOrdID']
        if kwargs.get('destClOrdID', None) is not None:
            self.destClOrdID = kwargs['destClOrdID']
        if kwargs.get('clientID', None) is not None:
            self.clientID = kwargs['clientID']
        if kwargs.get('accountID', None) is not None:
            self.accountID = kwargs['accountID']
        self.orderStatus = 'closed'

    def _cxlReject(self, **kwargs):
        self.popModify(True)

    def _expire(self, **kwargs):
        self.orderStatus = 'closed'
        if kwargs.get('clientID', None) is not None:
            self.clientID = kwargs['clientID']
        if kwargs.get('accountID', None) is not None:
            self.accountID = kwargs['accountID']

    def _dfd(self, **kwargs):
        self.orderStatus = 'closed'
        if kwargs.get('clientID', None) is not None:
            self.clientID = kwargs['clientID']
        if kwargs.get('accountID', None) is not None:
            self.accountID = kwargs['accountID']

    def _fill(self, **kwargs):
        self.execQty += kwargs['execQty']
        # modify/fill race condition
        self.orderQty = max(self.orderQty, self.execQty or 0)
        if self.openQty <= 0:
            self.orderStatus = 'closed'
        if kwargs.get('clientID', None) is not None:
            self.clientID = kwargs['clientID']
        if kwargs.get('accountID', None) is not None:
            self.accountID = kwargs['accountID']

    def _bust(self, **kwargs):
        self.execQty -= kwargs['execQty']
        if self.openQty > 0:
            self.orderStatus = 'open'
        if kwargs.get('clientID', None) is not None:
            self.clientID = kwargs['clientID']
        if kwargs.get('accountID', None) is not None:
            self.accountID = kwargs['accountID']


class GenericChecker(object):
    """
    A checker object helps verifying various things. The `GenericChecker` 
    verfies nothing. It is there to provide the basic interface. Subclasses like 
    `PositionChecker` and `DCChecker` do the actual verification.

    Usual usage:

    1. Create the checker instance of a subclass of your choice and call `reset()`
       to initialize.
    2. Execute some test.
    3. Call the corresponding method(s) to tell the checker what was supposed to
       happen.
    4. Call `verify`.

    ..note: All methods except `verify` return the checker object. So multiple
             calls can be chained together.

    ..warning: All methods and the constructor must be called with keyword
                arguments only. This ensures easy extensibilty.

                Checkers can be composed by multiple inheritance. Arguments
                are treated as a dictionary and simply passed from one class
                to the next. Constructors have to be called with named
                arguments for the same reason. 

    Example::

        sim.zcmd("cf --fill=1")
        checker = PositionChecker(...).reset()
        client.sendOrder(...)
        checker.newOrder(...).ordered(...).fill(...).verify()
    """

    def __init__(self, **kwargs):
        super(GenericChecker, self).__init__()
        self.orders = []
        self.orderHashes = {}

    def findOrderBy(self, attribute, value):
        if attributre in self.orderHashes:
            return self.orderHashes[attribute].get(value, None)
        hash = {}
        for order in self.orders:
            hash[getattr(order, attribute)] = order
        self.orderHashes[attribute] = hash
        return hash.get(value, None)

    def reset(self):
        """
        Resets the expected state of this checker by reading the actual current
        state from raptor.

        :returns: self
        """
        return self

    def verify(self):
        """
        Verifies the expected state of this checker by comparing it to the actual
        current state of raptor. After this method returns, the expected state
        is `reset` to the actual current state.

        :returns: None
        """
        self.reset()

    def callback(self, type, order, **kwargs):
        """
        Catch all method which can be overridden in order to add behavior to 
        all event methods. All event methods call this method with their method
        name prepended as first argument.
        """
        getattr(order, '_' + type)(**kwargs)

    def newOrder(self, order, **kwargs):
        """
        Expect a new order was sent. This initializes the order object. 
        Usually called from :meth:`Order.__init__`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.__init__`.

        :returns: `self`

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('newOrder', order, **kwargs)
        return self

    def ordering(self, order, **kwargs):
        """
        Expect a new order is pending. 
        Usually called from `Order.ordering`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.ordering`.

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('ordering', order, **kwargs)
        return self

    def ordered(self, order, **kwargs):
        """
        Expect a new order was confirmed. 
        Usually called from `Order.ordered`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.ordered`.

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('ordered', order, **kwargs)
        return self

    def reject(self, order, **kwargs):
        """
        Expect a new order was rejected.
        Usually called from `Order.reject`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.reject`.

        :returns: `self`

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('reject', order, **kwargs)
        return self

    # numeric attributes that are restored on every modReject
    _modifyDeltaAttributes = ('orderQty', 'orderPrice')
    # attributes that are stored on modify and always have an 'old' version
    _modifyAttributes = _modifyDeltaAttributes + ('clOrdID', 'timeInForce')

    def modify(self, order, **kwargs):
        """
        Expect an order modification was sent.
        Usually called from `Order.modify`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.modify`.

        :returns: `self`

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('modify', order, **kwargs)
        return self

    def modifying(self, order, **kwargs):
        """
        Expect an order modification is pending.
        Usually called from `Order.modifying`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.modifying`.

        :returns: `self`

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('modifying', order, **kwargs)

    def modified(self, order, **kwargs):
        """
        Expect an order modification was confirmed.
        Usually called from `Order.modified`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.modified`.

        :returns: `self`

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('modified', order, **kwargs)

    def modReject(self, order, **kwargs):
        """
        Expect an order modification was rejected.
        Usually called from `Order.modReject`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.modReject`.

        :returns: `self`

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('modReject', order, **kwargs)
        return self

    def cancel(self, order, **kwargs):
        """
        Expect an order cancellation was sent.
        Usually called from `Order.cancel`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.cancel`.

        :returns: `self`

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('cancel', order, **kwargs)
        return self

    def canceling(self, order, **kwargs):
        """
        Expect an order cancellation was confirmed.
        Usually called from `Order.canceling`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.canceling`.

        :returns: `self`

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('canceling', order, **kwargs)
        return self

    def canceled(self, order, **kwargs):
        """
        Expect an order cancellation was confirmed.
        Usually called from `Order.canceled`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.canceled`.

        :returns: `self`

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('canceled', order, **kwargs)
        return self

    def cxlReject(self, order, **kwargs):
        """
        Expect an order cancellation was rejected.
        Usually called from `Order.cxlReject`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.cxlReject`.

        :returns: `self`

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('cxlReject', order, **kwargs)
        return self

    def expire(self, order, **kwargs):
        """
        Expect an order expiration was sent by the market.
        Usually called by `Order.expire`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.expire`.

        :returns: `self`

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('expire', order, **kwargs)
        return self

    def dfd(self, order, **kwargs):
        """
        Expect an 'done for day' was sent by the market.
        Usually called by `Order.dfd`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.dfd`.

        :returns: `self`

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('dfd', order, **kwargs)
        return self

    def fill(self, order, **kwargs):
        """
        Expect an order was (possibly partially) executed.
        Usually called by `Order.fill`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.fill`.

        :returns: `self`

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        .. seealso:: `Order.fillRepeatTicks`
        """
        self.callback('fill', order, **kwargs)
        return self

    # list keyword arguments for Order.fillRepeatTicks
    _fillRepeatTicks_listKwArgs = ('execID2', 'transactTime', 'tradeDate')

    def bust(self, order, **kwargs):
        """
        Expect an order execution was busted.
        Usually called by `Order.bust`.

        :param order: the order object
        :type order: Order

        For other arguments see `Order.bust`.

        :returns: `self`

        .. warning: Arguments, except `order`, must be given as keyword arguments.
        """
        self.callback('bust', order, **kwargs)
        return self


class LoggingChecker(GenericChecker):
    """
    Prints all events. Inherit from this checker for additional logging.
    """

    def callback(self, type, order, **kwargs):
        print("%s(%s)" % (type,
               (',\n' + " " * (len(type) + 1)).join("%s=%r" % (k, v)
                         for k, v in dict(kwargs, order=order).items())))
        super(LoggingChecker, self).callback(type, order, **kwargs)


