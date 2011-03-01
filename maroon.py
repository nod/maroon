'''
maroon models - simplified object-relational mapper for Python and MongoDB
by Jeremy Kelley <jeremy@33ad.org> and Jeff McGee <JeffAMcGee@gmail.com>
'''

import time
from datetime import datetime as _dt
from collections import defaultdict
from copy import copy
import re


SLUG_REGEX = re.compile('[\w@\.]+$')


class BogusQuery(Exception): pass


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
    def __init__(self, name, default=None, null=True):
        self.name = name or None
        self._default = default
        self.null = null

    def default(self):
        return self._default

    def validated(self, val):
        """Subclasses raise TypeError or ValueError if they are sent invalid
        data.  If this method is overridden, it may return a
        functionally-equivalent copy of val."""
        if val is None and not self.null:
            raise ValueError("You can't assign None to an non-null property.")
        return val

    def to_d(self, val, **kwargs):
        "Changes val into something that can go to json.dumps"
        return val

    def __eq__(self, v): return Q({self.name: v})
    def __ge__(self, v): return Q({(self.name, '$gte'):v})
    def __gt__(self, v): return Q({(self.name, '$gt' ):v})
    def __le__(self, v): return Q({(self.name, '$lte'):v})
    def __lt__(self, v): return Q({(self.name, '$lt' ):v})
    def __ne__(self, v): return Q({(self.name, '$ne' ):v})
    
    def is_in(self, terms): return Q({(self.name, '$in' ):terms})
    def is_not_in(self, terms): return Q({(self.name, '$nin' ):terms})


class EnumProperty(Property):
    def __init__(self, name, constants, **kwargs):
        Property.__init__(self, name, **kwargs)
        self.constants = constants

    def validated(self, val):
        val = Property.validated(self, val)
        if val not in self.constants:
            raise TypeError("value not in %r"%self.constants)
        return val


class TypedProperty(Property):
    def  __init__(self, name, kind, **kwargs):
        Property.__init__(self, name, **kwargs)
        self.kind = kind

    def validated(self, val):
        val = Property.validated(self, val)
        ret = self.kind(val)
        if ret != val:
            raise TypeError("value %r not %s"%(val,self.kind.__name__))
        return ret


class BoolProperty(TypedProperty):
    def  __init__(self, name, **kwargs):
        TypedProperty.__init__(self, name, bool, **kwargs)


class IntProperty(TypedProperty):
    def  __init__(self, name, **kwargs):
        TypedProperty.__init__(self, name, int, **kwargs)


class FloatProperty(TypedProperty):
    def  __init__(self, name, **kwargs):
        TypedProperty.__init__(self, name, float, **kwargs)


class DictProperty(TypedProperty):
    def  __init__(self, name, **kwargs):
        TypedProperty.__init__(self, name, dict, **kwargs)


class DateTimeProperty(Property):
    def  __init__(self, name, format=None, **kwargs):
        "Creates a DateTimeProperty. format is a strptime string for decoding"
        Property.__init__(self, name, **kwargs)
        self._format = format

    def validated(self, val):
        "Accepts datetime, string, or list of 6 ints.  Returns a datetime."
        if isinstance(val,_dt):
            return val
        if self._format and isinstance(val,basestring):
            return _dt.strptime(val,self._format)
        try:
            return _dt.fromtimestamp(float(val))
        except TypeError:
            pass # it was not a number
        if len(val) > 2:
            return _dt(*val[:6])
        raise TypeError("value %r isn't a datetime"%val)


    def to_d(self, val, **kwargs):
        format = kwargs.get('dateformat',None)
        if format=="datetime":
            return val
        elif format=="epoch":
            return time.mktime(val.timetuple())
        elif format in (None,"list"):
            return val.timetuple()[0:6]
        else:
            return val.strftime(format)


class TextProperty(Property):
    """TextProperty needs to work correctly with Unicode and String objects.
    That is the reason this is not a subclass of TypedProperty."""
    def validated(self, val):
        val = Property.validated(self, val)
        if not isinstance(val, basestring):
            raise TypeError("value not text")
        return val

    def __floordiv__(self, pattern):
        return Q({self.name: re.compile(pattern)})


class IdProperty(Property):
    pass


