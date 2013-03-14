import logging

from ZODB.POSException import ConflictError
from zExceptions import Forbidden
from AccessControl import getSecurityManager

from zope.component import getMultiAdapter, getUtility, getAdapter
from zope.interface import Invalid, Interface, implements
from zope.schema import getFieldNames
from zope.component.hooks import getSite
from zope.annotation.interfaces import IAnnotations

from z3c.form import form, button, field
from z3c.form.interfaces import IErrorViewSnippet, DISPLAY_MODE
from z3c.form.util import expandPrefix
from z3c.form.browser.checkbox import CheckBoxFieldWidget

from plone.autoform.interfaces import OMITTED_KEY, ORDER_KEY
from plone.autoform.form import AutoExtensibleForm
from plone.protect import CheckAuthenticator

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.interfaces import ISiteRoot

from Products.CMFPlone import PloneMessageFactory as _
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage

from .register import IRegisterSchema, IAddUserSchema
from ..userdataschema import IUserDataZ3CSchema

from ..schemaeditor import get_ttw_edited_fields
from plone.app.users.browser.z3cpersonalpreferences import UserDataPanelSchemaAdapter

class IZ3CRegisterSchema(IRegisterSchema, IUserDataZ3CSchema):
    """Collect all register fields under the same interface"""

from zope.component import provideAdapter


class BaseRegistrationForm(AutoExtensibleForm, form.Form):
    """Form to be used as base for Register and Add User forms."""

    label = u""
    description = u""
    formErrorsMessage = _('There were errors.')
    ignoreContext = True
    schema = IZ3CRegisterSchema

    # this attribute indicates if user was successfully registered
    _finishedRegister = False

    def __init__(self, *a, **kw):
        super(BaseRegistrationForm, self).__init__(*a, **kw)
        ttw_fields = get_ttw_edited_fields(
            register = True
        )
        self.extra_field_ids = ttw_fields.keys()
        self.fields += ttw_fields
        for f in ttw_fields:
            schema = ttw_fields[f].field.interface
            # import in time to avoid circular imports errors
            # make forms adapters know about ttw fields
            # we force self.schema as it can be a
            # generated supermodel with TTw fields
            provideAdapter(UserDataPanelSchemaAdapter, (Interface,), schema)

    def render(self):
        if self._finishedRegister:
            return self.context.unrestrictedTraverse('registered')()

        return super(BaseRegistrationForm, self).render()

    def updateFields(self):
        """Fields are dynamic in this form, to be able to handle
        different join styles.
        """
        portal_props = getToolByName(self.context, 'portal_properties')
        props = portal_props.site_properties
        use_email_as_login = props.getProperty('use_email_as_login')

        # Ensure all listed fields are in the schema
        registration_fields = [f for f in props.getProperty(
                'user_registration_fields', []) if f in self.schema]

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

        # Add extra fields after password_ctl
        current_index = registration_fields.index('password_ctl')
        for f in self.extra_field_ids:
            if f not in registration_fields:
                current_index += 1
                registration_fields.insert(current_index, f)

        # Add email_me at the end
        if not 'mail_me' in registration_fields:
            registration_fields.insert(current_index + 1, 'mail_me')

        # Order/filter schema by registration_fields
        self.schema.setTaggedValue(ORDER_KEY, [
          (registration_fields[i], 'after', registration_fields[i - 1] if i > 0 else '*')
          for i in range(len(registration_fields))
        ])
        self.schema.setTaggedValue(OMITTED_KEY, [
          (Interface, name, name not in registration_fields)
          for name in self.schema
        ])

        # Finally, let autoform process the schema and any FormExtenders do
        # their thing
        super(BaseRegistrationForm, self).updateFields()

        # update email field description according to set login policy
        if use_email_as_login:
            self.fields['email'].field.description = _(
                u'help_email_creation_for_login', default=u"Enter an email "
                "address. This will be your login name. We respect your "
                "privacy, and will not give the address away to any third "
                "parties or expose it anywhere.")
        else:
            self.fields['email'].field.description = _(u'help_email_creation',
                default=u"Enter an email address. This is necessary in case the"
                " password is lost. We respect your privacy, and will not give "
                "the address away to any third parties or expose it anywhere.")

        # Make sure some fields are really required; a previous call
        # might have changed the default.
        for name in ('password', 'password_ctl'):
            self.fields[name].field.required = True

        # Change the password description based on PAS Plugin
        # The user needs a list of instructions on what kind of password is
        # required.
        # We'll reuse password errors as instructions e.g. "Must contain a
        # letter and a number".
        # Assume PASPlugin errors are already translated
        if self.fields.get('password',None):
            registration = getToolByName(self.context, 'portal_registration')
            err_str = registration.testPasswordValidity('')
            if err_str:
                msgid = _(u'Enter your new password. ${errors}',
                    mapping=dict(errors=err_str))
                self.fields['password'].field.description = \
                    self.context.translate(msgid)


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

        # set member properties
        self.applyProperties(user_id, data)

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

    def applyProperties(self, userid, data):
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        mt = getToolByName(self.context, 'portal_membership')
        member = mt.getMemberById(userid)

        # cache adapters
        adapters = {}

        register_fields = getFieldNames(IRegisterSchema) + \
            getFieldNames(IAddUserSchema)
        for k, value in data.items():
            # skip fields that are handled exclusively on user registration and
            # are not part of personal information form
            if k in register_fields:
                continue

            # get schema adapter
            schema = self.fields[k].field.interface
            if schema in adapters:
                adapter = adapters[schema]
            else:
                adapters[schema] = adapter = getAdapter(portal, schema)
                adapter.context = member

            # finally set value
            setattr(adapter, k, value)

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
