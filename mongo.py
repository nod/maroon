'''
maroon models - simplified object-relational mapper for Python and MongoDB
by Jeremy Kelley <jeremy@33ad.org> and Jeff McGee <JeffAMcGee@gmail.com>
'''

import pymongo
from pymongo.database import Database

class MongoDB(Database):
    def __init__(self, connection=None, name='maroon', **kwargs):
        if connection==None:
            connection = pymongo.Connection(**kwargs)
        Database.__init__(self,connection,name)

    def save(self, model):
        d = model.to_d()
        coll = self[model.__class__.__name__]
        coll.save(d)
        model._id = d['_id'] # save the unique id from mongo
        return model

    def get_id(self, cls, _id):
        coll = self[cls.__name__]
        return cls(coll.find_one(_id))

    def get_all(self, cls):
        coll = self[cls.__name__]
        for item in coll.find():
            yield cls(item)
