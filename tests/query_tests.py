#!/usr/bin/env python

import sys
sys.path.append("..")

import pymongo
import unittest

import maroon
from maroon import Model, TextField, IntField, BogusQuery


class NumberModel(Model):
    '''
    A very simple example of a model consisting of a few simple members.  This will
    be used to test simple assignment and also dictionary exporting
    '''
    n = IntField('n')
    quad = IntField('quad')
    name = TextField('name')

def _query_to_list(q):
    return sorted( [json['n'] for json in NumberModel.find(q)] )


class TestQueries(unittest.TestCase):

    def setUp(self):
        NumberModel.collection().remove()
        names = 'zero one two three four five six seven eight nine ten'.split()
        self.nums = [
                NumberModel(n=i, quad=((i-5)**2), name=names[i] ).save()
                for i in xrange(len(names))
                ]

    def tearDown(self):
        for num in self.nums:
            num.delete()

    def test_query(self):
        n = NumberModel.n
        name = NumberModel.name
        self.failUnlessEqual( [8,9,10], _query_to_list( n>7 ) )
        self.failUnlessEqual( [4,5], _query_to_list( (n>3) & (n<6) ) )
        self.failUnlessEqual( [4,5,10], _query_to_list(
            (n>3) & (name//'^[tf]') )
        )
    
    def test_or(self):
        n = NumberModel.n
        quad = NumberModel.quad
        name = NumberModel.name
        self.failUnlessEqual( [2,4,6], _query_to_list( (n==2)|(n==4)|(n==6) ) )
        self.failUnlessEqual( [1,4,5,9], _query_to_list(
            ((quad>15)&(quad<17)) | ((n>=4)&(n<=5)) ))
        self.failUnlessEqual( [0,3,6,7,10], _query_to_list(
            ((quad>15)|(quad<8)) & ((n<4)|(n>5)) ))

if __name__ == '__main__':
    from random import random
    maroon.connect(db_name='test_maroon')
    unittest.main()
