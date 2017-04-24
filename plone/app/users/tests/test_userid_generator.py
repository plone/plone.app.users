# -*- coding: utf-8 -*-
# Note: test setup somehow fails when only tests from this file are run.
from plone.app.users.browser.interfaces import IUserIdGenerator
from plone.app.users.browser.register import BaseRegistrationForm
from plone.app.users.tests.base import BaseTestCase
from plone.app.users.utils import uuid_userid_generator
from zope.component import getSiteManager


class TestGenerateUserId(BaseTestCase):

    def test_custom_generator(self):
        """Test if a custom user id generator overrides the default
        behavior.
        """

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

    def test_default(self):
        """Test generating user_id with no custom user id generator and
        the default security settings.
        """
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
        data = {'email': 'Joe@example.org'}
        self.assertEqual(form.generate_user_id(data), 'Joe@example.org')
        self.assertEqual(data.get('user_id'), 'Joe@example.org')

    def test_use_email_as_login_has_fullname(self):
        """"Test generating a user id if the use_email_as_login setting is
        enabled and full name is provided.
        """
        self.security_settings.use_email_as_login = True
        form = BaseRegistrationForm(self.portal, {})

        data = {}
        self.assertEqual(form.generate_user_id(data), '')
        self.assertEqual(data.get('user_id'), '')

        data = {'fullname': 'Joe User',
                'email': 'joe@example.org'}
        self.assertEqual(form.generate_user_id(data), 'joe-user')
        self.assertEqual(data.get('user_id'), 'joe-user')

    def test_use_email_as_login_no_fullname(self):
        """"Test generating a user id if the use_email_as_login setting is
        enabled and full name is not provided.
        """
        self.security_settings.use_email_as_login = True
        form = BaseRegistrationForm(self.portal, {})

        data = {}
        self.assertEqual(form.generate_user_id(data), '')
        self.assertEqual(data.get('user_id'), '')

        data = {'email': 'joe@example.org'}
        self.assertEqual(form.generate_user_id(data), 'joe@example.org')
        self.assertEqual(data.get('user_id'), 'joe@example.org')

    def test_use_email_as_login_no_fullname_uppercase_email(self):
        """"Test generating a user id if the use_email_as_login setting is
        enabled and full name is not provided, with an uppercase e-mail.
        """
        self.security_settings.use_email_as_login = True
        form = BaseRegistrationForm(self.portal, {})

        data = {}
        self.assertEqual(form.generate_user_id(data), '')
        self.assertEqual(data.get('user_id'), '')

        data = {'email': 'Joe@Example.org'}
        self.assertEqual(form.generate_user_id(data), 'joe@example.org')
        self.assertEqual(data.get('user_id'), 'joe@example.org')

    def test_use_uuid_as_userid_enabled(self):
        """Test generating a user id if the use_uuid_as_userid setting is
        enabled.
        """
        self.security_settings.use_uuid_as_userid = True
        form = BaseRegistrationForm(self.portal, {})

        data = {}
        user_id = form.generate_user_id(data)
        self.assertEqual(data.get('user_id'), user_id)
        self.assertEqual(len(data.get('user_id')),
                         len(uuid_userid_generator()))

        data = {'username': 'joe',
                'fullname': 'Joe User',
                'email': 'joe@example.org'}
        user_id = form.generate_user_id(data)
        self.assertNotEqual(user_id, 'joe')
        self.assertEqual(data.get('user_id'), user_id)
        self.assertEqual(len(user_id), len(uuid_userid_generator()))

        # Calling it twice should give a different result, as every
        # call to the uuid generator should be unique.
        self.assertNotEqual(form.generate_user_id(data),
                            form.generate_user_id(data))
