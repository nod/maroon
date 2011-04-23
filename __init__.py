from maroon import *
from tee import TeeDB
from mock import MockDB
from maroondb import MaroonDB, ASCENDING, DESCENDING

try:
    from mongo import MongoDB
except ImportError:
    pass

try:
    from couch import CouchDB
except ImportError:
    pass
