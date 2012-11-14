import logging

from Acquisition import aq_inner
from ZODB.POSException import ConflictError
from zExceptions import Forbidden
from AccessControl import getSecurityManager

from zope.component import adapter, getMultiAdapter, getUtility, getAdapter
from zope.event import notify
from zope.interface import implements, implementer, Invalid
from zope.schema import getFieldNamesInOrder

from z3c.form import form, button, field
from z3c.form.interfaces import HIDDEN_MODE, IFieldWidget, IFormLayer, \
    IErrorViewSnippet, DISPLAY_MODE
from z3c.form.widget import FieldWidget
from z3c.form.util import expandPrefix
from z3c.form.browser.checkbox import CheckBoxFieldWidget

from plone.autoform.form import AutoExtensibleForm
from plone.app.controlpanel.events import ConfigurationChangedEvent
from plone.formwidget.namedfile.widget import NamedImageWidget as BaseNamedImageWidget
from plone.namedfile.interfaces import INamedImageField
from plone.protect import CheckAuthenticator

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import SetOwnProperties, ManagePortal
from Products.CMFCore.interfaces import ISiteRoot

from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import set_own_login_name, safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from Products.PlonePAS.tools.membership import default_portrait as pas_default_portrait

from ZTUtils import make_query

from .account import IAccountPanelForm
from ..userdataschema import IUserDataZ3CSchema, IUserDataSchemaProvider
from .personalpreferences import IPersonalPreferences, IPasswordSchema
from .register import IRegisterSchema, IAddUserSchema

#TODO: CSRF
#TODO: make register and add-user forms work in thickboxes
#TODO: make 'registered' template login button work

class AccountPanelForm(AutoExtensibleForm, form.Form):
    """A simple form to be used as a basis for account panel screens."""

    implements(IAccountPanelForm)
    schema = IAccountPanelForm
    template = ViewPageTemplateFile('z3c-account-view.pt')

    hidden_widgets = []
    successMessage = _("Changes saved.")
    noChangesMessage =  _("No changes made.")

    def getContent(self):
        mt = getToolByName(self.context, 'portal_membership')
        userid = self.request.form.get('userid')
        if (userid and mt.checkPermission('Plone Site Setup: Users and Groups',
                                           self.context)):
            member = mt.getMemberById(userid)
        else:
            member = mt.getAuthenticatedMember()
            if mt.isAnonymousUser():
                return {}

        data = {}
        _marker = object()
        # For each prefix-less version of the fieldname...
        for k in (f.field.__name__ for f in self.fields.values()):
            if k == 'portrait':
                portal = getToolByName(self, 'portal_url').getPortalObject()
                value = mt.getPersonalPortrait(member.getId())
                if aq_inner(value) == aq_inner(getattr(portal,pas_default_portrait, None)):
                    value = None
                data[k] = value
                continue

            value = member.getProperty(k, _marker)
            data[k] = None if value is _marker else safe_unicode(value)
        return data

    def applyChanges(self, data):
        mt = getToolByName(self.context, 'portal_membership')
        site_props = getToolByName(self.context, 'portal_properties').site_properties
        userid = self.request.form.get('userid')
        if (userid and mt.checkPermission('Plone Site Setup: Users and Groups',
                                           self.context)):
            member = mt.getMemberById(userid)
        else:
            member = mt.getAuthenticatedMember()

        # Remove everything that hasn't changed.
        old_data = self.getContent()
        new_data = dict((k.split('.')[-1], data[k]) for k in data.keys())
        for k in new_data.keys():
            if k == 'portrait' and self.widgets[k].action() == 'nochange':
                # action is 'nochange' for new uploads, don't delete them.
                if not(old_data is None or new_data is not None):
                    del new_data[k]
                continue
            if new_data[k] == old_data[k] or (old_data[k] == u'' and new_data[k] is None):
                del new_data[k]
        if len(new_data) == 0:
            # Nothing has changed, stop here
            return False

        for k, value in new_data.items():
            if k == 'portrait':
                if value is None:
                    mt.deletePersonalPortrait(str(member.getId()))
                else:
                    file = value.open()
                    file.filename = value.filename
                    mt.changeMemberPortrait(file, str(member.getId()))
                del new_data[k]
                continue
            if k in ['wysiwyg_editor','language','fullname','email','home_page'
                    ,'description','location'] and value is None:
                new_data[k] = ''

        if site_props.getProperty('use_email_as_login') and 'email' in new_data:
            set_own_login_name(self.context, new_data['email'])

        member.setMemberProperties(new_data)
        return True # We updated something

    def makeQuery(self):
        if hasattr(self.request,'userid'):
            return '?' + make_query({'userid' : self.request.form.get('userid')})
        return ''

    def action(self):
        return self.request.getURL() + self.makeQuery()

    @button.buttonAndHandler(_(u'Save'))
    def handleSave(self, action):
        data, errors = self.extractData()
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
        if not(userid):
            mt = getToolByName(self.form.context, 'portal_membership')
            userid =  mt.getAuthenticatedMember().getId()
        return super(NamedImageWidget, self).download_url + '?' + make_query({'userid':userid})

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

            # TODO: remove this check after this ticket is closed:
            #       https://dev.plone.org/ticket/13325
            if not failMessage and new_password != new_password_ctl:
                failMessage = _(u'Your password and confirmation did not match.'
                    ' Please try again.')

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

