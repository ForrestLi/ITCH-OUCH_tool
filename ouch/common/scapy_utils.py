from scapy.all import *
import six
import time

origStrFixedLenField = StrFixedLenField

class StrFixedLenField(origStrFixedLenField):
    
    def i2m(self, pkt, x):
        return x.encode('us-ascii')
    
    def m2i(self, pkt, x):
        return x.decode('us-ascii')
    
    def any2i(self, pkt, x):
        if isinstance(x, six.string_types):
            return x
        elif isinstance(x, six.binary_type):
            return x.decode('us-ascii')
        else:
            raise ValueError('%r is not a str or bytes' % x)
        

class RPaddedStrFixedLenField(StrFixedLenField):
    __slots__ = ['padding', 'undefined_value']
    
    def __init__(self, name, default, length=None, length_from=None, padding=' ', 
                 undefined_value=''):
        StrFixedLenField.__init__(self, name=name, default=default, length=length, 
                                  length_from=length_from)
        if not isinstance(padding, six.binary_type):
            padding = str(padding)
        if not isinstance(undefined_value, six.binary_type):
            undefined_value = str(undefined_value)
        self.padding = padding
        self.undefined_value = undefined_value.rstrip(self.padding) if \
                undefined_value is not None else None

    def i2m(self, pkt, x):
        if x is None:
            x = self.undefined_value
        l = self.length_from(pkt)
        if len(x) < l:
            x = x + self.padding * (l - len(x))
        return StrFixedLenField.i2m(self, pkt, x)
    
    def m2i(self, pkt, s):
        v = StrFixedLenField.m2i(self, pkt, s).rstrip(self.padding)
        if v == self.undefined_value:
            return None
        else:
            return v
        
    def any2i(self, pkt, x):
        if x is None:
            return None
        else:
            return super(RPaddedStrFixedLenField, self).any2i(pkt, x)


class LPaddedStrFixedLenField(StrFixedLenField):
    __slots__ = ['padding', 'undefined_value']
    
    def __init__(self, name, default, length=None, length_from=None, padding=' ', 
                 undefined_value=''):
        StrFixedLenField.__init__(self, name=name, default=default, length=length, 
                                  length_from=length_from)
        if not isinstance(padding, six.binary_type):
            padding = str(padding)
        if not isinstance(undefined_value, six.binary_type):
            undefined_value = str(undefined_value)
        self.padding = padding
        self.undefined_value = undefined_value.lstrip(self.padding)

    def i2m(self, pkt, x):
        if x is None:
            x = self.undefined_value
        l = self.length_from(pkt)
        if len(x) < l:
            x = self.padding * (l - len(x)) + x
        return StrFixedLenField.i2m(self, pkt, x)
    
    def m2i(self, pkt, s):
        v = StrFixedLenField.m2i(self, pkt, s).lstrip(self.padding)
        if v == self.undefined_value:
            return None
        else:
            return v
    
    def any2i(self, pkt, x):
        if x is None:
            return None
        else:
            return super(LPaddedStrFixedLenField, self).any2i(pkt, x)

    
class LPaddedAsciiIntFixedLenField(LPaddedStrFixedLenField):
    
    def i2m(self, pkt, x):
        return LPaddedStrFixedLenField.i2m(self, pkt, str(x) if x is not None else None)
    
    def m2i(self, pkt, s):
        v = LPaddedStrFixedLenField.m2i(self, pkt, s)
        return int(v) if v is not None else None
    
    def any2i(self, pkt, x):
        if x is None:
            return None
        elif isinstance(x, six.integer_types):
            return int(x)
        else:
            x = super(LPaddedAsciiIntFixedLenField, self).any2i(pkt, x)
            return int(x)