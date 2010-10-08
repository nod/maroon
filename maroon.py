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


class Q(dict):
    def __init__(self, d=None):
        dict.__init__(self,d)

    def __and__(self, v):
        for key in set(self)&set(v):
            if key != '$or':
                raise BogusQuery( "field %s can't match %s and %s"%(
                        key, str(self[key]), str(v[key])
                    ))
        q = Q(self) #we do not want to modify self or v
        q.update(v)
        if self.has_key('$or') and v.has_key('$or'):
            #combine the things in $or using the distributive property
            #(a|b)&(c|d) -> (a&c | a&d | b&c | b&d)  
            q['$or'] = [
                self_term & v_term
                for self_term in self['$or']
                for v_term in v['$or']
            ]
        return q

    def __or__(self, v):
        fixed_self = self._to_distributed_list()
        fixed_v = v._to_distributed_list()
        return Q({'$or':fixed_self+fixed_v})
    
    def _to_distributed_list(self):
        #returns a list of Q objects that is equivalent to self if the terms
        #of the list are ORed together
        if not self.has_key('$or'):
            return [self]
        if len(self) ==1:
            return self['$or']
        outer = copy(self)
        del outer['$or']
        #mongo does not let you nest or statements - use boolean algebra to
        #return a "sum of products"
        return [ (outer & inner) for inner in self['$or']]

    def to_mongo_dict(self):
        d = defaultdict(dict)
        for key,val in self.iteritems():
            #crawl the tree
            if isinstance(val, Q):
                mongo_value = val.to_mongo_dict()
            elif hasattr(val, '__iter__') and not isinstance(val, basestring):
                mongo_value = [
                        item.to_mongo_dict() if isinstance(item,Q) else item
                        for item in val
                ]
            else:
                mongo_value = val

            #expand the tuples
            if isinstance(key, tuple):
                if key[0] in self:
                    raise BogusQuery( "field %s can't be %s and match %s"%(
                            key[0], str(self[key[0]]), str(val)
                        ))
                #convert self[('size','$gte')] to d['size']['$gte'] 
                d[key[0]][key[1]] = mongo_value
            else:
                d[key] = mongo_value
        return d


class Property(object):

    def __init__(self, name):
        self._name = name

    @classmethod
    def validate(self):
        pass

    def __eq__(self, v): return Q({self._name: v})
    def __ge__(self, v): return Q({(self._name, '$gte'):v})
    def __gt__(self, v): return Q({(self._name, '$gt' ):v})
    def __le__(self, v): return Q({(self._name, '$lte'):v})
    def __lt__(self, v): return Q({(self._name, '$lt' ):v})
    def __ne__(self, v): return Q({(self._name, '$ne' ):v})
    
    def is_in(self, terms): return Q({(self._name, '$in' ):terms})
    def is_not_in(self, terms): return Q({(self._name, '$nin' ):terms})

# ADD def for $all to peek in doc members with arrays  TODO

class IntProperty(Property):
    @classmethod
    def validate(self, val):
        if int(val) != val: # will raise ValueError if bogus
            raise ValueError("value not int")


class ListProperty(Property):
    @classmethod
    def validate(self, val):
        if not hasattr(val, '__iter__'): # will raise ValueError if bogus
            raise ValueError("value not list")
    
    def has_all(self, terms): return Q({(self._name, '$all' ):terms})


class TextProperty(Property):
    @classmethod
    def validate(self, val):
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
        '''Hide Propertys in instances of Models.'''
        #here be dragons - if you say self.anything, infinite recursion happens
        value = object.__getattribute__(self,name)
        #if name is not an instance variable, then we check if it is a Property
        if isinstance(value, Property):
            self_dict = object.__getattribute__(self,'__dict__')
            if not self_dict.has_key(name):
                return None
        return value

    def __setattr__(self, n, v):
        field = getattr(type(self),n,None)
        if field and isinstance(field, Property):
            if v is not None:
                field.validate(v)
        self.__dict__[n] = v

    def save(self):
        d = self.to_dict()
        self.collection().save(d)
        self._id = d['_id'] # save the unique id from mongo
        return self

    def to_dict(self):
        '''
        Build a dictionary from all non-callable entities attached to our
        object.  This will return any Propertys on the object, but also any object
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
        #print q
        if q is False or q is True:
            #make sure we didn't call one of python's comparison operators
            raise BogusQuery("The first term in a comparison must be a Property.")
        return self.collection().find(q.to_mongo_dict() if q else None)

    def delete(self):
        if hasattr(self, '_id'):
            self.collection().remove({'_id':self._id})


