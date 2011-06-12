#!/usr/bin/env python

import sys
sys.path.append("..")

import unittest
from datetime import datetime

import maroon
from maroon import Model, IntProperty, Property

from models import SimpleModel, FunModel, PersonModel

class TestBasicModelCreationAndAssignment(unittest.TestCase):

    def setUp(self):
        self.o1 = SimpleModel()
        self.o2 = SimpleModel()
        self.o3 = SimpleModel()

    def test_simple_assign_bogus(self):
        self.assertRaises(ValueError, setattr, self.o1, 'int1', 'bogus')

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
        obj1 = SimpleModel({'int1':2})
        obj2 = SimpleModel(dict(i1=3,i2=7))
        self.failUnlessEqual( 2, obj1.int1 )
        self.failUnlessEqual( 3, obj2.int1 )
        self.failUnlessEqual( 7, obj2.int2 )

    def test_ignored(self):
        o = SimpleModel(int1=17, i2=13, secret=42, keep=100)
        self.failUnlessEqual( 17, o.int1 )
        self.failUnlessEqual( 13, o.int2 )
        self.assertRaises(AttributeError, getattr, o, 'i2')
        self.failUnlessEqual( 100, o.keep )
        self.failUnlessEqual( 42, o.secret )
        self.failUnlessEqual( o.to_d(), {'i1':17,'i2':13,'keep':100})

    def test_fun_model(self):
        fun = FunModel()
        fun.part = PersonModel()
        self.assertRaises(TypeError, setattr, fun, 'enum', 'green')
        self.assertRaises(ValueError, setattr, fun, 'real', 'i')
        self.assertRaises(TypeError, setattr, fun, 'dic', [2,3])
        self.assertRaises(TypeError, setattr, fun, 'created', [])
        self.assertRaises(TypeError, setattr, fun, 'names', [7,8])
        self.assertRaises(TypeError, setattr, fun, 'names', 13)
        self.assertEqual(fun.enum, None)
        self.assertEqual(fun.part.age, 7)
        fun.part.age=100
        self.assertEqual(fun.part.age, 100)
        fun.part = {'n':'jeff'}
        self.assertEqual(fun.part.age, 7)
        self.assertEqual(fun.part.name, 'jeff')

    def test_date(self):
        fun = FunModel(date=datetime(2005,1,2,13))
        def do_to_d(df):
            return fun.to_d(dateformat=df)['dt']
        self.assertEqual(fun.date, datetime(2005,1,2,13))
        self.assertEqual(do_to_d('datetime'), datetime(2005,1,2,13))
        fun.date = [2005,1,2,16]
        self.assertEqual(fun.date, datetime(2005,1,2,16))
        self.assertEqual(do_to_d('list'),(2005,1,2,16,0,0))
        fun.date = 1104660000
        self.assertEqual(fun.date, datetime(2005,1,2,10))
        self.assertEqual(do_to_d('epoch'),1104660000)

    def test_long_names(self):
        self.o1.int1 = 3
        self.failUnlessEqual(self.o1.to_d(long_names=True), {'int1':3})
        self.failUnlessEqual(SimpleModel.long_names,
                {'i1':'int1','i2':'int2','_rev':'_rev','_id':'_id'})


if __name__ == '__main__':
    unittest.main()
