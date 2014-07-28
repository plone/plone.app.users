# -*- coding: utf-8 -*-
from Products.PloneTestCase.PloneTestCase import setupPloneSite
from Testing.ZopeTestCase import FunctionalDocFileSuite
from plone.app.users.tests.base import BaseTestCase
from unittest import TestSuite

import doctest


setupPloneSite()
OPTIONFLAGS = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)

doc_tests = [
    'duplicate_email.rst',
    'email_login.rst',
    'flexible_user_registration.rst',
    'forms_navigationroot.rst',
    'member_search.rst',
    'registration_forms.rst',
    'password.rst',
    'personal_preferences.rst',
    'personal_preferences_prefs_user_details.rst',
    'userdata.rst',
    'userdata_prefs_user_details.rst',
    '../vocabularies.py',
]


def test_suite():
    suite = TestSuite()
    for test_file in doc_tests:
        suite.addTest(FunctionalDocFileSuite(
            test_file,
            optionflags=OPTIONFLAGS,
            package='plone.app.users.tests',
            test_class=BaseTestCase
        ))
    return suite