class RegexTextProperty(TextProperty):
    def __init__(self, name, pattern, **kwargs):
        TextProperty.__init__(self, name, **kwargs)
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
    def __init__(self, name, **kwargs):
        RegexTextProperty.__init__(self, name, SLUG_REGEX, **kwargs)


class CreatedAtProperty(DateTimeProperty):
    def default(self):
        return _dt.utcnow()


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
    def __init__(self, name, kind=None, **kwargs):
        Property.__init__(self, name, **kwargs)
        self._kind = kind

    def validated(self, val):
        val = Property.validated(self, val)
        ret = ListPropertyInstance(self)
        ret.extend((self.validated_item(v) for v in val))
        return ret

    def validated_item(self, val):
        if self._kind and not isinstance(val, self._kind):
            raise TypeError("%s in list is not a %s"%(val,self._kind.__name__))
        return val

    def has_all(self, terms): return Q({(self.name, '$all' ):terms})


class SlugListProperty(ListProperty):
    def __init__(self, name, **kwargs):
        ListProperty.__init__(self, name, basestring, **kwargs)

    def validated_item(self, val):
        if not SLUG_REGEX.match(val):
            raise ValueError(
                '"%s" does not match "%s"'%(val,SLUG_REGEX)
                )
        return val


class ModelPart(object):
    def __new__(kind, *args, **kwargs):
        #FIXME: properties cannot be added to a Model at runtime!
        if 'long_names' not in kind.__dict__:
            kind.long_names = {}
            for name in dir(kind):
                prop = getattr(kind,name)
                if isinstance(prop, Property):
                    kind.long_names[prop.name] = name
        return object.__new__(kind)

    def __init__(self, from_dict=None, **kwargs):
        if from_dict:
            self.update(from_dict)
        self.update(kwargs)

        #set defaults
        for name in self.long_names.values():
            old_val = getattr(self,name,None)
            prop = getattr(type(self),name,None)
            if old_val is None and prop is not None:
                val = prop.default()
                if val is not None:
                    self.__dict__[name] = val

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

    def to_d(self, **kwargs):
        'Build a dictionary from all the properties attached to self.'
        d = dict()
        for name in dir(self):
            val = getattr(self,name)
            prop = getattr(type(self),name,None)
            if val is not None and prop is not None and isinstance(prop, Property):
                d[prop.name]=prop.to_d(val, **kwargs)
        return d

    def update(self,d):
        """convert key names in d to long names, and then use d to update
        self.__dict__"""
        for k,v in d.iteritems():
            setattr(self,self.long_names.get(k,k),v)


class ModelProperty(TypedProperty):
    def __init__(self, name, part, **kwargs):
        TypedProperty.__init__(self, name, part, **kwargs)

    def default(self):
        return self.kind(from_dict=self._default)

    def to_d(self, val, **kwargs):
        return val.to_d(**kwargs)

    def validated(self, val):
        val = Property.validated(self, val)
        if not isinstance(val, self.kind):
            return self.kind(val)
        return val


class Model(ModelPart):
    _id = IdProperty("_id")
    _rev = IdProperty('_rev')

    def save(self):
        return self.database.save(self)

    def delete(self):
        return self.database.delete_id(self.__class__.__name__,self._id)

    @classmethod
    def bulk_save(cls, models):
        return cls.database.bulk_save_models(models, cls)

    @classmethod
    def in_db(cls,_id):
        return cls.database.in_coll(cls, _id)

    @classmethod
    def get_id(cls, _id):
        return cls.database.get_id(cls,_id)

    @classmethod
    def get_all(cls,limit=None):
        return cls.database.get_all(cls,limit)

    @classmethod
    def find(cls, q=None, **kwargs):
        "execute the query - only works with mongodb"
        if q is False or q is True:
            #make sure we didn't call one of python's comparison operators
            raise BogusQuery("The first term in a comparison must be a Property.")
        return cls.database.find(cls, q.to_mongo_dict() if q else None,**kwargs)

    @classmethod
    def paged_view(cls,view_name,**kwargs):
        "look at a view through an iterator - only works with couchdb"
        return cls.database.paged_view(view_name,cls=cls,**kwargs)


class ModelCache(dict):
    def __init__(self, Class, **kwargs):
        dict.__init__(self, **kwargs)
        self.Class = Class

    def __missing__(self, key):
        obj = self.Class.get_id(str(key))
        self[key] = obj
        return obj