class BaseRegistrationForm(AutoExtensibleForm, form.Form):
    """Form to be used as base for Register and Add User forms."""

    label = u""
    description = u""
    formErrorsMessage = _('There were errors.')
    ignoreContext = True
    schema = IRegisterSchema

    # this attribute indicates if user was successfully registered
    _finishedRegister = False

    def render(self):
        if self._finishedRegister:
            return self.context.unrestrictedTraverse('registered')()
        return super(BaseRegistrationForm, self).render()

    def updateFields(self):
        """Fields are dynamic in this form, to be able to handle
        different join styles.

        Note: we still support extending registration form with
        IUserDataSchemaProvider utility. Now, when registration form is
        extensible, it's possible to extend it with IFormExtender adapter from
        plone.z3cform package. So in the future we may get rid of
        IUserDataSchemaProvider approach.
        """
        super(BaseRegistrationForm, self).updateFields()

        portal_props = getToolByName(self.context, 'portal_properties')
        props = portal_props.site_properties
        use_email_as_login = props.getProperty('use_email_as_login')
        registration_fields = list(props.getProperty(
                'user_registration_fields', []))

        # Check on required join fields
        if not 'username' in registration_fields and not use_email_as_login:
            registration_fields.insert(0, 'username')

        if 'username' in registration_fields and use_email_as_login:
            registration_fields.remove('username')

        if not 'email' in registration_fields:
            # Perhaps only when use_email_as_login is true, but also
            # for some other cases; the email field has always been
            # required.
            registration_fields.append('email')

        if not 'password' in registration_fields:
            if 'username' in registration_fields:
                base = registration_fields.index('username')
            else:
                base = registration_fields.index('email')
            registration_fields.insert(base + 1, 'password')

        # Add password_ctl after password
        if not 'password_ctl' in registration_fields:
            registration_fields.insert(
                registration_fields.index('password') + 1, 'password_ctl')

        # Add email_me after password_ctl
        if not 'mail_me' in registration_fields:
            registration_fields.insert(
                registration_fields.index('password_ctl') + 1, 'mail_me')

        # We need fields from both schemata here.
        util = getUtility(IUserDataSchemaProvider)
        schema = util.getSchema()

        all_fields = field.Fields(schema) + self.fields

        # update email field description according to set login policy
        if use_email_as_login:
            all_fields['email'].field.description = _(
                u'help_email_creation_for_login', default=u"Enter an email "
                "address. This will be your login name. We respect your "
                "privacy, and will not give the address away to any third "
                "parties or expose it anywhere.")
        else:
            all_fields['email'].field.description = _(u'help_email_creation',
                default=u"Enter an email address. This is necessary in case the"
                " password is lost. We respect your privacy, and will not give "
                "the address away to any third parties or expose it anywhere.")

        # Make sure some fields are really required; a previous call
        # might have changed the default.
        for name in ('password', 'password_ctl'):
            all_fields[name].field.required = True

        # Change the password description based on PAS Plugin
        # The user needs a list of instructions on what kind of password is
        # required.
        # We'll reuse password errors as instructions e.g. "Must contain a
        # letter and a number".
        # Assume PASPlugin errors are already translated
        if all_fields.get('password',None):
            registration = getToolByName(self.context, 'portal_registration')
            err_str = registration.testPasswordValidity('')
            if err_str:
                msgid = _(u'Enter your new password. ${errors}',
                    mapping=dict(errors=err_str))
                all_fields['password'].field.description = \
                    self.context.translate(msgid)

        self.fields = field.Fields(*[all_fields[id]
            for id in registration_fields])

    # Actions validators
    def validate_registration(self, errors, data):
        """
        specific business logic for this join form
        note: all this logic was taken directly from the old
        validate_registration.py script in
        Products/CMFPlone/skins/plone_login/join_form_validate.vpy
        """

        # CSRF protection
        CheckAuthenticator(self.request)

        registration = getToolByName(self.context, 'portal_registration')

        error_keys = [error.field.getName() for error in errors]

        form_field_names = [f for f in self.fields]

        portal = getUtility(ISiteRoot)
        portal_props = getToolByName(self.context, 'portal_properties')
        props = portal_props.site_properties
        use_email_as_login = props.getProperty('use_email_as_login')

        # passwords should match
        if 'password' in form_field_names:
            assert('password_ctl' in form_field_names)
            # Skip this check if password fields already have an error
            if not ('password' in error_keys or \
                    'password_ctl' in error_keys):
                password = data.get('password')
                password_ctl = data.get('password_ctl')
                if password != password_ctl:
                    err_str = _(u'Passwords do not match.')

                    # set error on password field
                    widget = self.widgets['password']
                    err_view = getMultiAdapter((Invalid(err_str), self.request,
                        widget, widget.field, self, self.context),
                        IErrorViewSnippet)
                    err_view.update()
                    widget.error = err_view
                    self.widgets.errors += (err_view,)
                    errors += (err_view,)

                    # set error on password_ctl field
                    widget = self.widgets['password_ctl']
                    err_view = getMultiAdapter((Invalid(err_str), self.request,
                        widget, widget.field, self, self.context),
                        IErrorViewSnippet)
                    err_view.update()
                    widget.error = err_view
                    self.widgets.errors += (err_view,)
                    errors += (err_view,)

        # Password field checked against RegistrationTool
        if 'password' in form_field_names:
            # Skip this check if password fields already have an error
            if not 'password' in error_keys:
                password = data.get('password')
                if password:
                    # Use PAS to test validity
                    err_str = registration.testPasswordValidity(password)
                    if err_str:
                        widget = self.widgets['password']
                        err_view = getMultiAdapter((Invalid(err_str),
                            self.request, widget, widget.field, self,
                            self.context), IErrorViewSnippet)
                        err_view.update()
                        widget.error = err_view
                        self.widgets.errors += (err_view,)
                        errors += (err_view,)

        username = data.get('username', '')
        email = data.get('email', '')
        if use_email_as_login:
            username_field = 'email'
            username = email
        else:
            username_field = 'username'

        # check if username is valid
        # Skip this check if username was already in error list
        if not username_field in error_keys:
            if username == portal.getId():
                err_str = _(u"This username is reserved. Please choose a "
                            "different name.")
                widget = self.widgets[username_field]
                err_view = getMultiAdapter((Invalid(err_str),
                    self.request, widget, widget.field, self,
                    self.context), IErrorViewSnippet)
                err_view.update()
                widget.error = err_view
                self.widgets.errors += (err_view,)
                errors += (err_view,)

        # check if username is allowed
        if not username_field in error_keys:
            if not registration.isMemberIdAllowed(username):
                err_str = _(u"The login name you selected is already in use "
                            "or is not valid. Please choose another.")
                widget = self.widgets[username_field]
                err_view = getMultiAdapter((Invalid(err_str),
                    self.request, widget, widget.field, self,
                    self.context), IErrorViewSnippet)
                err_view.update()
                widget.error = err_view
                self.widgets.errors += (err_view,)
                errors += (err_view,)

        # Skip this check if email was already in error list
        if not 'email' in error_keys:
            if 'email' in form_field_names:
                if not registration.isValidEmail(email):
                    err_str = _(u'You must enter a valid email address.')
                    widget = self.widgets['email']
                    err_view = getMultiAdapter((Invalid(err_str),
                        self.request, widget, widget.field, self,
                        self.context), IErrorViewSnippet)
                    err_view.update()
                    widget.error = err_view
                    self.widgets.errors += (err_view,)
                    errors += (err_view,)

        if 'password' in form_field_names and not 'password' in error_keys:
            # Admin can either set a password or mail the user (or both).
            if not (data.get('password') or data.get('mail_me')):
                err_str = _('msg_no_password_no_mail_me',
                            default=u"You must set a password or choose to "
                            "send an email.")

                # set error on password field
                widget = self.widgets['password']
                err_view = getMultiAdapter((Invalid(err_str),
                    self.request, widget, widget.field, self,
                    self.context), IErrorViewSnippet)
                err_view.update()
                widget.error = err_view
                self.widgets.errors += (err_view,)
                errors += (err_view,)

                # set error on mail_me field
                widget = self.widgets['mail_me']
                err_view = getMultiAdapter((Invalid(err_str),
                    self.request, widget, widget.field, self,
                    self.context), IErrorViewSnippet)
                err_view.update()
                widget.error = err_view
                self.widgets.errors += (err_view,)
                errors += (err_view,)

        return errors

    @button.buttonAndHandler(_(u'label_register', default=u'Register'),
        name='register')
    def action_join(self, action):
        data, errors = self.extractData()

        # extra password validation
        errors = self.validate_registration(errors, data)

        if errors:
            IStatusMessage(self.request).addStatusMessage(
                self.formErrorsMessage, type='error')
            return

        self.handle_join_success(data)

        self._finishedRegister = True

        # XXX Return somewhere else, depending on what
        # handle_join_success returns?
        came_from = self.request.form.get('came_from')
        if came_from:
            utool = getToolByName(self.context, 'portal_url')
            if utool.isURLInPortal(came_from):
                self.request.response.redirect(came_from)
                return ''

    def handle_join_success(self, data):
        # portal should be acquisition wrapped, this is needed for the schema
        # adapter below
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        registration = getToolByName(self.context, 'portal_registration')
        portal_props = getToolByName(self.context, 'portal_properties')
        mt = getToolByName(self.context, 'portal_membership')
        props = portal_props.site_properties
        use_email_as_login = props.getProperty('use_email_as_login')

        if use_email_as_login:
            # The username field is not shown as the email is going to
            # be the username, but the field *is* needed further down
            # the line.
            data['username'] = data['email']
            # Set username in the form; at least needed for logging in
            # immediately when password reset is bypassed.
            key = expandPrefix(self.prefix) + \
                expandPrefix(self.widgets.prefix) + 'username'
            self.request.form[key] = data['email']

        user_id = data['username']
        password = data.get('password') or registration.generatePassword()
        if isinstance(password, unicode):
            password = password.encode('utf8')

        try:
            registration.addMember(user_id, password, REQUEST=self.request)
        except (AttributeError, ValueError), err:
            logging.exception(err)
            IStatusMessage(self.request).addStatusMessage(err, type="error")
            return

        # set additional properties using the user schema adapter
        schema = getUtility(IUserDataSchemaProvider).getSchema()

        adapter = getAdapter(portal, schema)
        adapter.context = mt.getMemberById(user_id)

        for name in getFieldNamesInOrder(schema):
            if name in data:
                setattr(adapter, name, data[name])

        if data.get('mail_me') or (portal.validate_email and
                                   not data.get('password')):
            # We want to validate the email address (users cannot
            # select their own passwords on the register form) or the
            # admin has explicitly requested to send an email on the
            # 'add new user' form.
            try:
                # When all goes well, this call actually returns the
                # rendered mail_password_response template.  As a side
                # effect, this removes any status messages added to
                # the request so far, as they are already shown in
                # this template.
                response = registration.registeredNotify(user_id)
                return response
            except ConflictError:
                # Let Zope handle this exception.
                raise
            except Exception:
                ctrlOverview = getMultiAdapter((portal, self.request),
                                               name='overview-controlpanel')
                mail_settings_correct = not ctrlOverview.mailhost_warning()
                if mail_settings_correct:
                    # The email settings are correct, so the most
                    # likely cause of an error is a wrong email
                    # address.  We remove the account:
                    # Remove the account:
                    self.context.acl_users.userFolderDelUsers(
                        [user_id], REQUEST=self.request)
                    IStatusMessage(self.request).addStatusMessage(
                        _(u'status_fatal_password_mail',
                          default=u"Failed to create your account: we were "
                          "unable to send instructions for setting a password "
                          "to your email address: ${address}",
                          mapping={u'address': data.get('email', '')}),
                        type='error')
                    return
                else:
                    # This should only happen when an admin registers
                    # a user.  The admin should have seen a warning
                    # already, but we warn again for clarity.
                    IStatusMessage(self.request).addStatusMessage(
                        _(u'status_nonfatal_password_mail',
                          default=u"This account has been created, but we "
                          "were unable to send instructions for setting a "
                          "password to this email address: ${address}",
                          mapping={u'address': data.get('email', '')}),
                        type='warning')
                    return

        return

