# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from plone.app.multilingual.browser.setup import SetupMultilingualSite
from plone.app.users.browser.userdatapanel import UserDataPanel
from plone.app.users.testing import PLONE_APP_USERS_FUNCTIONAL_TESTING
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME, TEST_USER_PASSWORD
from plone.app.testing import setRoles
from plone.app.testing import login
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing.layers import FunctionalTesting
from plone.app.testing.bbb import PloneTestCase
from plone.testing import z2
from zExceptions import NotFound
from zope.i18n import translate

from transaction import commit
import unittest

class WITHPAMLayer(PloneSandboxLayer):

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'plone.app.multilingual:default')
        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)
        language_tool = getToolByName(portal, 'portal_languages')
        language_tool.addSupportedLanguage('fr')
        language_tool.addSupportedLanguage('it')
        setup_tool = SetupMultilingualSite()
        setup_tool.setupSite(portal)


WITHPAM_FIXTURE = WITHPAMLayer()

WITHPAM_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(WITHPAM_FIXTURE,),
    name="PloneAppUsersWithPAMLayer:Functional")


class TestUserDataPanelWithPAM(PloneTestCase):

    layer = WITHPAM_FUNCTIONAL_TESTING

    def test_pam(self):
        browser = z2.Browser(self.layer['app'])
        browser.addHeader('Authorization', 'Basic %s:%s' % (TEST_USER_NAME, TEST_USER_PASSWORD))
        browser.open('http://nohost/plone/fr/@@personal-information')
        self.assertTrue('Saisissez votre nom complet, par exemple Jean Dupont.' in browser.contents)
