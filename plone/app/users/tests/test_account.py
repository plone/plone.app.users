from plone.app.users.browser.account import AccountPanelSchemaAdapter
from plone.testing import zope
from Products.CMFCore.interfaces import IMembershipTool
from zope.component import provideUtility
from zope.interface import implementer

import unittest


@implementer(IMembershipTool)
class DummyPortalMembership:
    def __init__(self, allowed):
        self.allowed = allowed

    def getMemberById(self, id):
        return id

    def getAuthenticatedMember(self):
        return "(authenticated)"

    def checkPermission(self, permission, context):
        return self.allowed


class TestAccountPanelSchemaAdapter(unittest.TestCase):
    layer = zope.INTEGRATION_TESTING

    def test__init__no_userid(self):
        """Should edit current user."""
        provideUtility(DummyPortalMembership(False))
        adapter = AccountPanelSchemaAdapter(self.layer["request"])
        self.assertEqual("(authenticated)", adapter.context)

    def test__init__userid_in_request_form_for_non_manager(self):
        """Disallow for non-privileged users."""
        provideUtility(DummyPortalMembership(False))
        self.layer["request"].form["userid"] = "bob"
        adapter = AccountPanelSchemaAdapter(self.layer["request"])
        self.assertEqual("(authenticated)", adapter.context)

    def test__init__userid_in_request_form_for_manager(self):
        """Should allow for privileged users."""
        provideUtility(DummyPortalMembership(True))
        self.layer["request"].form["userid"] = "bob"
        adapter = AccountPanelSchemaAdapter(self.layer["request"])
        self.assertEqual("bob", adapter.context)
