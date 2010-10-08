'''
maroon models - simplified object-relational mapper for Python and MongoDB
by Jeremy Kelley <jeremy@33ad.org> and Jeff McGee <JeffAMcGee@gmail.com>
'''

import datetime
import re
import pymongo
from collections import defaultdict
from copy import copy

SLUG_REGEX = re.compile('[\w@\.]+$')

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
    def __init__(self, default=None, to_d=None, null=True):
        self._default=default
        self._to_d = to_d
        self.null = null

    def default(self):
        return self._default

    def validated(self, val):
        """Subclasses raise ValueError if they are sent invalid data.  If this
        method is overridden, it may return a functionally-equivalent copy of
        val."""
        if val is None and not self.null:
            raise ValueError("You can't assign None to an non-null property.")
        return val

    def to_d(self, val):
        "Changes val into something that can go to json.dumps"
        if self._to_d:
            #_to_d will only get one parameter, val
            return self._to_d(val)
        return val


    def __eq__(self, v): return Q({self._name: v})
    def __ge__(self, v): return Q({(self._name, '$gte'):v})
    def __gt__(self, v): return Q({(self._name, '$gt' ):v})
    def __le__(self, v): return Q({(self._name, '$lte'):v})
    def __lt__(self, v): return Q({(self._name, '$lt' ):v})
    def __ne__(self, v): return Q({(self._name, '$ne' ):v})
    
    def is_in(self, terms): return Q({(self._name, '$in' ):terms})
    def is_not_in(self, terms): return Q({(self._name, '$nin' ):terms})

class EnumProperty(Property):
    def __init__(self, constants, **kwargs):
        Property.__init__(self, constants, **kwargs)
        self.constants = constants

    def validated(self, val):
        val = Property.validated(self, val)
        if val not in self.constants:
            raise ValueError("value not in %r"%self.constants)
        return val


class TypedProperty(Property):
    def  __init__(self, kind, **kwargs):
        Property.__init__(self, **kwargs)
        self.kind = kind

    def validated(self, val):
        val = Property.validated(self, val)
        ret = self.kind(val)
        if ret != val:
            raise ValueError("value %r not %s"%(val,self.kind.__name__))
        return ret


class BoolProperty(TypedProperty):
    def  __init__(self, **kwargs):
        TypedProperty.__init__(self,bool, **kwargs)


class IntProperty(TypedProperty):
    def  __init__(self, **kwargs):
        TypedProperty.__init__(self,int, **kwargs)


class FloatProperty(TypedProperty):
    def  __init__(self, **kwargs):
        TypedProperty.__init__(self,float, **kwargs)


class DateTimeProperty(TypedProperty):
    def  __init__(self, **kwargs):
        "Creates a DateTimeProperty.  The to_d kwarg is ignored."
        TypedProperty.__init__(self,datetime.datetime, **kwargs)

    def validated(self, val):
        "Accepts either a datetime or list of 6 ints.  Returns a datetime."
        if len(val) > 2:
            return datetime.datetime(*val[:6])
        return TypedProperty.validated(self, val)

    def to_d(self, val):
        return val.timetuple()[0:6]


class TextProperty(Property):
    """TextProperty needs to work correctly with Unicode and String objects.
    That is the reason this is not a subclass of TypedProperty."""
    def validated(self, val):
        val = Property.validated(self, val)
        if not isinstance(val, basestring):
            raise ValueError("value not text")
        return val


class RegexTextProperty(TextProperty):
    def __init__(self, pattern, **kwargs):
        TextProperty.__init__(self, **kwargs)
        self._pattern = re.compile(pattern)

    def validated(self, value):
        """
        Verifies that the string matches the pattern.  Note that it uses
        python's match() and not search().  If the first character of value
        does not match, the pattern does not match.
        """
        value = super(TextProperty, self).validated(value)
        if value is None and not self.null:
            raise ValueError("this property can't be empty")
        if value and not self._pattern.match(value):
            raise ValueError(
                '"%s" does not match "%s"'%(value,self._pattern.pattern)
                )
        return value


class SlugProperty(RegexTextProperty):
    def __init__(self, **kwargs):
        RegexTextProperty.__init__(self, SLUG_REGEX, **kwargs)


class CreatedAtProperty(DateTimeProperty):
    def default(self):
        return datetime.datetime.now()


class ListPropertyInstance(list):
    def __init__(self, property):
        self.property = property

    def __setslice__(self,i,j,seq):
        self.__setitem__(slice(i,j),seq)

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            for obj in value:
                self.property.validated_item(obj)
        else:
            self.property.validated_item(value)
        list.__setitem__(self, key, value)


class ListProperty(Property):
    def __init__(self, kind=None, **kwargs):
        Property.__init__(self, **kwargs)
        #FIXME: Do we want this check in production?
        if kind is str:
            raise ValueError("ListProperty should look for basestring, not str.")
        self._kind = kind

    def validated(self, val):
        val = Property.validated(self, val)
        ret = ListPropertyInstance(self)
        ret.extend((self.validated_item(v) for v in val))
        return ret

    def validated_item(self, val):
        if self._kind and not isinstance(val, self._kind):
            raise ValueError("")
        return val

    def has_all(self, terms): return Q({(self._name, '$all' ):terms})


class SlugListProperty(ListProperty):
    def __init__(self, **kwargs):
        ListProperty.__init__(self, basestring, **kwargs)

    def validated_item(self, val):
        if not SLUG_REGEX.match(val):
            raise ValueError(
                '"%s" does not match "%s"'%(val,SLUG_REGEX)
                )
        return val


class Model(object):
    def __init__(self, from_dict=None, **kwargs):
        if from_dict:
            self.update(from_dict)
        self.update(kwargs)

        #set default values for anything the updates missed
        for name in dir(self):
            if name not in self.__dict__:
                prop = getattr(type(self),name)
                if isinstance(prop, Property):
                    val = prop.default()
                    if val is not None:
                        self.__dict__[name] = val

        # let's seed the doc_type with our class name
        if not self.__dict__.has_key('doc_type'):
            self.__dict__['doc_type'] = self.__class__.__name__.lower()


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
                v = field.validated(v)
        self.__dict__[n] = v

    def to_d(self):
        '''
        Build a dictionary from all non-callable entities attached to our
        object.  This will return any Propertys on the object, but also any
        object members added after the fact.
        '''
        d = dict()
        for (k,v) in self.__dict__.iteritems():
            if not callable(v):
                prop = getattr(type(self),k,None)
                if prop and isinstance(prop, Property):
                    d[k]=prop.to_d(v)
                else:
                    d[k]=v
        return d

    def update(self,d):
        "using __dict__.update instead of this will bypass __setattr__"
        for k,v in d.iteritems():
            setattr(self,k,v)

    def save(self):
        d = self.to_dict()
        self.collection().save(d)
        self._id = d['_id'] # save the unique id from mongo
        return self

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
