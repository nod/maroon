'''
maroon models - simplified object-relational mapper for Python and MongoDB
by Jeremy Kelley <jeremy@33ad.org> and Jeff McGee <JeffAMcGee@gmail.com>
'''

import datetime
import re


SLUG_REGEX = re.compile('[\w@\.]+$')


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


class IdProperty(Property):
    pass


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
    _id = IdProperty()

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

        #For couch: let's seed the doc_type with our class name
        #if not self.__dict__.has_key('doc_type'):
        #    self.__dict__['doc_type'] = self.__class__.__name__.lower()


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
        return self.database.save(self)

    def delete(self):
        return self.database.delete_id(self.__class__.__name__,self._id)

    @classmethod
    def get_id(cls, _id):
        return cls.database.get_id(cls,_id)

    @classmethod
    def get_all(cls,):
        return cls.database.get_all(cls)
