'''
maroon models - simplified object-relational mapper for Python and MongoDB
by Jeremy Kelley <jeremy@33ad.org>
'''

import re
import pymongo
from collections import defaultdict
from copy import copy

class BogusQuery(Exception): pass

conf = {
    'database': None,
    'connection': None,
}

def connect(host='localhost', port=27017, db_name='maroon'):
    conf['connection'] = pymongo.Connection(host,port)
    conf['database'] = getattr(conf['connection'], db_name)


class Q(defaultdict):
    def __init__(self, d=None):
        defaultdict.__init__(Q, d)

    def __and__(self, v):
        #This method works hard to not modify the old self object.  Bad things
        # will happen if you modify self['size']['$gte']
        q = Q(self)
        for key in set(self)|set(v):
            q[key] = 
            if key in self:
            if not hasattr(v[k], 'items') and k in self:
                raise BogusQuery(
                    "and'ing 2 terms with diff values will never be true"
                    )
            try: self[k].update(v[k])
            except: self.update(v)
        return q

    def __or__(self, v):
        fixed_self = _to_distributed_list(self)
        fixed_v = _to_distributed_list(v)
        return Q({'$or':fixed_self+fixed_v})
    
    def _just_or(self):
        return len(self)==1 and self.has_key('$or')

    #mongo does not let you nest or statements - use boolean algebra to return a
    #"sum of products"
    def _to_distributed_list(self):
        if not self.has_key('$or'):
            return [self]
        if len(self) ==1:
            return self['$or']
        outer = copy(self)
        del outer['$or']
        return [ (outer & inner) for inner in self['$or']]}


class Field(object):

    def __init__(self, name):
        self._name = name

    def _validate(self):
        pass

    def __eq__(self, v): return Q({(self._name, '$eq' ):v})
    def __ge__(self, v): return Q({(self._name, '$gte'):v})
    def __gt__(self, v): return Q({(self._name, '$gt' ):v})
    def __le__(self, v): return Q({(self._name, '$lte'):v})
    def __lt__(self, v): return Q({(self._name, '$lt' ):v})
    def __ne__(self, v): return Q({(self._name, '$ne' ):v})

# ADD def for $all to peek in doc members with arrays  TODO

class IntField(Field):
    def _validate(self, val):
        if int(val) != val: # will raise ValueError if bogus
            raise ValueError("value not int")


class ListField(Field):
    def _validate(self, val):
        if not hasattr(val, '__iter__'): # will raise ValueError if bogus
            raise ValueError("value not list")


class TextField(Field):
    def _validate(self, val):
        if unicode(val) != val: # will raise ValueError if bogus
            raise ValueError("value not text")

    def __floordiv__(self, pattern):
        return Q({self._name: re.compile(pattern)})


class Model(object):
    def __init__(self, from_dict=None, **kwargs):
        if from_dict:
            self.from_dict(from_dict)
        self.from_dict(kwargs)

    def __getattribute__(self, name):
        self_dict = object.__getattribute__(self,'__dict__')
        if not self_dict.has_key(name):
            field = getattr(type(self), name, None)
            if field and isinstance(field, Field):
                return None
        return object.__getattribute__(self,name)

    def __setattr__(self, n, v):
        field = getattr(type(self),n,None)
        if field and isinstance(field, Field):
            field._validate(v)
        self.__dict__[n] = v

    def save(self):
        d = self.to_dict()
        self.collection().insert(d)
        self._id = d['_id'] # save the unique id from mongo
        return self

    def to_dict(self):
        '''
        Build a dictionary from all non-callable entities attached to our
        object.  This will return any Fields on the object, but also any object
        members added after the fact.
        '''
        d = dict( (k,v) for k,v in self.__dict__.iteritems() if not callable(v) )
        return d

    def from_dict(self,d):
        for (k,v) in d.iteritems():
            setattr(self,k,v)

    @classmethod
    def collection(self):
        if not conf.get('database'):
            connect()
        return getattr(conf['database'],self.__name__)

    @classmethod
    def all(self):
        return self.collection().find()

    @classmethod
    def find(self, q=None):
        from pprint import pprint
        pprint(q.data)
        return self.collection().find(q.data if q else None)

    def delete(self):
        if hasattr(self, '_id'):
            self.collection().remove({'_id':self._id})


