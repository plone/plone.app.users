# -*- coding: utf-8 -*-
from plone.app.users.testing import PLONE_APP_USERS_FUNCTIONAL_TESTING
from plone.app.users.testing import optionflags
from plone.testing import layered

import doctest
import unittest


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
    suite = unittest.TestSuite()
    suite.addTests([
        layered(
            doctest.DocFileSuite(
                'tests/{0}'.format(test_file),
                package='plone.app.users',
                optionflags=optionflags
            ),
            layer=PLONE_APP_USERS_FUNCTIONAL_TESTING)
        for test_file in doc_tests
    ])

    return suite
