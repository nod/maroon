'''
maroon models - simplified object-relational mapper for Python and MongoDB
by Jeremy Kelley <jeremy@33ad.org> and Jeff McGee <JeffAMcGee@gmail.com>
'''

import pymongo

class MongoDB(object):
    def __init__(self, db_name='maroon', connection=None):
        if connection==None:
            connection = pymongo.Connection()
        self.connection = connection
        self.database = connection[db_name]

    def save(self, model):
        d = model.to_d()
        coll = self.database[model.__class__.__name__]
        coll.save(d)
        model._id = d['_id'] # save the unique id from mongo
        return model

    def get(self, cls, _id):
        coll = self.database[cls.__name__]
        return cls(coll.find_one(_id))

    def get_all(self, cls):
        coll = self.database[cls.__name__]
        for item in coll.find():
            yield cls(item)

    def delete(self, doc_type, _id):
        coll = self.database[doc_type]
        return coll.remove(_id)
