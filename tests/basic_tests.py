#!/usr/bin/env python

import sys
sys.path.append("..")

import unittest

import maroon
from maroon import Model, IntProperty, Property

from models import SimpleModel, FunModel

class TestBasicModelCreationAndAssignment(unittest.TestCase):

    def setUp(self):
        self.o1 = SimpleModel()
        self.o2 = SimpleModel()
        self.o3 = SimpleModel()

    def test_simple_assign_bogus(self):
        # test for assigning an obvious non-integer 
        def _bogus_assign():
            self.o1.int1 = 'bogus'
        self.failUnlessRaises(ValueError, _bogus_assign)

    def test_simple_assign_obvious(self):
        # test for an obvious integer
        self.o1.int1 = 5
        self.assertEqual(self.o1.int1, 5)

        # now test for changing to an obvious integer 
        self.o1.int1 = 9
        self.assertEqual(self.o1.int1, 9)
    
    def test_simple_arith(self):
        self.o1.int1 = 6
        self.failUnlessEqual( 7, 1+self.o1.int1)
        self.failUnless( self.o1.int1 > 3)

    def test_simple_assign_to_multiple(self):
        '''
        Since we're doing some odd introspection and catching assignments,
        let's ensure that we're actually creating new objects when a value is
        assigned instead of just overwriting the _value of a previous object
        '''
        self.o1.int1 = 8
        self.o2.int1 = 3
        self.assertNotEqual(self.o1.int1, self.o2.int1)

    def test_dict_creation(self):
        self.o1.int1 = 1
        self.failUnlessEqual(self.o1.to_d(), {'i1':1})

    def test_init_from_dict(self):
        obj1 = SimpleModel({'i1':2})
        obj2 = SimpleModel(dict(i1=3,i2=7))
        self.failUnlessEqual( 2, obj1.int1 )
        self.failUnlessEqual( 3, obj2.int1 )
        self.failUnlessEqual( 7, obj2.int2 )


if __name__ == '__main__':
    unittest.main()
