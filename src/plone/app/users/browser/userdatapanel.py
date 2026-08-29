from AccessControl.SecurityManagement import getSecurityManager
from plone.app.users.browser.account import AccountPanelSchemaAdapter
from plone.app.users.browser.account import getSchema
from plone.app.users.schema import IUserDataSchema
from plone.base.interfaces import ISecuritySchema
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import get_portal
from Products.CMFPlone.utils import set_own_login_name
from zope.component import getUtility

import zope.deferredimport

zope.deferredimport.initialize()

zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.account import UserDataPanel instead.",
    UserDataPanel="plone.app.layout.users.account:UserDataPanel",
)
zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.account import UserDataConfiglet instead.",
    UserDataConfiglet="plone.app.layout.users.account:UserDataConfiglet",
)


class UserDataPanelAdapter(AccountPanelSchemaAdapter):
    """One does not simply set portrait, email might be used to login with."""

    @property
    def schema(self):
        # prevent infinite recursion when accessing the schema via bypassing
        # __getattr__ of self
        try:
            return object.__getattribute__(self, "_schema")
        except AttributeError:
            object.__setattr__(self, "_schema", getUserDataSchema())
        return object.__getattribute__(self, "_schema")

    @schema.setter
    def schema(self, value):
        self._schema = value

    def get_email(self):
        return self._getProperty("email")

    def set_email(self, value):
        registry = getUtility(IRegistry)
        security_settings = registry.forInterface(ISecuritySchema, prefix="plone")
        if security_settings.use_email_as_login:
            mt = getToolByName(self.context, "portal_membership")
            if self.context.getId() == mt.getAuthenticatedMember().getId():
                set_own_login_name(self.context, value)
            else:
                pas = getToolByName(self.context, "acl_users")
                pas.updateLoginName(self.context.getId(), value)
        return self._setProperty("email", value)

    email = property(get_email, set_email)


def getUserDataSchema():
    portal = get_portal()
    form_name = "In User Profile"
    if getSecurityManager().checkPermission("Manage portal", portal):
        form_name = None
    schema = getSchema(IUserDataSchema, UserDataPanelAdapter, form_name=form_name)
    return schema
