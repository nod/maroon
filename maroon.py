


def _getval(v):
    return v._value if isinstance(Field, v) else v


class Field(object):

    @property
    def _name(self):
        return self.__name or self.__name__

    def __init__(self, name=None):
        self.__name = name
        self._value = None

    def _assign(self,v):
        self._validate(v)
        self._value = v

    def _validate(self):
        pass

    def __lt__(self, v): return {'$lt':_getval(v)}
    def __le__(self, v): return {'$lte':_getval(v)}
    def __gt__(self, v): return {'$gt':_getval(v)}
    def __ge__(self, v): return {'$gte':_getval(v)}
    def __eq__(self, v): return {'$eq':_getval(v)}
    def __ne__(self, v): return {'$ne':_getval(v)}


class IntField(Field):
    def _validate(self, val):
        if int(val) != val: # will raise ValueError if bogus
            raise ValueError("bogus value not int")


class Model(object):
    _collection = None
    _fields = []
    _db = None

    def __init__(self, db):
        self._db = db

    def __setattr__(self, n, v):
        '''
        Capture an assignment if it's to a Field type and have it go to the
        field's value member and not override the field itself.  Otherwise,
        just assign that value to the requested member.
        '''
        field = getattr(self,n)
        if field and isinstance(field, Field): field._assign(v)
        else: self.__dict__[n] = v

    def save(self):
        self._collection.insert(self.to_d)

    def to_dict(self):
         return dict(
            (k,v) for k,v in self.__dict__.iteritems() if isinstance(v,Field)
            )

    @classmethod
    def all(self):
        return self._collection.find()

    @classmethod
    def find(self, *args, **kwargs):
        return self._collection.find(  )



