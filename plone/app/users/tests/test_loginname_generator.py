# Note: test setup somehow fails when only tests from this file are run.
from zope.component import getSiteManager

from plone.app.users.browser.interfaces import ILoginNameGenerator
from plone.app.users.browser.register import BaseRegistrationForm
from plone.app.users.tests.base import BaseTestCase


class TestGenerateLoginName(BaseTestCase):
    def test_generate_user_id_simplistic(self):
        sm = getSiteManager(context=self.portal)

        # Without a function, return username
        self.assertEqual(
            self.generateLoginName(dict(username='frank')),
            'frank'
        )

        # Generator overrides this behavior
        sm.registerUtility(lambda data: data['useme'], provided=ILoginNameGenerator)
        self.assertEqual(
            self.generateLoginName(dict(useme='me me me', username='frank')),
            'me me me'
        )

    def generateLoginName(self, data):
        """Generate login name, optionally registering function first"""
        form = BaseRegistrationForm(self.portal, {})
        return form.generate_login_name(data)
