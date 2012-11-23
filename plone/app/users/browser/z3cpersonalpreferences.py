from Acquisition import aq_inner
from AccessControl import Unauthorized

from zope.component import adapter, getMultiAdapter
from zope.event import notify
from zope.interface import implements, implementer, Invalid

from z3c.form import form, button
from z3c.form.interfaces import HIDDEN_MODE, IFieldWidget, IFormLayer, \
    IErrorViewSnippet
from z3c.form.widget import FieldWidget

from plone.autoform.form import AutoExtensibleForm
from plone.app.controlpanel.events import ConfigurationChangedEvent
from plone.formwidget.namedfile.widget import NamedImageWidget as BaseNamedImageWidget
from plone.namedfile.interfaces import INamedImageField
from plone.protect import CheckAuthenticator

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import SetOwnProperties

from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import set_own_login_name, safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from Products.PlonePAS.tools.membership import default_portrait as pas_default_portrait

from ZTUtils import make_query

from .account import IAccountPanelForm
from ..userdataschema import IUserDataZ3CSchema
from .personalpreferences import IPersonalPreferences, IPasswordSchema

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
        elif mt.isAnonymousUser():
            raise ValueError('Cannot change permissions for anonymous user')
        else:
            self.context = mt.getAuthenticatedMember()

    def _getProperty(self, name):
        value = self.context.getProperty(name, '')
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
            # In schema and no explicit handler, assume it's in the property sheet
            return self._getProperty(name)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name not in self.schema or hasattr(self.__class__, name):
            # Either not part of the schema or dealt with by an explicit
            # property
            return super(AccountPanelSchemaAdapter, self).__setattr__(name, value)
        return self._setProperty(name, value)


