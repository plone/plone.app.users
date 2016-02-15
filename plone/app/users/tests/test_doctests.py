from plone.app.users.tests import TestCase
from Products.PloneTestCase.PloneTestCase import setupPloneSite
from Testing.ZopeTestCase import FunctionalDocFileSuite
from unittest import TestSuite

import doctest
import os


setupPloneSite()

OPTIONFLAGS = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


class DocTestCase(TestCase):
    # Just here to work around a weird error message.
    # And now an extra helper method.

    def get_test_file(self, filename):
        return open(os.path.join(os.path.dirname(__file__), filename))


def test_suite():
    tests = ['flexible_user_registration.txt',
             'forms_navigationroot.txt',
             'registration_forms.txt',
             'userdata.txt',
             'userdata_prefs_user_details.txt',
             'personal_preferences.txt',
             'personal_preferences_prefs_user_details.txt',
             'password.txt'
             ]
    suite = TestSuite()
    for test in tests:
        suite.addTest(FunctionalDocFileSuite(test,
            optionflags=OPTIONFLAGS,
            package="plone.app.users.tests",
            test_class=DocTestCase))
    return suite
