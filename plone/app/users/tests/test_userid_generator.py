from zope.component import getSiteManager

from plone.app.users.browser.interfaces import IUserIdGenerator
from plone.app.users.browser.register import BaseRegistrationForm
from plone.app.users.tests.base import TestCase


class TestGenerateUserId(TestCase):

    def test_standard_generate_user_id(self):
        form = BaseRegistrationForm(self.portal, {})
        data = {}
        self.assertEqual(form.generate_user_id(data), '')
        self.assertEqual(data.get('user_id'), '')

        # An explicit username is taken by default.
        data = {'username': 'joe',
                'fullname': 'Joe User',
                'email': 'joe@example.org'}
        self.assertEqual(form.generate_user_id(data), 'joe')
        self.assertEqual(data.get('user_id'), 'joe')

        # When no username is there, we try a normalized fullname.
        data = {'fullname': 'Joe User',
                'email': 'joe@example.org'}
        self.assertEqual(form.generate_user_id(data), 'joe-user')
        self.assertEqual(data.get('user_id'), 'joe-user')

        # With no fullname, we take the email.
        data = {'email': 'joe@example.org'}
        self.assertEqual(form.generate_user_id(data), 'joe@example.org')
        self.assertEqual(data.get('user_id'), 'joe@example.org')

    def test_generate_user_id_simplistic(self):
        # Test a simplistic user id generator.
        def one_generator(data):
            return 'one'

        sm = getSiteManager(context=self.portal)
        sm.registerUtility(one_generator, provided=IUserIdGenerator)
        form = BaseRegistrationForm(self.portal, {})

        data = {}
        self.assertEqual(form.generate_user_id(data), 'one')
        self.assertEqual(data.get('user_id'), 'one')

        data = {'username': 'joe',
                'fullname': 'Joe User',
                'email': 'joe@example.org'}
        self.assertEqual(form.generate_user_id(data), 'one')
        self.assertEqual(data.get('user_id'), 'one')

    def test_generate_user_id_email(self):
        # It is easy to force the email as user id.
        def email_getter(data):
            return data.get('email')

        sm = getSiteManager(context=self.portal)
        sm.registerUtility(email_getter, provided=IUserIdGenerator)
        form = BaseRegistrationForm(self.portal, {})

        data = {}
        self.assertEqual(form.generate_user_id(data), '')
        self.assertEqual(data.get('user_id'), '')

        data = {'username': 'joe',
                'fullname': 'Joe User',
                'email': 'joe@example.org'}
        self.assertEqual(form.generate_user_id(data), 'joe@example.org')
        self.assertEqual(data.get('user_id'), 'joe@example.org')
