#!/usr/bin/env python

import pymongo
import unittest

from maroon import Model, IntField, Field


# README
# -----------------------------------------------------------------------
# note!! this collection will get created, populated and destroyed during
# testing. DO NOT USE A REAL COLLECTION HERE
db_collection = None # some global love


class SimpleModel(Model):
    '''
    A very simple example of a model consisting of ONLY ONE member.  This will
    be used to test simple assignment and also dictionary exporting
    '''
    myint = IntField('myint')


class TestNaming(unittest.TestCase):
    pass


class TestModelCreationAndAssignment(unittest.TestCase):

    def setUp(self):
        SimpleModel._collection = db_collection # broke?
        self.o1 = SimpleModel(db_collection)
        self.o2 = SimpleModel(db_collection)

    def tearDown(self):
        del self.o1
        del self.o2

    def test_attrs(self):
        self.failUnless( isinstance(self.o1.myint, Field) )

    def test_simple_assign_bogus(self):
        # test for assigning an obvious non-integer 
        def _bogus_assign():
            self.o1.myint = 'bogus'
        self.failUnlessRaises(ValueError, _bogus_assign)

    def test_simple_assign_obvious(self):
        # test for an obvious integer
        self.o1.myint = 5
        self.assertEqual(self.o1.myint._value, 5)

        # now test for changing to an obvious integer 
        self.o1.myint = 9
        self.assertEqual(self.o1.myint._value, 9)

    def test_simple_assign_to_multiple(self):
        '''
        Since we're doing some odd introspection and catching assignments,
        let's ensure that we're actually creating new objects when a value is
        assigned instead of just overwriting the _value of a previous object
        '''
        self.o1.myint = 8
        self.o2.myint = 3
        self.assertNotEqual(self.o1.myint._value, self.o2.myint._value)

    def test_dict_creation(self):
        self.o1.myint = 1
        self.failUnlessEqual(self.o1.to_dict(), {'myint':1})

    def test_simple_save(self):
        self.o1.myint = 44
        self.failIf( self.o1.save() )
        self.o2.myint = 1
        self.o2.save()
        self.failUnless( 4 == SimpleModel.all().count() )

    def test_simple_queries(self):
        self.o1.myint = 10
        self.o1.save()
        self.o2.myint = 11
        self.o2.save()
        i = SimpleModel.myint
        self.failUnless( 1 == SimpleModel.find( i<99, i>10 ).count() )
        # print "COUNT", SimpleModel.find( i<99, i>41 ).count()
        # self.failUnless( 1 == SimpleModel.find( i>41 ).count() )


if __name__ == '__main__':
    from random import random
    mongo_connection = pymongo.Connection('localhost', 27017)
    db_collection = getattr(  # generate a random collection name to work in
        mongo_connection.test_db,
        'test_'+hex(abs(hash(random())))
        )
    unittest.main()
    mongo_connection.test_db.drop_collection(db_collection)

