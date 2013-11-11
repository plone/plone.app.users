# Note: test setup somehow fails when only tests from this file are run.
from zope.component import getSiteManager

from plone.app.users.browser.interfaces import IUserIdGenerator
from plone.app.users.browser.register import BaseRegistrationForm
from plone.app.users.tests.base import BaseTestCase
from plone.app.users.utils import uuid_userid_generator


class TestGenerateUserId(BaseTestCase):

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

    def test_generate_user_id_with_uuid(self):
        sm = getSiteManager(context=self.portal)
        sm.registerUtility(uuid_userid_generator, provided=IUserIdGenerator)
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


class TestGenerateUUIDUserId(BaseTestCase):

    def afterSetUp(self):
        super(TestGenerateUUIDUserId, self).afterSetUp()
        # If use_uuid_as_userid is set in the site_properties, we
        # generate a uuid.
        self.ptool = ptool = getattr(self.portal, 'portal_properties')
        if not ptool.site_properties.hasProperty('use_uuid_as_userid'):
            ptool.site_properties.manage_addProperty(
                'use_uuid_as_userid', False, 'boolean'
            )  # Try to add it.
        ptool.site_properties.manage_changeProperties(
            use_uuid_as_userid=True
        )  # Change it.
        ptool.site_properties.getProperty('use_uuid_as_userid')

    def test_generate_uuid_user_id(self):
        self.assertTrue(
            self.ptool.site_properties.getProperty('use_uuid_as_userid')
        )
        form = BaseRegistrationForm(self.portal, {})
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
