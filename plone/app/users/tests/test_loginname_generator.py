# -*- coding: utf-8 -*-
from plone.app.users.browser.interfaces import ILoginNameGenerator
from plone.app.users.browser.register import BaseRegistrationForm
from plone.app.users.testing import PLONE_APP_USERS_INTEGRATION_TESTING
from zope.component import getSiteManager

import unittest


class TestGenerateLoginName(unittest.TestCase):

    layer = PLONE_APP_USERS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def test_generate_user_id_simplistic(self):
        sm = getSiteManager(context=self.portal)

        # Without a function, return username
        self.assertEqual(
            self._generate_login_name(dict(username='frank')),
            'frank'
        )

        # Generator overrides this behavior
        sm.registerUtility(lambda data: data['useme'],
                           provided=ILoginNameGenerator)
        self.assertEqual(
            self._generate_login_name(dict(useme='me me me',
                                           username='frank')),
            'me me me'
        )

    def _generate_login_name(self, data):
        """Generate login name, optionally registering function first"""
        form = BaseRegistrationForm(self.portal, {})
        return form.generate_login_name(data)
