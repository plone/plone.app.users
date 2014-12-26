# -*- coding: utf-8 -*-
from plone.app.users.browser.account import AccountPanelSchemaAdapter
from plone.app.users.tests.base import BaseTestCase


class DummyPortalMembership(object):

    def __init__(self, allowed):
        self.allowed = allowed

    def getMemberById(self, id):
        return id

    def getAuthenticatedMember(self):
        return '(authenticated)'

    def checkPermission(self, permission, context):
        return self.allowed


class TestAccountPanelSchemaAdapter(BaseTestCase):

    def test__init__no_userid(self):
        """Should edit current user."""
        self.request.portal_membership = DummyPortalMembership(False)
        adapter = AccountPanelSchemaAdapter(self.request)
        self.assertEqual('(authenticated)', adapter.context)

    def test__init__userid_in_request_form_for_non_manager(self):
        """Disallow for non-privileged users."""
        self.request.portal_membership = DummyPortalMembership(False)
        self.request.REQUEST.form['userid'] = 'bob'
        adapter = AccountPanelSchemaAdapter(self.request)
        self.assertEqual('(authenticated)', adapter.context)

    def test__init__userid_in_request_form_for_manager(self):
        """Should allow for privileged users."""
        self.request.portal_membership = DummyPortalMembership(True)
        self.request.REQUEST.form['userid'] = 'bob'
        adapter = AccountPanelSchemaAdapter(self.request)
        self.assertEqual('bob', adapter.context)
