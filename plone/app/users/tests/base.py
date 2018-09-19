# -*- coding: utf-8 -*-
"""Base class for flexible user registration test cases.

This is in a separate module because it's potentially useful to other
packages which register accountpanels. They should be able to import it
without the PloneTestCase.setupPloneSite() side effects.
"""
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from OFS.Cache import Cacheable
from plone.app.testing import setRoles
from plone.app.testing import login
from plone.app.users.testing import PLONE_APP_USERS_FUNCTIONAL_TESTING
from plone.registry.interfaces import IRegistry
from plone.testing.z2 import Browser
from Products.CMFPlone.interfaces import ISecuritySchema
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from Products.CMFPlone.tests.utils import MockMailHost
from Products.MailHost.interfaces import IMailHost
from Products.PlonePAS.setuphandlers import activatePluginInterfaces
from Products.PluggableAuthService.interfaces.plugins import IValidationPlugin
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements
from transaction import commit
from zope.component import getSiteManager
from zope.component import getUtility

import unittest


class BaseTestCase(unittest.TestCase):
    """ base test case which adds amin user """

    layer = PLONE_APP_USERS_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.portal.acl_users._doAddUser('admin', 'secret', ['Manager'], [])
        set_mock_mailhost(self.portal)
        self.membership = self.portal.portal_membership
        self.security_settings = get_security_settings()

        self.browser = Browser(self.layer['app'])
        self.request = self.layer['request']

    def tearDown(self):
        login(self.portal, 'admin')
        unset_mock_mailhost(self.portal)
        pas_instance = self.portal.acl_users
        plugin = getattr(pas_instance, 'test', None)
        if plugin is not None:
            plugins = pas_instance._getOb('plugins')
            plugins.deactivatePlugin(IValidationPlugin, 'test')
            # plugins.deactivatePlugin(IPropertiesPlugin, 'test')
            pas_instance.manage_delObjects('test')

    def test_nothing(self):
        """ Add a dummy test here, so the base class 'passes'. """

# Dummy password validation PAS plugin


class DeadParrotPassword(BasePlugin, Cacheable):
    meta_type = 'Test Password Strength Plugin'
    security = ClassSecurityInfo()

    def __init__(self, id, title=None):
        self._id = self.id = id
        self.title = title

    security.declarePrivate('validateUserInfo')

    def validateUserInfo(self, user, set_id, set_info):
        errors = []
        if set_info and set_info.get('password', None) is not None:
            password = set_info['password']
            if password.count('dead') or password == '':
                errors = [{'id': 'password', 'error': u'Must not be dead'}]
            else:
                errors = []
        return errors


# Helper methods used in doctests

def setMailHost():
    registry = getUtility(IRegistry)
    mail_settings = registry.forInterface(IMailSchema, prefix='plone')
    mail_settings.smtp_host = u'localhost'
    mail_settings.email_from_address = 'admin@foo.com'
    commit()


def unsetMailHost():
    registry = getUtility(IRegistry)
    mail_settings = registry.forInterface(IMailSchema, prefix='plone')
    mail_settings.smtp_host = u''
    mail_settings.email_from_address = ''
    commit()


def activateDefaultPasswordPolicy(portal):
    uf = portal.acl_users
    for policy in uf.objectIds(['Default Plone Password Policy']):
        activatePluginInterfaces(portal, policy)


def addParrotPasswordPolicy(portal):
    # remove default policy
    uf = portal.acl_users
    for policy in uf.objectIds(['Default Plone Password Policy']):
        uf.plugins.deactivatePlugin(IValidationPlugin, policy)

    obj = DeadParrotPassword('test')
    uf._setObject(obj.getId(), obj)
    obj = uf[obj.getId()]
    activatePluginInterfaces(portal, obj.getId())

    # portal = getUtility(ISiteRoot)
    plugins = uf._getOb('plugins')
    validators = plugins.listPlugins(IValidationPlugin)
    assert validators
    commit()


classImplements(DeadParrotPassword, IValidationPlugin)


def get_security_settings():
    registry = getUtility(IRegistry)
    return registry.forInterface(ISecuritySchema, prefix="plone")


def set_mock_mailhost(portal):
    portal._original_MailHost = portal.MailHost
    portal.MailHost = mailhost = MockMailHost('MailHost')
    sm = getSiteManager(context=portal)
    sm.unregisterUtility(provided=IMailHost)
    sm.registerUtility(mailhost, provided=IMailHost)


def unset_mock_mailhost(portal):
    portal.MailHost = portal._original_MailHost
    sm = getSiteManager(context=portal)
    sm.unregisterUtility(provided=IMailHost)
    sm.registerUtility(aq_base(portal._original_MailHost), provided=IMailHost)
