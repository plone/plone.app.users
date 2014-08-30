# -*- coding: utf-8 -*-
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.testing.z2 import Browser
from plone.app.users.testing import PLONE_APP_USERS_INTEGRATION_TESTING

import transaction
import unittest


class TestNewUser(unittest.TestCase):

    layer = PLONE_APP_USERS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        app = self.layer['app']
        setRoles(self.portal, TEST_USER_ID, ['Manager', ])
        self.browser = Browser(app)

    def test_new_user_as_site_administrator(self):
        self.portal.acl_users._doAddUser(
            'siteadmin', 'secret', ['Site Administrator'], []
        )
        # make the user available
        transaction.commit()

        self.browser.addHeader('Authorization', 'Basic siteadmin:secret')
        self.browser.open('http://nohost/plone/new-user')
        self.browser.getControl('User Name').value = 'newuser'
        self.browser.getControl('E-mail').value = 'newuser@example.com'
        self.browser.getControl('Password').value = 'foobar'
        self.browser.getControl('Confirm password').value = 'foobar'
        self.browser.getControl('Site Administrators').selected = True
        self.browser.getControl('Register').click()

        # make sure the new user is in the Site Administrators group
        self.assertTrue(
            'Site Administrator' in
            self.portal.acl_users.getUserById('newuser').getRoles()
        )
