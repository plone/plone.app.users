# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import plone.app.users


class PloneAppUsersLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=plone.app.users)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'plone.app.users:default')


PLONE_APP_USERS_FIXTURE = PloneAppUsersLayer()


PLONE_APP_USERS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONE_APP_USERS_FIXTURE,),
    name='PloneAppUsersLayer:IntegrationTesting',
)


PLONE_APP_USERS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONE_APP_USERS_FIXTURE,),
    name='PloneAppUsersLayer:FunctionalTesting',
)


PLONE_APP_USERS_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        PLONE_APP_USERS_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='PloneAppUsersLayer:AcceptanceTesting',
)
