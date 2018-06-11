# -*- coding: utf-8 -*-
from plone.app.users.testing import PLONE_APP_USERS_ACCEPTANCE_TESTING
from plone.testing import layered

import os
import robotsuite
import unittest


def test_suite():
    suite = unittest.TestSuite()
    for testfile in os.listdir(
            os.path.join(os.path.dirname(__file__), "acceptance")):
        testfilepath = os.path.join("acceptance", testfile)
#        if not os.path.isdir(testfilepath) and testfile.endswith('.robot'):
#            suite.addTests([
#                layered(
#                    robotsuite.RobotTestSuite(
#                        testfilepath,
#                        noncritical=['fixme']),
#                    layer=PLONE_APP_USERS_ACCEPTANCE_TESTING),
#            ])
    return suite
