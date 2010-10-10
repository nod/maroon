import couchdbkit

# This code is, and will probably continue to be, broken!
class CouchDB(object):

        # let's seed the doc_type with our class name
        #if not self.__dict__.has_key('doc_type'):
        #    self.__dict__['doc_type'] = self.__class__.__name__.lower()

    @classmethod
    def get(self, key, **kwargs):
        """gets object from couchdb if couchdb instance is available"""
        self.couchdb.get(key, **kwargs)

    def save(self, callback=None):
        """gets object from couchdb if couchdb instance is available"""
        if not callback:
            callback = self._save_generic_cb
        _id = self.__dict__.get('_id')
        if _id:
            self.couchdb.set(_id, self.to_d(), callback)
        else:
            self.couchdb.set(self.to_d(), callback)

    def _save_generic_cb(self, doc):
        if doc.error:
            print "ERROR:", doc.msg

    @classmethod
    def view(self, resource, callback, **kwargs):
        """
        Return a list of documents at the specified view.  The return is always
        a list, even if only one item matches.

        - resource : should be of the form  'design/view'
        - callback : a valid callback function. async ftw!
        """
        des, res = resource.split('/')
        self.couchdb.view(des, res, callback, **kwargs)