class AccountPanelForm(AutoExtensibleForm, form.Form):
    """A simple form to be used as a basis for account panel screens."""

    implements(IAccountPanelForm)
    schema = IAccountPanelForm
    template = ViewPageTemplateFile('z3c-account-view.pt')

    hidden_widgets = []
    successMessage = _("Changes saved.")
    noChangesMessage =  _("No changes made.")

    def makeQuery(self):
        if hasattr(self.request,'userid'):
            return '?' + make_query({'userid' : self.request.form.get('userid')})
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
                    err_view = getMultiAdapter((Invalid(err_str), self.request,
                        widget, widget.field, self, self.context),
                        IErrorViewSnippet)
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
        self.request.response.redirect('%s%s' % (self.request['ACTUAL_URL'],
            self.makeQuery()))

    def _on_save(self, data=None):
        pass

    def prepareObjectTabs(self, default_tab='view', sort_first=['folderContents']):
        context = self.context
        mt = getToolByName(context, 'portal_membership')
        tabs = []
        navigation_root_url = context.absolute_url()

        if mt.checkPermission(SetOwnProperties, context):
            tabs.append({
                'title': _('title_personal_information_form', u'Personal Information'),
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


class PersonalPreferencesPanelSchemaAdapter(AccountPanelSchemaAdapter):
    schema = IPersonalPreferences


class PersonalPreferencesPanel(AccountPanelForm):
    """ Implementation of personalize form that uses z3c.form """

    label = _(u"heading_my_preferences", default=u"Personal Preferences")
    form_name = _(u'legend_personal_details', u'Personal Details')

    @property
    def description(self):
        userid = self.request.form.get('userid')
        mt = getToolByName(self.context, 'portal_membership')
        if userid and (userid != mt.getAuthenticatedMember().getId()):
            #editing someone else's profile
            return _(u'description_preferences_form_otheruser', default='Personal settings for $name', mapping={'name': userid})
        else:
            #editing my own profile
            return _(u'description_my_preferences', default='Your personal settings.')

    schema = IPersonalPreferences

    def updateWidgets(self):
        """ Hide the visible_ids field based on portal_properties.
        """
        context = aq_inner(self.context)
        properties = getToolByName(context, 'portal_properties')
        siteProperties = properties.site_properties

        super(PersonalPreferencesPanel, self).updateWidgets()

        self.widgets['language'].noValueMessage = _(u"vocabulary-missing-single-value-for-edit", u"Language neutral (site default)")
        self.widgets['wysiwyg_editor'].noValueMessage = _(u"vocabulary-available-editor-novalue", u"Use site default")
        if not siteProperties.visible_ids:
            self.widgets['visible_ids'].mode = HIDDEN_MODE


class UserDataPanelSchemaAdapter(AccountPanelSchemaAdapter):
    """One does not simply set portrait, email might be used to login with
    """
    schema = IUserDataZ3CSchema

    def get_portrait(self):
        """If user has default portrait, return none
        """
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        mt = getToolByName(self.context, 'portal_membership')
        value = mt.getPersonalPortrait(self.context.getId())
        if aq_inner(value) == aq_inner(getattr(portal, pas_default_portrait, None)):
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
            set_own_login_name(self.context, value)
        return self._setProperty('email', value)

    email = property(get_email, set_email)


class UserDataPanel(AccountPanelForm):

    label = _(u'title_personal_information_form', default=u'Personal Information')
    form_name = _(u'User Data Form')
    schema = IUserDataZ3CSchema

    @property
    def description(self):
        userid = self.request.form.get('userid')
        mt = getToolByName(self.context, 'portal_membership')
        if userid and (userid != mt.getAuthenticatedMember().getId()):
            #editing someone else's profile
            return _(u'description_personal_information_form_otheruser', default='Change personal information for $name', mapping={'name': userid})
        else:
            #editing my own profile
            return _(u'description_personal_information_form', default='Change your personal information')


class NamedImageWidget(BaseNamedImageWidget):
    # Cheat around 2 bugs:
    # * You are not authenticated during traversal, so fetching
    #   the current user does not work.
    # * download_url won't append our querystring, so fetching
    #   another user's image does not work.
    @property
    def download_url(self):
        userid = self.request.form.get('userid')
        if not userid:
            mt = getToolByName(self.form.context, 'portal_membership')
            userid =  mt.getAuthenticatedMember().getId()

        # anonymous
        if not userid:
            return None

        url = super(NamedImageWidget, self).download_url
        if not url:
            return None

        return '%s?%s' % (url, make_query({'userid':userid}))

@implementer(IFieldWidget)
@adapter(INamedImageField, IFormLayer)
def NamedImageFieldWidget(field, request):
    return FieldWidget(field, NamedImageWidget(request))


class PersonalPreferencesConfiglet(PersonalPreferencesPanel):
    """Control panel version of the personal preferences panel"""
    template = ViewPageTemplateFile('z3c-account-configlet.pt')


class UserDataConfiglet(UserDataPanel):
    """Control panel version of the userdata panel"""
    template = ViewPageTemplateFile('z3c-account-configlet.pt')

class PasswordAccountPanel(AccountPanelForm):
    """ Implementation of password reset form that uses z3c.form"""
    label = _(u'listingheader_reset_password', default=u'Reset Password')
    description = _(u"Change Password")
    form_name = _(u'legend_password_details', default=u'Password Details')
    schema = IPasswordSchema

    def updateFields(self):
        super(PasswordAccountPanel, self).updateFields()
        
        # Change the password description based on PAS Plugin
        # The user needs a list of instructions on what kind of password is
        # required.
        # We'll reuse password errors as instructions e.g. "Must contain a
        # letter and a number".
        # Assume PASPlugin errors are already translated
        registration = getToolByName(self.context, 'portal_registration')
        err_str = registration.testPasswordValidity('')
        if err_str:
            self.fields['new_password'].field.description = \
                _(u'Enter your new password. ') + err_str

    def validate_password(self, errors, data):
        context = aq_inner(self.context)
        registration = getToolByName(context, 'portal_registration')
        membertool = getToolByName(context, 'portal_membership')

        # check if password is correct
        current_password = data.get('current_password')
        if current_password:
            current_password = current_password.encode('ascii', 'ignore')

            if not membertool.testCurrentPassword(current_password):
                # add error to current_password widget
                err_str = _(u"Incorrect value for current password")
                widget = self.widgets['current_password']
                err_view = getMultiAdapter((Invalid(err_str), self.request,
                    widget, widget.field, self, self.context),
                    IErrorViewSnippet)
                err_view.update()
                widget.error = err_view
                self.widgets.errors += (err_view,)
                errors += (err_view,)

        # check if passwords are same and valid according to plugin
        new_password = data.get('new_password')
        new_password_ctl = data.get('new_password_ctl')
        if new_password and new_password_ctl:
            failMessage = registration.testPasswordValidity(new_password,
                                                            new_password_ctl)

            if failMessage:
                # add error to new_password widget
                widget = self.widgets['new_password']
                err_view = getMultiAdapter((Invalid(failMessage), self.request,
                    widget, widget.field, self, self.context),
                    IErrorViewSnippet)
                err_view.update()
                widget.error = err_view
                self.widgets.errors += (err_view,)
                errors += (err_view,)

                # add error to new_password_ctl widget
                widget = self.widgets['new_password_ctl']
                err_view = getMultiAdapter((Invalid(failMessage), self.request,
                    widget, widget.field, self, self.context),
                    IErrorViewSnippet)
                err_view.update()
                widget.error = err_view
                self.widgets.errors += (err_view,)
                errors += (err_view,)

        return errors

    @button.buttonAndHandler(_(u'label_change_password',
        default=u'Change Password'), name='reset_passwd')
    def action_reset_passwd(self, action):
        data, errors = self.extractData()

        # extra password validation
        errors = self.validate_password(errors, data)

        if errors:
            IStatusMessage(self.request).addStatusMessage(
                self.formErrorsMessage, type='error')
            return

        membertool = getToolByName(self.context, 'portal_membership')

        password = data['new_password']

        try:
            membertool.setPassword(password, None, REQUEST=self.request)
        except AttributeError:
            failMessage = _(u'While changing your password an AttributeError '
                            u'occurred. This is usually caused by your user '
                            u'being defined outside the portal.')

            IStatusMessage(self.request).addStatusMessage(_(failMessage),
                                                          type="error")
            return

        IStatusMessage(self.request).addStatusMessage(_("Password changed"),
                                                          type="info")

    # hide inherited Save and Cancel buttons
    @button.buttonAndHandler(_(u'Save'), condition=lambda form:False)
    def handleSave(self, action):
        pass

    @button.buttonAndHandler(_(u'Cancel'), condition=lambda form:False)
    def cancel(self, action):
        pass
