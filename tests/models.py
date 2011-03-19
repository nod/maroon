#!/usr/bin/env python

from maroon import *


class SimpleModel(Model):
    '''
    A very simple example of a model consisting of a few simple members.  This will
    be used to test simple assignment and also dictionary exporting
    '''
    int1 = IntProperty("i1")
    int2 = IntProperty("i2")
    ignored = ['secret']


class PersonModel(Model):
    name = TextProperty("n")
    age = IntProperty("a", default=7)


class FunModel(Model):
    '''
    This is a more complex model used to test all the different field types.
    '''
    enum = EnumProperty("e", ["red", "blue"])
    real = FloatProperty("f")
    date = DateTimeProperty("dt")
    dic = DictProperty("d")
    created = CreatedAtProperty("ca")
    names = ListProperty("ns", basestring)
    part = ModelProperty("me", PersonModel)
