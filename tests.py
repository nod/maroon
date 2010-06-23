#!/usr/bin/env python

import pymongo
import unittest

from maroon import Model, IntField, Field


db_ = None # some global love

class SampleModel(Model):
    myint = IntField()


class TestNaming(unittest.TestCase):
    pass


class TestModelCreationAndAssignment(unittest.TestCase):

    def setUp(self):
        self.o1 = SampleModel(db_)
        self.o2 = SampleModel(db_)

    def tearDown(self):
        del self.o1
        del self.o2

    def test_attrs(self):
        self.failUnless( isinstance(self.o1.myint, Field) )

    def test_int_assign_bogus(self):
        # test for assigning an obvious non-integer 
        def _bogus_assign():
            self.o1.myint = 'bogus'
        self.failUnlessRaises(ValueError, _bogus_assign)

    def test_int_assign_obvious(self):
        # test for an obvious integer
        self.o1.myint = 5
        self.assertEqual(self.o1.myint._value, 5)

        # now test for changing to an obvious integer 
        self.o1.myint = 9
        self.assertEqual(self.o1.myint._value, 9)

    def test_int_assign_to_multiple(self):
        self.o1.myint = 8
        self.o2.myint = 3
        self.assertNotEqual(self.o1.myint._value, self.o2.myint._value)


if __name__ == '__main__':
    mongo_connection = pymongo.Connection('localhost', 27017)
    db_ = mongo_connection.db.testing

    unittest.main()

