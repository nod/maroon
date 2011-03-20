from maroon import *
from tee import TeeDB
from mock import MockDB

try:
    from mongo import MongoDB
except ImportError:
    pass

try:
    from couch import CouchDB
except ImportError:
    pass
