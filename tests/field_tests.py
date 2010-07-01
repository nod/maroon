#!/usr/bin/env python

import sys
sys.path.append("..")

import pymongo
import unittest

from maroon import Model, ListField, IntField, Field, BogusQuery


# README
# -----------------------------------------------------------------------
# note!! this collection will get created, populated and destroyed during
# testing. DO NOT USE A REAL COLLECTION HERE
db_collection = None # some global love


class ComplexModel(Model):
    '''
    a bit more complex model to test the other field types
    '''
    i1 = IntField('i1')
    bag = ListField('bag')


class TestComplexModelCreationAndAssignment(unittest.TestCase):

    def setUp(self):
        ComplexModel._collection = db_collection # broke?
        self.o1 = ComplexModel(db_collection)
        self.o2 = ComplexModel(db_collection)
        self.o3 = ComplexModel(db_collection)

    def tearDown(self):
        self.o1.delete()
        self.o2.delete()
        self.o3.delete()

    def test_attrs(self):
        self.failUnless( isinstance(self.o1.i1, Field) )
        self.failUnless( isinstance(self.o1.i1, IntField) )
        self.failUnless( isinstance(self.o1.bag, ListField) )

    def test_simple_queries(self):
        self.o1.i1 = 10
        self.o1.bag = [1,2,3]
        self.o1.save()
        self.o2.i1 = 11
        self.o2.save()
        i1 = ComplexModel.i1
        self.failUnless( 2 == ComplexModel.find( (i1>=8) ).count() )
        self.failUnless( 1 == ComplexModel.find( (i1==10) ).count() )

if __name__ == '__main__':
    from random import random
    mongo_connection = pymongo.Connection('localhost', 27017)
    db_collection = getattr(  # generate a random collection name to work in
        mongo_connection.test_db,
        'test_'+hex(abs(hash(random())))
        )
    unittest.main()
    mongo_connection.test_db.drop_collection(db_collection)

