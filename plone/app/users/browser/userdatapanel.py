# -*- coding: utf-8 -*-
from zope.component import getUtility
from zope.interface import Interface
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.interfaces import ISecuritySchema
from Products.CMFPlone.utils import set_own_login_name
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.users.browser.account import AccountPanelForm
from plone.app.users.browser.account import AccountPanelSchemaAdapter
from plone.autoform.interfaces import OMITTED_KEY
from plone.registry.interfaces import IRegistry

from ..schema import IUserDataSchemaProvider, IUserDataSchema


class UserDataPanelAdapter(AccountPanelSchemaAdapter):
    """One does not simply set portrait, email might be used to login with.
    """

    def __init__(self, *args, **kwargs):
        super(UserDataPanelAdapter, self).__init__(*args, **kwargs)
        self.schema = getUtility(IUserDataSchemaProvider).getSchema()

    def get_email(self):
        return self._getProperty('email')

    def set_email(self, value):
        registry = getUtility(IRegistry)
        security_settings = registry.forInterface(
            ISecuritySchema, prefix="plone")
        if security_settings.use_email_as_login:
            mt = getToolByName(self.context, 'portal_membership')
            if self.context.getId() == mt.getAuthenticatedMember().getId():
                set_own_login_name(self.context, value)
            else:
                pas = getToolByName(self.context, 'acl_users')
                pas.updateLoginName(self.context.getId(), value)
        return self._setProperty('email', value)

    email = property(get_email, set_email)


class UserDataPanel(AccountPanelForm):

    form_name = _(u'User Data Form')
    enableCSRFProtection = True

    def __init__(self, *args, **kwargs):
        super(UserDataPanel, self).__init__(*args, **kwargs)
        self.schema = getUtility(IUserDataSchemaProvider).getSchema()

    def updateFields(self):
        """Fields are dynamic in this form
        """

        # Filter schema for user profile
        omitted = []
        default_fields = IUserDataSchema.names()
        for name in self.schema:
            # we always preserve default fields
            if name in default_fields:
                omit = False
            else:
                forms_selection = getattr(
                    self.schema[name], 'forms_selection', [])
                if u'In User Profile' in forms_selection:
                    omit = False
                else:
                    omit = True
            omitted.append((Interface, name, omit))
        self.schema.setTaggedValue(OMITTED_KEY, omitted)

        # Finally, let autoform process the schema and any FormExtenders do
        # their thing
        super(AccountPanelForm, self).updateFields()

    @property
    def description(self):
        userid = self.request.form.get('userid')
        mt = getToolByName(self.context, 'portal_membership')
        if userid and (userid != mt.getAuthenticatedMember().getId()):
            # editing someone else's profile
            return _(
                u'description_personal_information_form_otheruser',
                default='Change personal information for $name',
                mapping={'name': userid}
            )
        else:
            # editing my own profile
            return _(
                u'description_personal_information_form',
                default='Change your personal information'
            )


class UserDataConfiglet(UserDataPanel):
    """Control panel version of the userdata panel"""
    template = ViewPageTemplateFile('account-configlet.pt')
