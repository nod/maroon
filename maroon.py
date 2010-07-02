'''
maroon models - simplified object-relational mapper for Python and MongoDB
by Jeremy Kelley <jeremy@33ad.org>
'''

import re
import pymongo
from collections import defaultdict

class BogusQuery(Exception): pass

conf = {
    'host': 'localhost',
    'port': 27017,
    'db_name': 'maroon',
    'database': None,
}

def connect(host=None, port=None, db_name=None):
    host = host or conf['host']
    port = port or conf['port']
    db_name = db_name or conf['db_name']
    conf['database'] = getattr(pymongo.Connection(host,port), db_name)

def _getval(v):
    '''
    decides to return a flat value or the _value member of a Field object
    '''
    try: return v._value if isinstance(v, Field) else v
    except TypeError:return v


class Q(object):

    def __init__(self, d):
        self.data = defaultdict(dict, d)

    def __and__(self, v):
        for k in v.data:
            if not hasattr(v.data[k], 'items') and k in self.data:
                raise BogusQuery(
                    "and'ing 2 terms with diff values will never be true"
                    )
            try: self.data[k].update(v.data[k])
            except: self.data.update(v.data)
        return self

    def __or__(self, v):
        self.data = {'$or':[self.data, v.data]}
        return self


class Field(object):

    def __init__(self, name):
        self._name = name
        self._value = None

    def _assign(self,v):
        self._validate(v)
        self._value = v

    def _validate(self):
        pass

    def __eq__(self, v): return Q({self._name: _getval(v)})
    def __ge__(self, v): return Q({self._name: {'$gte':_getval(v)}})
    def __gt__(self, v): return Q({self._name: {'$gt':_getval(v)}})
    def __le__(self, v): return Q({self._name: {'$lte':_getval(v)}})
    def __lt__(self, v): return Q({self._name: {'$lt':_getval(v)}})
    def __ne__(self, v): return Q({self._name: {'$ne':_getval(v)}})

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
    def __init__(self, collection):
        pass

    def __setattr__(self, n, v):
        '''
        Capture an assignment if it's to a Field type and have it go to the
        field's value member and not override the field itself.  Otherwise,
        just assign that value to the requested member.
        '''
        field = getattr(self,n,None)
        if field and isinstance(field, Field):
            if not self.__dict__.has_key(n):
                #call the field's constructor, and puts the new object in self
                self.__dict__[n] = field.__class__(n)
            self.__dict__[n]._assign(v)
        else: self.__dict__[n] = v

    def save(self):
        d = self.to_dict()
        self.collection().insert(d)
        self._id = d['_id'] # save the unique id from mongo

    def to_dict(self):
        '''
        Build a dictionary from all non-callable entities attached to our
        object.  This will return any Fields on the object, but also any object
        members added after the fact.
        '''
        d = dict(
            (k,_getval(v)) for k,v in self.__dict__.iteritems() if not callable(v)
            )
        return d

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
        return self.collection().find(q.data if q else None)

    def delete(self):
        if hasattr(self, '_id'):
            self.collection().remove({'_id':self._id})


