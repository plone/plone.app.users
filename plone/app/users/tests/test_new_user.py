from plone.app.users.tests.base import TestCase
from urllib2 import HTTPError


class TestNewUser(TestCase):

    def test_new_user_as_site_administrator(self):
        self.portal.acl_users._doAddUser('siteadmin', 'secret', ['Site Administrator'], [])
        self.browser.addHeader('Authorization', 'Basic siteadmin:secret')
        self.browser.open('http://nohost/plone/new-user')
        self.browser.getControl('User Name').value = 'newuser'
        self.browser.getControl('E-mail').value = 'newuser@example.com'
        self.browser.getControl('Password').value = 'foobar'
        self.browser.getControl('Confirm password').value = 'foobar'
        self.browser.getControl('Site Administrators').selected = True
        self.browser.getControl('Register').click()

        # make sure the new user is in the Site Administrators group
        self.assertTrue('Site Administrator' in
            self.portal.acl_users.getUserById('newuser').getRoles())

    def test_new_user_with_portrait_field(self):
        """expose https://dev.plone.org/ticket/15306"""
        # add portrait field to the fields shown for registration
        site_props = self.portal.portal_properties.site_properties
        site_props._updateProperty(
            'user_registration_fields',
            ['fullname', 'username', 'email', 'password', 'home_page', 'portrait']
        )
        # log in to a browser as an admin user
        self.portal.acl_users._doAddUser('siteadmin', 'secret', ['Site Administrator'], [])
        self.browser.addHeader('Authorization', 'Basic siteadmin:secret')
        # attempting to open the new user form will throw an error if 15306
        # reverts, due to a Component Lookup Error on the FileUpload field
        try:
            self.browser.open('http://nohost/plone/new-user')
        except HTTPError as e:
            # get the error just thrown
            err = self.portal.error_log.getLogEntries()[0]
            msg = "%s:\n %s" % (e, err['tb_text'])
            self.fail(msg)
