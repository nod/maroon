#!/usr/bin/env python

import sys
sys.path.append("..")

import pymongo
import unittest
import re

from maroon import Model, ListField, IntField, TextField, Field, BogusQuery


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
    t1 = TextField('t1')


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

    def test_text_unicode(self):
        kawaii = u'\u53ef\u611b\u3044!'
        self.o1.t1 = kawaii
        self.o1.i1 = 7
        self.o1.save()
        self.o2.t1 = "cute!"
        self.o2.i1 = 4
        self.o2.save()
        
        self.assertEqual(kawaii, self.o1.t1._value)
        results = ComplexModel.find( ComplexModel.t1==kawaii )
        self.assertEqual(1, results.count())
        self.assertEqual(7, results[0]['i1'])
        self.assertEqual(kawaii, results[0]['t1'])
        
        results = ComplexModel.find( ComplexModel.i1==7 )
        self.assertEqual(kawaii, results[0]['t1'])

    def test_text_sort(self):
        self.o1.t1="apocrypha"
        self.o1.save()
        self.o2.t1="bible"
        self.o2.save()
        self.o3.t1="spam"
        self.o3.save()
        t1 = ComplexModel.t1
        self.failUnless( 1 == ComplexModel.find( (t1>'bible') ).count() )
        self.failUnless( 2 == ComplexModel.find( (t1<='bible') ).count() )
        self.failUnless( 0 == ComplexModel.find( (t1<'apocrypha') ).count() )

    def test_text_regex(self):
        self.o1.t1="dovefoot"
        self.o1.save()
        self.o2.t1="Football"
        self.o2.save()
        self.o3.t1="not foolhardy"
        self.o3.save()
        t1 = ComplexModel.t1
        regex = re.compile('foo',re.I)
        self.failUnless( 3 == ComplexModel.find( (t1//regex) ).count() )
        self.failUnless( 2 == ComplexModel.find( (t1//'foo') ).count() )
        self.failUnless( 1 == ComplexModel.find( (t1//'foot$') ).count() )
        self.failUnless( 1 == ComplexModel.find( (t1//'\sfoo') ).count() )

    def test_text_evil(self):
        evil1=r"''\\x42'gig"
        evil2=r'""\\"em'
        evil3=r'//{{%ags'
        self.o1.t1=evil1
        self.o1.save()
        self.o2.t1=evil2
        self.o2.save()
        self.o3.t1=evil3
        self.o3.save()
        t1 = ComplexModel.t1
        results = ComplexModel.find( t1//'gig' )
        self.assertEqual(evil1, results[0]['t1'])
        results = ComplexModel.find( t1//'em' )
        self.assertEqual(evil2, results[0]['t1'])
        results = ComplexModel.find( t1//'em' )
        self.assertEqual(evil2, results[0]['t1'])
        self.failUnless(1 == ComplexModel.find( t1//'^//\\{{2}' ).count() )


if __name__ == '__main__':
    from random import random
    mongo_connection = pymongo.Connection('localhost', 27017)
    db_collection = getattr(  # generate a random collection name to work in
        mongo_connection.test_db,
        'test_'+hex(abs(hash(random())))
        )
    unittest.main()
    mongo_connection.test_db.drop_collection(db_collection)

