# -*- coding: utf-8 -*-
from Products.CMFPlone.tests.utils import MockMailHost
from Products.MailHost.interfaces import IMailHost
from plone.app.testing.bbb import PTC_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing.layers import FunctionalTesting
from zope.component import getSiteManager
from zope.configuration import xmlconfig

import doctest


class PloneAppUsersLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        import plone.app.users
        self.loadZCML(package=plone.app.users)

    def setUpPloneSite(self, portal):
        # Configure mock mail host
        mail_host = portal.MailHost = MockMailHost('MailHost')
        site_manager = getSiteManager(portal)
        site_manager.unregisterUtility(provided=IMailHost)
        site_manager.registerUtility(mail_host, IMailHost)

    def addParrotPasswordPolicy(self):
        a = 2
        """# remove default policy
        uf = self.portal.acl_users
        for policy in uf.objectIds(['Default Plone Password Policy']):
            uf.plugins.deactivatePlugin(IValidationPlugin, policy)

        obj = DeadParrotPassword('test')
        uf._setObject(obj.getId(), obj)
        obj = uf[obj.getId()]
        activatePluginInterfaces(self.portal, obj.getId())

        portal = getUtility(ISiteRoot)
        pas_instance = portal.acl_users
        plugins = pas_instance._getOb('plugins')
        validators = plugins.listPlugins(IValidationPlugin)
        assert validators"""



PLONE_APP_USERS_FIXTURE = PloneAppUsersLayer()
PLONE_APP_USERS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONE_APP_USERS_FIXTURE, ),
    name='PloneAppUsersLayer:Functional'
)


optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
