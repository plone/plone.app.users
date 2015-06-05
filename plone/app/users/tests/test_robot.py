import unittest
import os
import robotsuite
from plone.app.users.testing import PLONE_APP_USERS_ROBOT
from plone.testing import layered


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
#                    layer=PLONE_APP_USERS_ROBOT),
#            ])
    return suite
