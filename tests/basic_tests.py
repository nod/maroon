#!/usr/bin/env python

import sys
sys.path.append("..")

import pymongo
import unittest

import maroon
from maroon import Model, IntProperty, Property


class SimpleModel(Model):
    '''
    A very simple example of a model consisting of a few simple members.  This will
    be used to test simple assignment and also dictionary exporting
    '''
    i1 = IntProperty()
    i2 = IntProperty()


class TestBasicModelCreationAndAssignment(unittest.TestCase):

    def setUp(self):
        SimpleModel.collection().remove()
        self.o1 = SimpleModel()
        self.o2 = SimpleModel()
        self.o3 = SimpleModel()

    def tearDown(self):
        self.o1.delete()
        self.o2.delete()
        self.o3.delete()

    def test_delete(self):
        self.o1.i1 = 2
        self.o1.save()

    def test_simple_assign_bogus(self):
        # test for assigning an obvious non-integer 
        def _bogus_assign():
            self.o1.i1 = 'bogus'
        self.failUnlessRaises(ValueError, _bogus_assign)

    def test_simple_assign_obvious(self):
        # test for an obvious integer
        self.o1.i1 = 5
        self.assertEqual(self.o1.i1, 5)

        # now test for changing to an obvious integer 
        self.o1.i1 = 9
        self.assertEqual(self.o1.i1, 9)
    
    def test_simple_arith(self):
        self.o1.i1 = 6
        self.failUnlessEqual( 7, 1+self.o1.i1)
        self.failUnless( self.o1.i1 > 3)

    def test_simple_assign_to_multiple(self):
        '''
        Since we're doing some odd introspection and catching assignments,
        let's ensure that we're actually creating new objects when a value is
        assigned instead of just overwriting the _value of a previous object
        '''
        self.o1.i1 = 8
        self.o2.i1 = 3
        self.assertNotEqual(self.o1.i1, self.o2.i1)

    def test_dict_creation(self):
        self.o1.i1 = 1
        self.failUnlessEqual(self.o1.to_d(), {'i1':1})

    def test_init_from_dict(self):
        obj1 = SimpleModel({'i1':2})
        obj2 = SimpleModel(dict(i1=3,i2=7))
        self.failUnlessEqual( 2, obj1.i1 )
        self.failUnlessEqual( 3, obj2.i1 )
        self.failUnlessEqual( 7, obj2.i2 )


if __name__ == '__main__':
    from random import random
    maroon.connect(db_name='test_maroon')
    unittest.main()
