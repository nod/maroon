#!/usr/bin/env python

import sys
sys.path.append("..")

import pymongo
import unittest

import maroon
from maroon import Model, IntField, Field, BogusQuery


class SimpleModel(Model):
    '''
    A very simple example of a model consisting of a few simple members.  This will
    be used to test simple assignment and also dictionary exporting
    '''
    i1 = IntField('i1')
    i2 = IntField('i2')


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
        self.failUnless( 7 == 1+self.o1.i1)
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
        self.failUnlessEqual(self.o1.to_dict(), {'i1':1})

    def test_init_from_dict(self):
        self.o2.i1 = 3
        self.o2.i2 = 7
        self.o2.save()
        self.o3.i1 = 8
        self.o3.save()
        i1 = SimpleModel.i1
        obj1 = SimpleModel({'i1':2})
        obj2 = SimpleModel(SimpleModel.find( (i1==3) )[0])
        obj3 = SimpleModel(SimpleModel.find( (i1==8) )[0])
        self.failUnless( 2 == obj1.i1 )
        self.failUnless( 3 == obj2.i1 )
        self.failUnless( 7 == obj2.i2 )
        self.failUnless( 8 == obj3.i1 )

    def test_simple_save(self):
        self.o1.i1 = 44
        self.failIf( self.o1.save() )
        self.o2.i1 = 1
        self.o2.save()
        self.failUnless( 2 == SimpleModel.all().count() )

    def test_simple_queries(self):
        self.o1.i1 = 10
        self.o1.save()
        self.o2.i1 = 11
        self.o2.save()
        i1 = SimpleModel.i1
        self.failUnless( 2 == SimpleModel.find( (i1>=8) ).count() )
        self.failUnless( 1 == SimpleModel.find( (i1==10) ).count() )

    def test_advanced_queries(self):
        self.o1.i1 = 10;  self.o1.save()
        self.o2.i1 = 11;  self.o2.save()
        self.o3.i1 = 100;
        self.o3.i2 = 29; self.o3.save()
        i1 = SimpleModel.i1
        i2 = SimpleModel.i2
        self.failUnless( 1 == SimpleModel.find( (i1>10) & (i1<100) ).count() )
        self.failUnless( 2 == SimpleModel.find( (i1==10) | (i1>=100) ).count() )
        self.failUnless( 0 == SimpleModel.find( (i1==10) & (i2==29) ).count() )
        self.failUnless( 1 == SimpleModel.find( (i1==100) & (i2==29) ).count() )
        self.failUnless( 1 == SimpleModel.find( (i1!=44) & (i2==29) ).count() )
        self.failUnless( 1 == SimpleModel.find( (i2==29) & (i1!=44) ).count() )
        self.failUnless( 1 == SimpleModel.find( (i2<=30) & (i1!=44) ).count() )
        self.failUnless( 0 == SimpleModel.find( (i2<=30) & (i1==44) ).count() )
        self.failUnlessRaises(
            BogusQuery,
            lambda: 0 == SimpleModel.find( (i1==10) & (i1==100) ).count() 
            )

if __name__ == '__main__':
    from random import random
    maroon.connect(db_name='test_maroon')
    unittest.main()
