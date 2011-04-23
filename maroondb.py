
try:
    from mongo import ASCENDING, DESCENDING
except ImportError:
    ASCENDING, DESCENDING = 1,-1

class MaroonDB(object):
    def get_all(self, cls, **kwargs):
        return self.find(cls,None,**kwargs)

    def _sort_key_list(self, sort=None, sort_list=None, descending=False):
        if sort_list and sort:
            raise ValueError("Do not set sort_list and sort parameters.")
        if sort:
            return [(_field_name(sort),DESCENDING if descending else ASCENDING)]
        elif sort_list:
            return [_sort_key_item(x,descending) for x in sort_list]
        else:
            return []


def _sort_key_item(item,desc):
    if isinstance(item,(list,tuple)):
        return (_field_name(item[0]), item[1])
    else:
        return (_field_name(item), DESCENDING if desc else ASCENDING)


def _field_name(field):
    try:
        return field.name
    except AttributeError:
        return field
