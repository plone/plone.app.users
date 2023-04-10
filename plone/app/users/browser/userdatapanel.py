from AccessControl.SecurityManagement import getSecurityManager
from plone.app.users.browser.account import AccountPanelForm
from plone.app.users.browser.account import AccountPanelSchemaAdapter
from plone.app.users.browser.account import getSchema
from plone.app.users.schema import IUserDataSchema
from plone.base import PloneMessageFactory as _
from plone.base.interfaces import ISecuritySchema
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import get_portal
from Products.CMFPlone.utils import set_own_login_name
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zExceptions import NotFound
from zope.component import getUtility


try:
    from html import escape
except ImportError:
    from cgi import escape


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


class UserDataPanel(AccountPanelForm):
    form_name = _("User Data Form")
    enableCSRFProtection = True

    @property
    def schema(self):
        schema = getUserDataSchema()
        return schema

    @property
    def description(self):
        userid = self.request.form.get("userid")
        mt = getToolByName(self.context, "portal_membership")
        if userid and (userid != mt.getAuthenticatedMember().getId()):
            # editing someone else's profile
            return _(
                "description_personal_information_form_otheruser",
                default="Change personal information for $name",
                mapping={"name": escape(userid)},
            )
        else:
            # editing my own profile
            return _(
                "description_personal_information_form",
                default="Change your personal information",
            )

    def __call__(self):
        userid = self.request.form.get("userid")
        if userid:
            mt = getToolByName(self.context, "portal_membership")
            if mt.getMemberById(userid) is None:
                raise NotFound("User does not exist.")
        self.request.set("disable_border", 1)
        return super().__call__()


def getUserDataSchema():
    portal = get_portal()
    form_name = "In User Profile"
    if getSecurityManager().checkPermission("Manage portal", portal):
        form_name = None
    schema = getSchema(IUserDataSchema, UserDataPanelAdapter, form_name=form_name)
    return schema


class UserDataConfiglet(UserDataPanel):
    """Control panel version of the userdata panel"""

    template = ViewPageTemplateFile("account-configlet.pt")
    tab = "userdata"
