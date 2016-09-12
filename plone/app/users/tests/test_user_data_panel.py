from zExceptions import NotFound
from plone.app.users.browser.userdatapanel import UserDataPanel
from plone.app.users.testing import PLONE_APP_USERS_FUNCTIONAL_TESTING
from zope.i18n import translate

import unittest


class TestUserDataPanel(unittest.TestCase):

    layer = PLONE_APP_USERS_FUNCTIONAL_TESTING

    def test_regression(self):
        portal = self.layer['portal']
        request = self.layer['request']
        request.form.update({
            'userid': 'admin'
        })
        form = UserDataPanel(portal, request)
        description = translate(form.description, context=request)
        self.assertTrue('admin' in description)
        # form can be called without raising exception.
        self.assertTrue(form())

    def test_escape_html(self):
        portal = self.layer['portal']
        request = self.layer['request']
        request.form.update({
            'userid': 'admin<script>alert("userid")</script>'
        })
        form = UserDataPanel(portal, request)
        description = translate(form.description, context=request)
        self.assertTrue('<script>' not in description)
        self.assertRaises(NotFound, form)
