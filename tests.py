import pymongo
import unittest

from maroon import Model, IntField, Field


class SampleModel(Model):
    myint = IntField()


class TestNaming(unittest.TestCase):
    pass


class TestModelCreationAndAssignment(unittest.TestCase):

    def setUp(self):
        self.obj = SampleModel(None)

    def tearDown(self):
        del self.obj

    def test_attrs(self):
        self.failUnless( isinstance(self.obj.myint, Field) )

    def test_int_assign_bogus(self):
        # test for assigning an obvious non-integer 
        def _bogus_assign():
            self.obj.myint = 'bogus'
        self.failUnlessRaises(ValueError, _bogus_assign)

    def test_int_assign_obvious(self):
        # test for an obvious integer
        self.obj.myint = 5
        self.assertEqual(self.obj.myint._value, 5)

        # now test for changing to an obvious integer 
        self.obj.myint = 9
        self.assertEqual(self.obj.myint._value, 9)


if __name__ == '__main__':
    mongo_connection = pymongo.Connection('localhost', 27017)
    db_ = mongo_connection.db.testing

    unittest.main()

