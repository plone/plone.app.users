from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import set_own_login_name
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PlonePAS.tools.membership import default_portrait
from plone.app.users.browser.account import AccountPanelForm
from plone.app.users.browser.account import AccountPanelSchemaAdapter
from plone.app.users.schema import IUserDataSchema
from z3c.form.interfaces import IErrorViewSnippet
from zope.component import getMultiAdapter
from zope.interface import Invalid


class UserDataPanelAdapter(AccountPanelSchemaAdapter):
    """One does not simply set portrait, email might be used to login with.
    """
    schema = IUserDataSchema

    def get_portrait(self):
        """If user has default portrait, return none
        """
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        mt = getToolByName(self.context, 'portal_membership')
        value = mt.getPersonalPortrait(self.context.getId())
        if aq_inner(value) == aq_inner(getattr(portal,
                                               default_portrait,
                                               None)):
            return None
        return value

    def set_portrait(self, value):
        mt = getToolByName(self.context, 'portal_membership')
        if value is None:
            mt.deletePersonalPortrait(str(self.context.getId()))
        else:
            file = value.open()
            file.filename = value.filename
            mt.changeMemberPortrait(file, str(self.context.getId()))

    portrait = property(get_portrait, set_portrait)

    def get_email(self):
        return self._getProperty('email')

    def set_email(self, value):
        pp = getToolByName(self.context, 'portal_properties')
        if pp.site_properties.getProperty('use_email_as_login'):
            mt = getToolByName(self.context, 'portal_membership')
            if self.context.getId() == mt.getAuthenticatedMember().getId():
                set_own_login_name(self.context, value)
            else:
                pas = getToolByName(self.context, 'acl_users')
                pas.updateLoginName(self.context.getId(), value)
        return self._setProperty('email', value)

    email = property(get_email, set_email)


class UserDataPanel(AccountPanelForm):

    label = _(u'title_personal_information_form',
              default=u'Personal Information')
    form_name = _(u'User Data Form')
    schema = IUserDataSchema

    @property
    def description(self):
        userid = self.request.form.get('userid')
        mt = getToolByName(self.context, 'portal_membership')
        if userid and (userid != mt.getAuthenticatedMember().getId()):
            #editing someone else's profile
            return _(
                u'description_personal_information_form_otheruser',
                default='Change personal information for $name',
                mapping={'name': userid}
            )
        else:
            #editing my own profile
            return _(
                u'description_personal_information_form',
                default='Change your personal information'
            )


class UserDataConfiglet(UserDataPanel):
    """Control panel version of the userdata panel"""
    template = ViewPageTemplateFile('account-configlet.pt')
