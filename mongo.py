'''
maroon models - simplified object-relational mapper for Python and MongoDB
by Jeremy Kelley <jeremy@33ad.org> and Jeff McGee <JeffAMcGee@gmail.com>
'''

import pymongo
from maroondb import MaroonDB


class MongoDB(pymongo.database.Database,MaroonDB):
    def __init__(self, connection=None, name='maroon', **kwargs):
        if connection==None:
            connection = pymongo.Connection(**kwargs)
        pymongo.database.Database.__init__(self,connection,name)

    def _coll(self, model):
        return self[model.__class__.__name__]

    def bulk_save_models(self, models, cls=None):
        if models:
            if cls == None:
                cls=models[0].__class__
            self[cls.__name__].insert(m.to_d(dateformat="datetime") for m in models)

    def save(self, model):
        d = model.to_d(dateformat="datetime")
        self._coll(model).save(d)
        model._id = d['_id'] # save the unique id from mongo
        return model

    def merge(self, model):
        d = model.to_d(dateformat="datetime")
        del d['_id']
        self._coll(model).find_and_modify(
            {'_id':model._id},
            {'$set':d},
            upsert=True,
            )

    def get_id(self, cls, _id, **kwargs):
        d = self[cls.__name__].find_one(_id, **kwargs)
        return cls(d) if d else None

    def get_all(self, cls, **kwargs):
        return self.find(cls,None,**kwargs)

    def find(self, cls, q, limit=None, where=None, **kwargs):
        coll = self[cls.__name__]
        try:
            q = q.to_mongo_dict()
        except AttributeError:
            pass
        sort_args = self._sort_key_list(**kwargs)
        kwargs.pop('sort',None)
        cursor = coll.find(q, **kwargs)
        if sort_args:
           cursor.sort(sort_args)
        if where != None:
            cursor.where(where)
        if limit != None:
            cursor.limit(limit)
        return (cls(d) for d in cursor)

    def in_coll(self, cls, _id):
        return bool(self[cls.__name__].find(dict(_id=_id)).count())
