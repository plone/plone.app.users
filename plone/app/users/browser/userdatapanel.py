from Acquisition import aq_inner
from zope.component import getUtility, provideAdapter
from zope.interface import Interface
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import set_own_login_name
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PlonePAS.tools.membership import default_portrait
from plone.app.users.browser.account import AccountPanelForm
from plone.app.users.browser.account import AccountPanelSchemaAdapter
from plone.namedfile.file import NamedBlobImage
from plone.app.layout.navigation.interfaces import INavigationRoot

from ..schema import IUserDataSchemaProvider


class UserDataPanelAdapter(AccountPanelSchemaAdapter):
    """One does not simply set portrait, email might be used to login with.
    """

    def __init__(self, *args, **kwargs):
        super(UserDataPanelAdapter, self).__init__(*args, **kwargs)
        self.schema = getUtility(IUserDataSchemaProvider).getSchema()
        # make forms adapters know about ttw fields
        # we force self.schema as it can be a
        # generated supermodel with TTw fields
        provideAdapter(self.__class__, (Interface,), self.schema)

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
        return NamedBlobImage(value.data, contentType=value.content_type,
                              filename=getattr(value, 'filename', None))

    def set_portrait(self, value):
        mt = getToolByName(self.context, 'portal_membership')
        if value is None:
            mt.deletePersonalPortrait(str(self.context.getId()))
        else:
            portrait_file = value.open()
            portrait_file.filename = value.filename
            mt.changeMemberPortrait(portrait_file, str(self.context.getId()))

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
    enableCSRFProtection = True

    def __init__(self, *args, **kwargs):
        super(UserDataPanel, self).__init__(*args, **kwargs)
        self.schema = getUtility(IUserDataSchemaProvider).getSchema()
        # as schema is a generated supermodel, just insert a relevant
        # adapter for it
        provideAdapter(UserDataPanelAdapter, (INavigationRoot,), self.schema)

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
