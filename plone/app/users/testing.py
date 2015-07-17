# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import AUTOLOGIN_LIBRARY_FIXTURE
from plone.app.testing.bbb import PTC_FIXTURE
from plone.app.testing.bbb import PTC_FUNCTIONAL_TESTING
from plone.app.testing.layers import FunctionalTesting
from plone.testing import z2

import doctest

PLONE_APP_USERS_FIXTURE = PTC_FIXTURE
PLONE_APP_USERS_FUNCTIONAL_TESTING = PTC_FUNCTIONAL_TESTING

PLONE_APP_USERS_ROBOT = FunctionalTesting(
    bases=(PLONE_APP_USERS_FIXTURE,
           AUTOLOGIN_LIBRARY_FIXTURE,
           z2.ZSERVER_FIXTURE),
    name="PloneAppUsersLayer:Robot")

optionflags = (
    doctest.ELLIPSIS |
    doctest.NORMALIZE_WHITESPACE |
    doctest.REPORT_ONLY_FIRST_FAILURE
)
