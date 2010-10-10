#!/usr/bin/env python

import sys
sys.path.append("..")

import pymongo
import unittest

import maroon
from maroon import Model, IntProperty, Property
from mongo import MongoDB


class SimpleModel(Model):
    '''
    A very simple example of a model consisting of a few simple members.  This will
    be used to test simple assignment and also dictionary exporting
    '''
    i1 = IntProperty()
    i2 = IntProperty()


class TestBasicModelCreationAndAssignment(unittest.TestCase):

    def setUp(self):
        self.o1 = SimpleModel()
        self.o2 = SimpleModel()
        self.o3 = SimpleModel()

    def test_simple_save(self):
        self.o1.i1 = 44
        self.o1.save()
        self.failIfEqual(self.o1._id, None)

    def test_update_object(self):
        #make sure that we replace objects when they are updated
        self.o1._id = "mustafa"
        self.o1.i1 = 1
        self.o1.i2 = 2
        self.o1.save()
        ob = SimpleModel.get("mustafa")
        ob.i2 = 3
        ob.save()
        ob = SimpleModel.get("mustafa")
        self.failUnlessEqual(3, ob.i2)

    def test_missing_fields(self):
        obj1 = SimpleModel({'_id':'simba','i1':2})
        obj1.save()
        ob = SimpleModel.get('simba')
        self.failUnlessEqual(ob.i2, None)

    def test_set_missing_field(self):
        SimpleModel({'i1':2,'_id':'timon'}).save()
        ob = SimpleModel.get('timon')
        ob.i2 = 15
        ob.save()
        ob = SimpleModel.get('timon')
        self.failUnlessEqual(ob.i2, 15)

    def test_remove_field(self):
        self.o2._id = "nala"
        self.o2.i1 = 2
        self.o2.i2 = 3
        self.o2.save()
        item = SimpleModel.get("nala")
        self.failUnlessEqual( item.i2, 3)
        item.i2 = None
        item.save()
        result = SimpleModel.get("nala")
        self.failUnlessEqual( result.i2, None)

if __name__ == '__main__':
    Model.database = MongoDB('test_maroon')
    Model.database.database['SimpleModel'].remove()
    unittest.main()
