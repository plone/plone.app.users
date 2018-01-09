# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from plone.app.users.browser.userdatapanel import UserDataPanel
from plone.app.users.testing import PLONE_APP_USERS_FUNCTIONAL_TESTING
from plone.app.testing import applyProfile
from plone.app.testing.bbb import PloneTestCase
from plone.testing import z2
from zExceptions import NotFound
from zope.i18n import translate

import unittest


class TestUserDataPanel(PloneTestCase):

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

    def test_pam(self):
        import plone.app.multilingual
        self.loadZCML(package=plone.app.multilingual)
        z2.installProduct(app, 'plone.app.multilingual')
        applyProfile(portal, 'plone.app.multilingual:default')
        language_tool = getToolByName(portal, 'portal_languages')
        language_tool.addSupportedLanguage('fr')
        language_tool.addSupportedLanguage('it')
        self.browser.addHeader('Authorization', 'Basic siteadmin:secret')
        self.browser.open('http://nohost/plone/en/@@personal-information')

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
