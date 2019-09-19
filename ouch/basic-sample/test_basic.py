import pytest
from test_utils import *
from ouch_utils import *

def test_newModFillCxl(mxgw, mxsim, ouch_client, checker, security, price):
    o = Order(checker, security=security, orderPrice=price, orderQty=10, side='B').\
        ordered().verify()
    
    price = price + 1
    o.modify(orderPrice=price, orderQty=11).modified().verify()
    
    o.fill(execQty=2, execPrice=price).verify()
    
    o.cancel().canceled().verify()
    

def test_newFillCxlByID(mxgw, mxsim, ouch_client, checker, security, price):
    o = Order(checker, security=security, orderPrice=price, orderQty=10, side='B')
    o.ordered().verify()
    
    o.fill(execQty=2, execPrice=price).verify()
    
    o.cancel().canceled().verify()
    
def test_newRej(mxgw, mxsim, ouch_client, checker, securities):
    security = securities.invalid('0')
    Order(checker, security=security, orderPrice=0, orderQty=0, side='B').\
        reject().verify()
    
def test_modRej(mxgw, mxsim, checker, security, price):
    Order(checker, clOrdID='X', dk=True).\
        modify(orderPrice=0, orderQty=0).modReject().verify()