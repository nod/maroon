import couchdbkit
from couchdbkit import Database


class CouchDB(Database):
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
        return self.bulk_save(ds)

    def get_id(self, cls, _id):
        d = self.open_doc(_id)
        return cls(d)

    def get_all(self, cls):
        for doc in self.paged_view('_all_docs',include_docs=True):
            if doc['id'][0]!='_':
                yield cls(doc['doc'])

    def paged_view(self, view_name, page_size=1000, **params):
        #FIXME: you can't set a limit with a paged view!
        params['limit']=page_size+1
        while True:
            res = list(self.view(view_name, **params))
            for r in res[0:page_size]:
                yield r
            if len(res) != page_size+1:
                break
            last = res[-1]
            params['startkey']=last['key']
            params['startkey_docid']=last.get('id') # sometimes there is no id