class RegistrationForm(BaseRegistrationForm):
    """ Dynamically get fields from user data, through admin
        config settings.
    """
    label = _(u'heading_registration_form', default=u'Registration form')
    description = u""
    template = ViewPageTemplateFile('z3c-register-form.pt')

    @property
    def showForm(self):
        """The form should not be displayed to the user if the system is
           incapable of sending emails and email validation is switched on
           (users are not allowed to select their own passwords).
        """
        portal = getUtility(ISiteRoot)
        ctrlOverview = getMultiAdapter((portal, self.request),
                                       name='overview-controlpanel')

        # hide form iff mailhost_warning == True and validate_email == True
        return not (ctrlOverview.mailhost_warning() and
                    portal.getProperty('validate_email', True))

    def updateFields(self):
        if not self.showForm:
            # We do not want to spend time calculating fields that
            # will never get displayed.
            return

        super(RegistrationForm, self).updateFields()
        defaultFields = field.Fields(self.fields)

        # Can the user actually set his/her own password?
        portal = getUtility(ISiteRoot)
        if portal.getProperty('validate_email', True):
            # No? Remove the password fields.
            defaultFields = defaultFields.omit('password', 'password_ctl')
        else:
            # The portal is not interested in validating emails, and
            # the user is not interested in getting an email with a
            # link to set his password if he can set this password in
            # the current form already.
            defaultFields = defaultFields.omit('mail_me')

        self.fields = defaultFields

    def updateWidgets(self):
        if not self.showForm:
            # We do not want to spend time calculating widgets that
            # will never get displayed.
            return

        super(RegistrationForm, self).updateWidgets()
        portal = getUtility(ISiteRoot)
        if portal.getProperty('validate_email', True):
            # Show a message indicating that a password reset link
            # will be mailed to the user.
            widget = self.widgets['mail_me']
            widget.mode = DISPLAY_MODE
            widget.value = ['selected']
            widget.label = _(u'label_password_change_mail',
                default=u"A URL will be generated and e-mailed to you; "
                "follow the link to reach a page where you can change your "
                "password and complete the registration process.")
            widget.terms = None
            widget.updateTerms()

