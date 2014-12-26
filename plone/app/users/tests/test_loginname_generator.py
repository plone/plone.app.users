# -*- coding: utf-8 -*-
# Note: test setup somehow fails when only tests from this file are run.
from plone.app.users.browser.interfaces import ILoginNameGenerator
from plone.app.users.browser.register import BaseRegistrationForm
from plone.app.users.tests.base import BaseTestCase
from zope.component import getSiteManager


class TestGenerateLoginName(BaseTestCase):

    def test_custom_generator(self):
        """Test if a custom login name generator overrides the default
        behavior.
        """
        sm = getSiteManager(context=self.portal)
        form = BaseRegistrationForm(self.portal, {})
        data = {'useme': 'me me me', 'username': 'frank'}

        sm.registerUtility(
            lambda data: data['useme'], provided=ILoginNameGenerator)

        self.assertEqual(form.generate_login_name(data), 'me me me')
        self.assertEqual(data.get('login_name'), 'me me me')

    def test_custom_generator_empty(self):
        """Test that the username is used if a custom login name generator
        returns an empty value.
        """
        sm = getSiteManager(context=self.portal)
        form = BaseRegistrationForm(self.portal, {})
        data = {'useme': '', 'username': 'Frank'}

        sm.registerUtility(
            lambda data: data['useme'], provided=ILoginNameGenerator)

        self.assertEqual(form.generate_login_name(data), 'Frank')
        self.assertEqual(data.get('login_name'), 'Frank')

    def test_use_email_as_login_disabled(self):
        """Test generating user_id with no custom login name generator and
        with the use_email_as_login security setting disabled.
        """
        form = BaseRegistrationForm(self.portal, {})
        data = {'username': 'Frank'}
        self.security_settings.use_email_as_login = False

        self.assertEqual(form.generate_login_name(data), 'Frank')
        self.assertEqual(data.get('login_name'), 'Frank')

    def test_use_email_as_login_enabled(self):
        """Test generating user_id with no custom login name generator and
        with the use_email_as_login security setting enabled.
        """
        form = BaseRegistrationForm(self.portal, {})
        data = {'username': 'Frank', 'email': 'Frank@Test.com'}
        self.security_settings.use_email_as_login = True

        self.assertEqual(form.generate_login_name(data), 'frank@test.com')
        self.assertEqual(data.get('login_name'), 'frank@test.com')
