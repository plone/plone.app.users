from Acquisition import aq_inner
from zope.interface import implements
from ZTUtils import make_query
from plone.app.controlpanel.events import ConfigurationChangedEvent
from plone.protect import CheckAuthenticator
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.users.browser.interfaces import IAccountPanelForm
from z3c.form import form, button
from plone.autoform.form import AutoExtensibleForm
from Products.CMFPlone.utils import safe_unicode
from Products.CMFCore.permissions import SetOwnProperties
from zope.event import notify
from AccessControl import Unauthorized
from zope.component import getMultiAdapter
from zope.interface import Invalid
from z3c.form.interfaces import IErrorViewSnippet


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
        if value is None:
            value = ''
        return self.context.setMemberProperties({name: value})

    def __getattr__(self, name):
        if name in self.schema:
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
        return self._setProperty(name, value)


class AccountPanelForm(AutoExtensibleForm, form.Form):
    """A simple form to be used as a basis for account panel screens."""

    implements(IAccountPanelForm)
    schema = IAccountPanelForm
    template = ViewPageTemplateFile('account-panel.pt')

    hidden_widgets = []
    successMessage = _("Changes saved.")
    noChangesMessage = _("No changes made.")

    def makeQuery(self):
        if hasattr(self.request, 'userid'):
            return '?' + make_query({
                'userid': self.request.form.get('userid')
            })
        return ''

    def action(self):
        return self.request.getURL() + self.makeQuery()

    def validate_email(self, errors, data):
        context = aq_inner(self.context)
        error_keys = [error.field.getName() for error in errors]

        if 'email' not in error_keys:
            reg_tool = getToolByName(context, 'portal_registration')
            props = getToolByName(context, 'portal_properties')
            if props.site_properties.getProperty('use_email_as_login'):
                err_str = ''
                try:
                    id_allowed = reg_tool.isMemberIdAllowed(data['email'])
                except Unauthorized:
                    err_str = _('message_email_cannot_change',
                                default=(u"Sorry, you are not allowed to "
                                         u"change your email address."))
                else:
                    if not id_allowed:
                        # Keeping your email the same (which happens when you
                        # change something else on the personalize form) or
                        # changing it back to your login name, is fine.
                        membership = getToolByName(context,
                                                   'portal_membership')
                        if self.request.get('userid'):
                            member = membership.getMemberById(
                                self.request.get('userid'))
                        else:
                            member = membership.getAuthenticatedMember()
                        if data['email'] not in (member.getId(),
                                                 member.getUserName()):
                            err_str = _(
                                'message_email_in_use',
                                default=(
                                    u"The email address you selected is "
                                    u"already in use or is not valid as login "
                                    u"name. Please choose another."))

                if err_str:
                    widget = self.widgets['email']
                    err_view = getMultiAdapter((
                        Invalid(err_str),
                        self.request,
                        widget,
                        widget.field,
                        self, self.context
                    ), IErrorViewSnippet)
                    err_view.update()
                    widget.error = err_view
                    self.widgets.errors += (err_view,)
                    errors += (err_view,)

        return errors

    @button.buttonAndHandler(_(u'Save'))
    def handleSave(self, action):
        CheckAuthenticator(self.request)

        data, errors = self.extractData()

        # extra validation for email
        errors = self.validate_email(errors, data)

        if errors:
            IStatusMessage(self.request).addStatusMessage(
                self.formErrorsMessage, type='error')
            return

        if self.applyChanges(data):
            IStatusMessage(self.request).addStatusMessage(
                self.successMessage, type='info')
            notify(ConfigurationChangedEvent(self, data))
            self._on_save(data)
        else:
            IStatusMessage(self.request).addStatusMessage(
                self.noChangesMessage, type='info')

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

        if mt.checkPermission(SetOwnProperties, context):
            tabs.append({
                'title': _('title_personal_information_form',
                           u'Personal Information'),
                'url': navigation_root_url + '/@@personal-information',
                'selected': (self.__name__ == 'personal-information'),
                'id': 'user_data-personal-information',
            })
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