class AddUserForm(BaseRegistrationForm):

    label = _(u'heading_add_user_form', default=u'Add New User')
    description = u""
    template = ViewPageTemplateFile('z3c-newuser-form.pt')

    def updateFields(self):
        super(AddUserForm, self).updateFields()
        defaultFields = field.Fields(self.fields)

        # The mail_me field needs special handling depending on the
        # validate_email property and on the correctness of the mail
        # settings.
        portal = getUtility(ISiteRoot)
        ctrlOverview = getMultiAdapter((portal, self.request),
                                       name='overview-controlpanel')
        mail_settings_correct = not ctrlOverview.mailhost_warning()
        if mail_settings_correct:
            # Make the password fields optional: either specify a
            # password or mail the user (or both).  The validation
            # will check that at least one of the options is chosen.
            defaultFields['password'].field.required = False
            defaultFields['password_ctl'].field.required = False
            if portal.getProperty('validate_email', True):
                defaultFields['mail_me'].field.default = True
            else:
                defaultFields['mail_me'].field.default = False

        # Append the manager-focused fields
        allFields = defaultFields + field.Fields(IAddUserSchema)

        allFields['groups'].widgetFactory = CheckBoxFieldWidget

        self.fields = allFields

    def updateWidgets(self):
        super(AddUserForm, self).updateWidgets()

        # set display mode for mail_me field if no mailhost is configured
        portal = getUtility(ISiteRoot)
        ctrlOverview = getMultiAdapter((portal, self.request),
            name='overview-controlpanel')
        mail_settings_correct = not ctrlOverview.mailhost_warning()
        if not mail_settings_correct:
            widget = self.widgets['mail_me']
            widget.mode = DISPLAY_MODE
            widget.value = ['selected']
            widget.label = _(
                u'label_cant_mail_password_reset', default=u"Normally we would "
                "offer to send the user an email with instructions to set a "
                "password on completion of this form. But this site does not "
                "have a valid email setup. You can fix this in the Mail "
                "settings.")
            widget.terms = None
            widget.updateTerms()

    @button.buttonAndHandler(_(u'label_register', default=u'Register'),
        name='register')
    def action_join(self, action):
        data, errors = self.extractData()

        # extra password validation
        errors = self.validate_registration(errors, data)

        if errors:
            IStatusMessage(self.request).addStatusMessage(
                self.formErrorsMessage, type='error')
            return

        super(AddUserForm, self).handle_join_success(data)

        portal_groups = getToolByName(self.context, 'portal_groups')
        user_id = data['username']
        is_zope_manager = getSecurityManager().checkPermission(
            ManagePortal, self.context)

        try:
            # Add user to the selected group(s)
            if 'groups' in data.keys():
                for groupname in data['groups']:
                    group = portal_groups.getGroupById(groupname)
                    if 'Manager' in group.getRoles() and not is_zope_manager:
                        raise Forbidden
                    portal_groups.addPrincipalToGroup(user_id, groupname,
                                                      self.request)
        except (AttributeError, ValueError), err:
            IStatusMessage(self.request).addStatusMessage(err, type="error")
            return

        IStatusMessage(self.request).addStatusMessage(
            _(u"User added."), type='info')
        self.request.response.redirect(
            self.context.absolute_url() +
            '/@@usergroup-userprefs?searchstring=' + user_id)

        self._finishedRegister = True
