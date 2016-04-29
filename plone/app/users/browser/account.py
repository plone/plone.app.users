# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.interfaces import ISecuritySchema
from Products.CMFPlone.utils import safe_unicode
from Products.PlonePAS.tools.membership import default_portrait
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from ZTUtils import make_query
from Products.CMFPlone.controlpanel.events import ConfigurationChangedEvent
from plone.app.users.browser.interfaces import IAccountPanelForm
from plone.app.users.utils import notifyWidgetActionExecutionError
from plone.autoform.form import AutoExtensibleForm
from plone.namedfile.file import NamedBlobImage
from plone.protect import CheckAuthenticator
from plone.registry.interfaces import IRegistry
from z3c.form import button
from z3c.form import form
from zope import schema
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.event import notify
from zope.interface import implements


MESSAGE_EMAIL_CANNOT_CHANGE = \
    _('message_email_cannot_change',
      default=(u"Sorry, you are not allowed to "
               u"change your email address."))

MESSAGE_EMAIL_IN_USE = \
    _('message_email_in_use',
      default=(u"The email address you selected is "
               u"already in use or is not valid as login "
               u"name. Please choose another."))


def isDefaultPortrait(value, portal):
    default_portrait_value = getattr(portal, default_portrait, None)
    return aq_inner(value) == aq_inner(default_portrait_value)


class AccountPanelSchemaAdapter(object):
    """Data manager that gets and sets any property mentioned
       in the schema to the property sheet
    """
    context = None
    schema = IAccountPanelForm

    def __init__(self, context):
        mt = getToolByName(context, 'portal_membership')
        userid = context.REQUEST.form.get('userid')
        if (userid and mt.checkPermission('Plone Site Setup: Users and Groups',
                                          context)):
            self.context = mt.getMemberById(userid)
        else:
            self.context = mt.getAuthenticatedMember()

    def _getProperty(self, name):
        value = self.context.getProperty(name, '')
        if value == '':
            value = None
        if value:
            # PlonePAS encodes all unicode coming from PropertySheets.
            return safe_unicode(value)
        return value

    def _setProperty(self, name, value):
        if type(value) is set:
            value = list(value)
        if value and isinstance(self.schema[name], schema.Choice):
            value = str(value)
        return self.context.setMemberProperties(
            {name: value}, force_empty=True
        )

    def __getattr__(self, name):
        if name in self.schema:
            if isinstance(self.schema[name], NamedBlobImage):
                # any image is the portrait
                return self.get_portrait()
            # In schema and no explicit handler, assume it's in the property
            # sheet
            return self._getProperty(name)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name not in self.schema or hasattr(self.__class__, name):
            # Either not part of the schema or dealt with by an explicit
            # property
            return super(AccountPanelSchemaAdapter, self).__setattr__(name,
                                                                      value)
        if isinstance(value, NamedBlobImage):
            # any image is stored as portrait
            return self.set_portrait(value)

        return self._setProperty(name, value)

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()

    def get_portrait(self):
        """If user has default portrait, return none"""
        mt = getToolByName(self.context, 'portal_membership')
        value = mt.getPersonalPortrait(self.context.getId())
        if isDefaultPortrait(value, self.portal):
            return None
        return NamedBlobImage(value.data, contentType=value.content_type,
                              filename=getattr(value, 'filename', None))

    def set_portrait(self, value):
        mt = getToolByName(self.context, 'portal_membership')
        member_id = self.context.getId()
        if value is None:
            previous = mt.getPersonalPortrait(member_id)
            if not isDefaultPortrait(previous, self.portal):
                mt.deletePersonalPortrait(str(member_id))
        else:
            portrait_file = value.open()
            portrait_file.filename = value.filename
            mt.changeMemberPortrait(portrait_file, str(self.context.getId()))

    portrait = property(get_portrait, set_portrait)


