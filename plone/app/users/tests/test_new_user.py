from plone.app.testing import TEST_USER_PASSWORD
from plone.app.users.tests.base import BaseTestCase
from plone.app.users.utils import uuid_userid_generator
from Products.CMFCore.utils import getToolByName

import transaction


class TestNewUser(BaseTestCase):
    def test_new_user_as_site_administrator(self):
        self.portal.acl_users._doAddUser(
            "siteadmin", TEST_USER_PASSWORD, ["Site Administrator"], []
        )
        # make the user available
        transaction.commit()

        self.browser.addHeader("Authorization", f"Basic siteadmin:{TEST_USER_PASSWORD}")
        self.browser.open("http://nohost/plone/new-user")
        self.browser.getControl("User Name").value = "newuser"
        self.browser.getControl("Email").value = "newuser@example.com"
        self.browser.getControl("Password").value = TEST_USER_PASSWORD
        self.browser.getControl("Confirm password").value = TEST_USER_PASSWORD
        self.browser.getControl("Site Administrators").selected = True
        self.browser.getControl("Register").click()

        # make sure the new user is in the Site Administrators group
        self.assertTrue(
            "Site Administrator"
            in self.portal.acl_users.getUserById("newuser").getRoles()
        )


class TestGenerateUserIdLoginName(BaseTestCase):
    """Test if the user id and user name are properly generated based on the
    security settings.
    """

    def setUp(self):
        super().setUp()
        self.portal_url = self.portal.absolute_url()
        self.portal.acl_users._doAddUser(
            "siteadmin", TEST_USER_PASSWORD, ["Site Administrator"], []
        )
        transaction.commit()
        self.browser.addHeader("Authorization", f"Basic siteadmin:{TEST_USER_PASSWORD}")

    def test_uuid_disabled_email_as_login_disabled(self):
        self.security_settings.use_uuid_as_userid = False
        self.security_settings.use_email_as_login = False
        transaction.commit()

        # create a user
        self.browser.open("http://nohost/plone/@@new-user")
        self.browser.getControl("Full Name").value = "New User"
        self.browser.getControl("User Name").value = "newie"
        self.browser.getControl("Email").value = "NewUser@Example.Com"
        self.browser.getControl("Password").value = TEST_USER_PASSWORD
        self.browser.getControl("Confirm password").value = TEST_USER_PASSWORD
        self.browser.getControl("Register").click()

        # user id should be set the same as user name
        pas = getToolByName(self.portal, "acl_users")
        self.assertEqual(len(pas.searchUsers(name="newie")), 1)
        user = pas.getUser("newie")
        self.assertEqual(user.getId(), "newie")
        self.assertEqual(user.getUserName(), "newie")

    def test_uuid_disabled_email_as_login_enabled_no_full_name(self):
        self.security_settings.use_uuid_as_userid = False
        self.security_settings.use_email_as_login = True
        transaction.commit()

        # create a user
        self.browser.open("http://nohost/plone/@@new-user")
        self.browser.getControl("Email").value = "newuser@example.com"
        self.browser.getControl("Password").value = TEST_USER_PASSWORD
        self.browser.getControl("Confirm password").value = TEST_USER_PASSWORD
        self.browser.getControl("Register").click()

        # Since full name is not provided, the user id is set based on the
        # e-mail, the same as the user name.
        pas = getToolByName(self.portal, "acl_users")
        self.assertEqual(len(pas.searchUsers(name="newuser@example.com")), 1)
        self.assertEqual(len(pas.searchUsers(name="newuser@example.com")), 1)
        user = pas.getUser("newuser@example.com")
        self.assertEqual(user.getId(), "newuser@example.com")
        self.assertEqual(user.getUserName(), "newuser@example.com")

    def test_uuid_disabled_email_as_login_enabled_no_full_name_uppercase(self):
        self.security_settings.use_uuid_as_userid = False
        self.security_settings.use_email_as_login = True
        transaction.commit()

        # create a user
        self.browser.open("http://nohost/plone/@@new-user")
        self.browser.getControl("Email").value = "NewUser@Example.Com"
        self.browser.getControl("Password").value = TEST_USER_PASSWORD
        self.browser.getControl("Confirm password").value = TEST_USER_PASSWORD
        self.browser.getControl("Register").click()

        # the user id is set based on the e-mail, which should be lowercased
        pas = getToolByName(self.portal, "acl_users")
        self.assertEqual(len(pas.searchUsers(name="newuser@example.com")), 1)
        self.assertEqual(len(pas.searchUsers(name="NewUser@Example.Com")), 1)
        user = pas.getUser("newuser@Example.Com")
        self.assertEqual(user.getId(), "newuser@example.com")
        self.assertEqual(user.getUserName(), "newuser@example.com")

    def test_uuid_disabled_email_as_login_enabled_has_full_name(self):
        self.security_settings.use_uuid_as_userid = False
        self.security_settings.use_email_as_login = True
        transaction.commit()

        # create a user
        self.browser.open("http://nohost/plone/@@new-user")
        self.browser.getControl("Full Name").value = "New User"
        self.browser.getControl("Email").value = "NewUser@Example.Com"
        self.browser.getControl("Password").value = TEST_USER_PASSWORD
        self.browser.getControl("Confirm password").value = TEST_USER_PASSWORD
        self.browser.getControl("Register").click()

        # User id should be set based on the full name, user name should be
        # set based on the e-mail.
        pas = getToolByName(self.portal, "acl_users")
        self.assertEqual(len(pas.searchUsers(name="newuser@example.com")), 1)
        self.assertEqual(len(pas.searchUsers(name="NewUser@Example.Com")), 1)
        user = pas.getUser("newuser@Example.Com")
        self.assertEqual(user.getId(), "new-user")
        self.assertEqual(user.getUserName(), "newuser@example.com")

    def test_uuid_enabled_email_as_login_disabled(self):
        self.security_settings.use_uuid_as_userid = True
        self.security_settings.use_email_as_login = False
        transaction.commit()

        # create a user
        self.browser.open("http://nohost/plone/@@new-user")
        self.browser.getControl("Full Name").value = "New User"
        self.browser.getControl("User Name").value = "newie"
        self.browser.getControl("Email").value = "NewUser@Example.Com"
        self.browser.getControl("Password").value = TEST_USER_PASSWORD
        self.browser.getControl("Confirm password").value = TEST_USER_PASSWORD
        self.browser.getControl("Register").click()

        # uuid should be used for the user id
        pas = getToolByName(self.portal, "acl_users")
        self.assertEqual(len(pas.searchUsers(name="newie")), 1)
        user = pas.getUser("newie")
        self.assertEqual(len(user.getId()), len(uuid_userid_generator()))
        self.assertNotEqual(user.getId(), "newuser@example.com")
        self.assertNotEqual(user.getId(), "newie")
        self.assertNotEqual(user.getId(), "new-user")
        self.assertEqual(user.getUserName(), "newie")

    def test_uuid_enabled_email_as_login_enabled(self):
        self.security_settings.use_uuid_as_userid = True
        self.security_settings.use_email_as_login = True
        transaction.commit()

        # create a user
        self.browser.open("http://nohost/plone/@@new-user")
        self.browser.getControl("Full Name").value = "New User"
        self.browser.getControl("Email").value = "NewUser@Example.Com"
        self.browser.getControl("Password").value = TEST_USER_PASSWORD
        self.browser.getControl("Confirm password").value = TEST_USER_PASSWORD
        self.browser.getControl("Register").click()

        # uuid should be used for the user id, user name should be based on
        # the e-mail
        pas = getToolByName(self.portal, "acl_users")
        self.assertEqual(len(pas.searchUsers(name="newuser@example.com")), 1)
        self.assertEqual(len(pas.searchUsers(name="NewUser@Example.Com")), 1)
        user = pas.getUser("newuser@example.com")
        self.assertEqual(len(user.getId()), len(uuid_userid_generator()))
        self.assertNotEqual(user.getId(), "newuser@example.com")
        self.assertNotEqual(user.getId(), "newie")
        self.assertNotEqual(user.getId(), "new-user")
        self.assertEqual(user.getUserName(), "newuser@example.com")
