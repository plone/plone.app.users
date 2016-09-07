from plone.app.users.browser.personalpreferences import UserDataPanel
from plone.app.users.tests.base import TestCase
from zExceptions import NotFound
from zope.i18n import translate


class TestUserDataPanel(TestCase):

    def test_regression(self):
        portal = self.portal
        request = portal.REQUEST
        request.form.update({
            'userid': 'admin'
        })
        form = UserDataPanel(portal, request)
        description = translate(form.description, context=request)
        self.assertTrue('admin' in description)
        # form can be called without raising exception.
        self.assertTrue(form())

    def test_escape_html(self):
        portal = self.portal
        request = portal.REQUEST
        request.form.update({
            'userid': 'admin<script>alert("userid")</script>'
        })
        form = UserDataPanel(portal, request)
        description = translate(form.description, context=request)
        self.assertTrue('<script>' not in description)
        self.assertRaises(NotFound, form)
