from plone.app.users.tests.base import BaseTestCase
from plone.protect import authenticator as auth
import hmac
from hashlib import sha1 as sha


class TestNewUser(BaseTestCase):

    def test_new_user_as_site_administrator(self):
        self.portal.acl_users._doAddUser(
            'siteadmin', 'secret', ['Site Administrator'], []
        )
        self.browser.addHeader('Authorization', 'Basic siteadmin:secret')
        # XXX need to use auth token here because there is one case of write
        # on read for portlets that isn't hit here...
        ring = auth._getKeyring('siteadmin')
        secret = ring.random()
        token = hmac.new(secret, 'siteadmin', sha).hexdigest()
        self.browser.open('http://nohost/plone/new-user?_authenticator=%s' % (
            token))
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
