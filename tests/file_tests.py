#!/usr/bin/env python

import sys
sys.path.append("..")
import os
import unittest
import json
import tempfile

import maroon
from mongo import MongoDB
from tee import TeeDB
from models import PersonModel


class TestTee(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = self.dir+"/log"
        maroon.Model.database = TeeDB(self.path, MongoDB(None,'test_maroon'))

    def tearDown(self):
        os.remove(self.path)
        os.removedirs(self.dir)

    def _read_log(self):
        people = (
                PersonModel(from_dict=json.loads(line))
                for line in open(self.path)
                )
        return dict((p._id,p) for p in people)

    def test_simple_save(self):
        o1 = PersonModel(_id=0, name="Remy", age=2)
        o1.save()
        people = self._read_log()
        self.failUnlessEqual(2, people[0].age)

    def test_bulk_save(self):
        #make sure that we replace objects when they are updated
        o1 = PersonModel(_id=1, name="Alfredo", age=17)
        o2 = PersonModel(_id=2, name="Colette", age=16)
        PersonModel.bulk_save([o1,o2])
        people = self._read_log()
        self.failUnlessEqual(17, people[1].age)
        self.failUnlessEqual("Colette", people[2].name)

    def test_other_method(self):
        o = PersonModel(_id=3, name="Skinner", age=50)
        o.save()
        g = PersonModel.get_id(3)
        self.failUnlessEqual(50, g.age)

if __name__ == '__main__':
    db = MongoDB(None,'test_maroon')
    db.PersonModel.remove()
    unittest.main()
