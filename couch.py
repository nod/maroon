import couchdbkit
from couchdbkit import Database, ResourceNotFound
from maroondb import MaroonDB


class CouchDB(Database,MaroonDB):
    def save(self, model):
        d = model.to_d()
        self.save_doc(d)
        model._id = d['_id'] # save the unique id from couchdb
        model._rev = d['_rev'] # save the unique id from couchdb
        return model

    def bulk_save_models(self, models):
        ds = []
        for m in models:
            d = m.to_d()
            ds.append(d)
        self.bulk_save(ds)

    def get_id(self, cls, _id, **kwargs):
        try:
            d = self.open_doc(_id, **kwargs)
            return cls(d)
        except ResourceNotFound:
            return None

    def get_all(self, cls, limit=None):
        for doc in self.paged_view('_all_docs',include_docs=True,limit=limit):
            if doc['id'][0]!='_':
                yield cls(doc['doc'])

    def paged_view(self, view_name, page_size=1000, cls=None, **params):
        orig_limit = params.get('limit',None)
        yielded = 0
        params['limit']=page_size+1
        if cls:
            params['include_docs']=True
        while True:
            if orig_limit is not None:
                params['limit']=min(orig_limit-yielded,page_size+1)
            res = list(self.view(view_name, **params))
            for r in res[0:page_size]:
                if cls:
                    yield cls(r['doc'])
                else:
                    yield r
            if len(res) != page_size+1:
                break
            yielded +=page_size
            last = res[-1]
            params['startkey']=last['key']
            params['startkey_docid']=last.get('id')
