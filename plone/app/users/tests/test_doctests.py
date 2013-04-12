import doctest
from unittest import TestSuite

from Testing.ZopeTestCase import FunctionalDocFileSuite
from Products.PloneTestCase.PloneTestCase import setupPloneSite

from plone.app.users.tests import TestCase

setupPloneSite()

OPTIONFLAGS = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


class DocTestCase(TestCase):
    form_library = 'formlib'


class Z3CDocTestCase(TestCase):
    form_library = 'z3c.form'


def test_suite():
    tests = []
    suite = TestSuite()
    for test in tests:
        suite.addTest(FunctionalDocFileSuite(test,
            optionflags=OPTIONFLAGS,
            package="plone.app.users.tests",
            test_class=DocTestCase))
    return suite
