# -*- coding: utf-8 -*-
from plone.app.testing.bbb import PTC_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing.layers import FunctionalTesting

import doctest


class PloneAppUsersLayer(PloneSandboxLayer):
    defaultBases = (PTC_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        import plone.app.users
        self.loadZCML(package=plone.app.users)

PLONE_APP_USERS_FIXTURE = PloneAppUsersLayer()
PLONE_APP_USERS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONE_APP_USERS_FIXTURE, ),
    name='PloneAppUsersLayer:Functional')


optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE | doctest.REPORT_ONLY_FIRST_FAILURE)
