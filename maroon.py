'''
maroon models - simplified object-relational mapper for Python and MongoDB
by Jeremy Kelley <jeremy@33ad.org>
'''

import re
import pymongo
from collections import defaultdict

class BogusQuery(Exception): pass

conf = {
    'database': None,
    'connection': None,
}

def connect(host='localhost', port=27017, db_name='maroon'):
    conf['connection'] = pymongo.Connection(host,port)
    conf['database'] = getattr(conf['connection'], db_name)


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

    def _validate(self):
        pass

    def __eq__(self, v): return Q({self._name: v})
    def __ge__(self, v): return Q({self._name: {'$gte':v}})
    def __gt__(self, v): return Q({self._name: {'$gt':v}})
    def __le__(self, v): return Q({self._name: {'$lte':v}})
    def __lt__(self, v): return Q({self._name: {'$lt':v}})
    def __ne__(self, v): return Q({self._name: {'$ne':v}})

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
                raise AttributeError()
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
        return self.collection().find(q.data if q else None)

    def delete(self):
        if hasattr(self, '_id'):
            self.collection().remove({'_id':self._id})


