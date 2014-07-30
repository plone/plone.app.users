# -*- coding: utf-8 -*-
from Products.CMFPlone.tests.utils import MockMailHost
from Products.MailHost.interfaces import IMailHost
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing.layers import FunctionalTesting
from plone.app.testing.layers import IntegrationTesting
from zope.component import getSiteManager
from zope.configuration import xmlconfig

import doctest


class PloneAppUsersLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        import plone.app.users
        xmlconfig.file(
            'configure.zcml',
            plone.app.users,
            context=configurationContext
        )

    def setUpPloneSite(self, portal):
        # Configure mock mail host
        mail_host = portal.MailHost = MockMailHost('MailHost')
        site_manager = getSiteManager(portal)
        site_manager.unregisterUtility(provided=IMailHost)
        site_manager.registerUtility(mail_host, IMailHost)


PLONE_APP_USERS_FIXTURE = PloneAppUsersLayer()
PLONE_APP_USERS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONE_APP_USERS_FIXTURE, ),
    name='PloneAppUsersLayer:Integration'
)
PLONE_APP_USERS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONE_APP_USERS_FIXTURE, ),
    name='PloneAppUsersLayer:Functional'
)


optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
