from plone.app.multilingual.browser.setup import SetupMultilingualSite
from plone.app.testing import applyProfile
from plone.app.testing import login
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.testing.layers import FunctionalTesting
from plone.testing import zope
from Products.CMFCore.utils import getToolByName

import unittest


class WITHPAMLayer(PloneSandboxLayer):
    def setUpPloneSite(self, portal):
        applyProfile(portal, "plone.app.multilingual:default")
        setRoles(portal, TEST_USER_ID, ["Manager"])
        login(portal, TEST_USER_NAME)
        language_tool = getToolByName(portal, "portal_languages")
        language_tool.addSupportedLanguage("fr")
        language_tool.addSupportedLanguage("it")
        setup_tool = SetupMultilingualSite()
        setup_tool.setupSite(portal)


WITHPAM_FIXTURE = WITHPAMLayer()

WITHPAM_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(WITHPAM_FIXTURE,), name="PloneAppUsersWithPAMLayer:Functional"
)


class TestUserDataPanelWithPAM(unittest.TestCase):
    layer = WITHPAM_FUNCTIONAL_TESTING

    def test_pam(self):
        browser = zope.Browser(self.layer["app"])
        browser.addHeader(
            "Authorization", f"Basic {TEST_USER_NAME}:{TEST_USER_PASSWORD}"
        )
        browser.open("http://nohost/plone/fr/@@personal-information")
        self.assertIn(
            "Saisissez votre nom complet, par exemple Jean Dupont.",
            browser.contents,
        )
