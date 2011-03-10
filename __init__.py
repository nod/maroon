from maroon import *
from tee import TeeDB

try:
    from mongo import MongoDB
except ImportError:
    pass

try:
    from couch import CouchDB
except ImportError:
    pass
