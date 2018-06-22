# -*- coding: utf-8 -*-
from plone.app.users.testing import PLONE_APP_USERS_FUNCTIONAL_TESTING
from plone.testing import layered

import doctest
import re
import six
import unittest


doc_tests = [
    'duplicate_email.rst',
    'email_login.rst',
    'flexible_user_registration.rst',
    'forms_navigationroot.rst',  # need to ask about content types layer
    'member_search.rst',
    'registration_forms.rst',  # working on it
    'password.rst',  # for later
    'personal_preferences.rst',
    'personal_preferences_prefs_user_details.rst',
    'userdata.rst',
    'userdata_prefs_user_details.rst',
    '../vocabularies.py',
]

optionflags = (
    doctest.ELLIPSIS |
    doctest.NORMALIZE_WHITESPACE |
    doctest.REPORT_ONLY_FIRST_FAILURE
)


class Py23DocChecker(doctest.OutputChecker):
    def check_output(self, want, got, optionflags):
        if six.PY2:
            got = got.replace('Unauthorized', 'zExceptions.unauthorized.Unauthorized')
            got = got.replace(':utf8:ustring', '')
            got = re.sub("u'(.*?)'", "'\\1'", got)
            want = re.sub("b'(.*?)'", "'\\1'", want)
        return doctest.OutputChecker.check_output(self, want, got, optionflags)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(
            doctest.DocFileSuite(
                'tests/{0}'.format(test_file),
                package='plone.app.users',
                optionflags=optionflags,
                checker=Py23DocChecker(),
            ),
            layer=PLONE_APP_USERS_FUNCTIONAL_TESTING)
        for test_file in doc_tests
    ])

    return suite
