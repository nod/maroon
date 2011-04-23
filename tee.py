'''
maroon models - simplified object-relational mapper for Python and MongoDB
by Jeremy Kelley <jeremy@33ad.org> and Jeff McGee <JeffAMcGee@gmail.com>
'''

try:
    import simplejson as json
except:
    import json

import itertools


#We do not extend MaroonDB because we want to call the methods in self._db
class TeeDB(object):
    def __init__(self, path, db):
        self._db = db
        self._f = open(path,'a')

    def _log(self,model):
        print>>self._f,json.dumps(model.to_d())

    def bulk_save_models(self, models, *args):
        for model in models:
            self._log(model)
        self._f.flush()
        return self._db.bulk_save_models(models, *args)

    def save(self, model):
        self._log(model)
        self._f.flush()
        return self._db.save(model)

    def __getattr__(self,name):
        return getattr(self._db,name)