class AccountPanelForm(AutoExtensibleForm, form.Form):
    """A simple form to be used as a basis for account panel screens."""

    implements(IAccountPanelForm)
    schema = IAccountPanelForm
    template = ViewPageTemplateFile('account-panel.pt')
    enableCSRFProtection = True

    hidden_widgets = []
    successMessage = _("Changes saved.")
    noChangesMessage = _("No changes made.")

    @lazy_property
    def member(self):
        mtool = getToolByName(self.context, 'portal_membership')
        if self.request.get('userid'):
            return mtool.getMemberById(self.request.get('userid'))
        return mtool.getAuthenticatedMember()

    @property
    def label(self):
        return self.member.getProperty('fullname') or self.member.getUserName()

    def _differentEmail(self, email):
        """Check if the submitted form email address differs from the existing
        one.

        Keeping your email the same (which happens when you change something
        else on the personalize form) or changing it back to your login name,
        is fine.
        """
        membership = getToolByName(self.context, 'portal_membership')
        if self.request.get('userid'):
            member = membership.getMemberById(self.request.get('userid'))
        else:
            member = membership.getAuthenticatedMember()
        return email not in (member.getId(), member.getUserName())

    def makeQuery(self):
        if hasattr(self.request, 'userid'):
            return '?' + make_query({
                'userid': self.request.form.get('userid')
            })
        return ''

    def action(self):
        return self.request.getURL() + self.makeQuery()

    def validate_email(self, action, data):
        context = aq_inner(self.context)
        error_keys = [
            error.field.getName()
            for error
            in action.form.widgets.errors
        ]
        if 'email' not in error_keys:
            registration = getToolByName(context, 'portal_registration')
            registry = getUtility(IRegistry)
            security_settings = registry.forInterface(
                ISecuritySchema, prefix="plone")
            if security_settings.use_email_as_login:
                err_str = ''
                try:
                    id_allowed = registration.isMemberIdAllowed(data['email'])
                except Unauthorized:
                    err_str = MESSAGE_EMAIL_CANNOT_CHANGE
                else:
                    if not id_allowed:
                        # only allow if unchanged
                        if self._differentEmail(data['email']):
                            err_str = MESSAGE_EMAIL_IN_USE
                if err_str:
                    notifyWidgetActionExecutionError(action, 'email', err_str)

    @button.buttonAndHandler(_(u'Save'))
    def handleSave(self, action):
        CheckAuthenticator(self.request)
        data, errors = self.extractData()

        # Extra validation for email, when it is there.  email is not in the
        # data when you are at the personal-preferences page.
        if 'email' in data:
            self.validate_email(action, data)

        if action.form.widgets.errors:
            self.status = self.formErrorsMessage
            return
        if self.applyChanges(data):
            IStatusMessage(self.request).addStatusMessage(
                self.successMessage, type='info')
            notify(ConfigurationChangedEvent(self, data))
            self._on_save(data)
        else:
            IStatusMessage(self.request).addStatusMessage(
                self.noChangesMessage, type='info')
        self.request.response.redirect(self.action())

    def updateActions(self):
        super(AccountPanelForm, self).updateActions()
        if self.actions and 'save' in self.actions:
            self.actions['save'].addClass('context')

    @button.buttonAndHandler(_(u'Cancel'))
    def cancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_("Changes canceled."),
                                                      type="info")
        self.request.response.redirect(
            '%s%s' % (self.request['ACTUAL_URL'], self.makeQuery())
        )

    def _on_save(self, data=None):
        pass

    def prepareObjectTabs(self,
                          default_tab='view',
                          sort_first=['folderContents']):
        context = self.context
        mt = getToolByName(context, 'portal_membership')
        tabs = []
        navigation_root_url = context.absolute_url()

        def _check_allowed(context, request, name):
            """Check, if user has required permissions on view.
            """
            view = getMultiAdapter((context, request), name=name)
            allowed = True
            for perm in view.__ac_permissions__:
                allowed = allowed and mt.checkPermission(perm[0], context)
            return allowed

        if _check_allowed(context, self.request, 'personal-information'):
            tabs.append({
                'title': _('title_personal_information_form',
                           u'Personal Information'),
                'url': navigation_root_url + '/@@personal-information',
                'selected': (self.__name__ == 'personal-information'),
                'id': 'user_data-personal-information',
            })

        if _check_allowed(context, self.request, 'personal-preferences'):
            tabs.append({
                'title': _(u'Personal Preferences'),
                'url': navigation_root_url + '/@@personal-preferences',
                'selected': (self.__name__ == 'personal-preferences'),
                'id': 'user_data-personal-preferences',
            })

        member = mt.getAuthenticatedMember()
        if member.canPasswordSet():
            tabs.append({
                'title': _('label_password', u'Password'),
                'url': navigation_root_url + '/@@change-password',
                'selected': (self.__name__ == 'change-password'),
                'id': 'user_data-change-password',
            })
        return tabs
