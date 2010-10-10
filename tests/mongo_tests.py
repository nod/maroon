#!/usr/bin/env python

import sys
sys.path.append("..")

import pymongo
import unittest

import maroon
from maroon import Model, IntProperty, Property
from mongo import MongoDB
from models import SimpleModel, FunModel


class SimpleModel(Model):
    '''
    A very simple example of a model consisting of a few simple members.  This will
    be used to test simple assignment and also dictionary exporting
    '''
    int1 = IntProperty("i1")
    int2 = IntProperty("i2")


class TestBasicModelCreationAndAssignment(unittest.TestCase):

    def setUp(self):
        self.o1 = SimpleModel()
        self.o2 = SimpleModel()
        self.o3 = SimpleModel()

    def test_simple_save(self):
        self.o1.int1 = 44
        self.o1.save()
        self.failIfEqual(self.o1._id, None)

    def test_update_object(self):
        #make sure that we replace objects when they are updated
        self.o1._id = "mustafa"
        self.o1.int1 = 1
        self.o1.int2 = 2
        self.o1.save()
        ob = SimpleModel.get_id("mustafa")
        ob.int2 = 3
        ob.save()
        ob = SimpleModel.get_id("mustafa")
        self.failUnlessEqual(3, ob.int2)

    def test_missing_fields(self):
        obj1 = SimpleModel({'_id':'simba','i1':2})
        obj1.save()
        ob = SimpleModel.get_id('simba')
        self.failUnlessEqual(ob.int2, None)

    def test_set_missing_field(self):
        SimpleModel({'i1':2,'_id':'timon'}).save()
        ob = SimpleModel.get_id('timon')
        ob.int2 = 15
        ob.save()
        ob = SimpleModel.get_id('timon')
        self.failUnlessEqual(ob.int2, 15)

    def test_remove_field(self):
        self.o2._id = "nala"
        self.o2.int1 = 2
        self.o2.int2 = 3
        self.o2.save()
        item = SimpleModel.get_id("nala")
        self.failUnlessEqual( item.int2, 3)
        item.int2 = None
        item.save()
        result = SimpleModel.get_id("nala")
        self.failUnlessEqual( result.int2, None)

if __name__ == '__main__':
    Model.database = MongoDB(None,'test_maroon')
    Model.database['SimpleModel'].remove()
    unittest.main()
