# -*- coding: utf-8 -*-
from AccessControl import getSecurityManager
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.interfaces import ISecuritySchema
from Products.CMFPlone.utils import normalizeString
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from ZODB.POSException import ConflictError
from plone.autoform.form import AutoExtensibleForm
from plone.autoform.interfaces import OMITTED_KEY
from plone.protect import CheckAuthenticator
from plone.registry.interfaces import IRegistry
from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.interfaces import DISPLAY_MODE
from zExceptions import Forbidden
from zope.component import (
    getUtility,
    queryUtility,
    getAdapter,
    provideAdapter,
    getMultiAdapter)
from zope.component.hooks import getSite
from zope.schema import getFieldNames
import logging

from ..schema import (
    IRegisterSchema,
    IAddUserSchema,
    ICombinedRegisterSchema
)
from ..utils import (
    notifyWidgetActionExecutionError,
    uuid_userid_generator,
)
from .account import AccountPanelSchemaAdapter
from .schemaeditor import getFromBaseSchema

from plone.app.users.browser.interfaces import ILoginNameGenerator
from plone.app.users.browser.interfaces import IUserIdGenerator

# Number of retries for creating a user id like bob-jones-42:
RENAME_AFTER_CREATION_ATTEMPTS = 100


def getRegisterSchema():
    portal = getSite()
    schema = getattr(portal, '_v_register_schema', None)
    if schema is None:
        portal._v_register_schema = schema = getFromBaseSchema(
            ICombinedRegisterSchema,
            form_name=u'On Registration'
        )
        # as schema is a generated supermodel,
        # needed adapters can only be registered at run time
        provideAdapter(AccountPanelSchemaAdapter, (IPloneSiteRoot,), schema)
    return schema


class BaseRegistrationForm(AutoExtensibleForm, form.Form):
    """Form to be used as base for Register and Add User forms."""
    label = u""
    description = u""
    formErrorsMessage = _('There were errors.')
    ignoreContext = True
    enableCSRFProtection = True
    schema = ICombinedRegisterSchema

    # this attribute indicates if user was successfully registered
    _finishedRegister = False

    @property
    def schema(self):
        return getRegisterSchema()

    def _get_security_settings(self):
        """Return security settings from the registry."""
        registry = getUtility(IRegistry)
        return registry.forInterface(ISecuritySchema, prefix="plone")

    def render(self):
        if self._finishedRegister:
            return self.context.unrestrictedTraverse('registered')()

        return super(BaseRegistrationForm, self).render()

    def updateFields(self):
        """Fields are dynamic in this form, to be able to handle
        different join styles.
        """
        settings = self._get_security_settings()
        use_email_as_login = settings.use_email_as_login

        # Finally, let autoform process the schema and any FormExtenders do
        # their thing
        super(BaseRegistrationForm, self).updateFields()

        if use_email_as_login:
            self.fields['email'].field.description = _(
                u'help_email_creation_for_login', default=u"Enter an email "
                "address. This will be your login name. We respect your "
                "privacy, and will not give the address away to any third "
                "parties or expose it anywhere.")
            del self.fields['username']
        else:
            self.fields['email'].field.description = _(
                u'help_email_creation',
                default=u"Enter an email address. This is necessary in case "
                        u"the password is lost. We respect your privacy, and "
                        u"will not give the address away to any third parties "
                        u"or expose it anywhere."
            )

        # Change the password description based on PAS Plugin The user needs a
        # list of instructions on what kind of password is required.  We'll
        # reuse password errors as instructions e.g. "Must contain a letter and
        # a number".  Assume PASPlugin errors are already translated
        if self.fields.get('password', None):
            registration = getToolByName(self.context, 'portal_registration')
            err_str = registration.testPasswordValidity('')
            if err_str:
                msg = _(
                    u'help_password_creation_with_errors',
                    default=u'Enter your new password. ${errors}',
                    mapping=dict(errors=err_str)
                )
                self.fields['password'].field.description = msg

    def generate_user_id(self, data):
        """Generate a user id from data.

        We try a few options for coming up with a good user id:

        1. We query a utility, so integrators can register a hook to
           generate a user id using their own logic.

        2. If use_uuid_as_userid is set in the registry, we
           generate a uuid.

        3. If a username is given and we do not use email as login,
           then we simply return that username as the user id.

        4. We create a user id based on the full name, if that is
           passed.  This may result in an id like bob-jones-2.

        When the email address is used as login name, we originally
        used the email address as user id as well.  This has a few
        possible downsides, which are the main reasons for the new,
        pluggable approach:

        - It does not work for some valid email addresses.

        - Exposing the email address in this way may not be wanted.

        - When the user later changes his email address, the user id
          will still be his old address.  It works, but may be
          confusing.

        Another possibility would be to simply generate a uuid, but that
        is ugly.  We could certainly try that though: the big plus here
        would be that you then cannot create a new user with the same user
        id as a previously existing user if this ever gets removed.  If
        you would get the same id, this new user would get the same global
        and local roles, if those have not been cleaned up.

        When a user id is chosen, the 'user_id' key of the data gets
        set and the user id is returned.
        """
        generator = queryUtility(IUserIdGenerator)
        if generator:
            userid = generator(data)
            if userid:
                data['user_id'] = userid
                return userid

        settings = self._get_security_settings()
        if settings.use_uuid_as_userid:
            userid = uuid_userid_generator()
            data['user_id'] = userid
            return userid

        # We may have a username already.
        userid = data.get('username')
        if userid:
            # If we are not using email as login, then this user name is fine.
            if not settings.use_email_as_login:
                data['user_id'] = userid
                return userid

        # First get a default value that we can return if we cannot
        # find anything better.
        pas = getToolByName(self.context, 'acl_users')
        email = pas.applyTransform(data.get('email'))
        default = data.get('username') or email or ''
        data['user_id'] = default
        fullname = data.get('fullname')
        if not fullname:
            return default
        userid = normalizeString(fullname)
        # First check that this is a valid member id, regardless of
        # whether a member with this id already exists or not.  We
        # access an underscore attribute of the registration tool, so
        # we take a precaution in case this is ever removed as an
        # implementation detail.
        registration = getToolByName(self.context, 'portal_registration')
        if hasattr(registration, '_ALLOWED_MEMBER_ID_PATTERN'):
            if not registration._ALLOWED_MEMBER_ID_PATTERN.match(userid):
                # If 'bob-jones' is not good then 'bob-jones-1' will not
                # be good either.
                return default
        if registration.isMemberIdAllowed(userid):
            data['user_id'] = userid
            return userid
        # Try bob-jones-1, bob-jones-2, etc.
        idx = 1
        while idx <= RENAME_AFTER_CREATION_ATTEMPTS:
            new_id = "%s-%d" % (userid, idx)
            if registration.isMemberIdAllowed(new_id):
                data['user_id'] = new_id
                return new_id
            idx += 1

        # We cannot come up with a nice id, so we simply return the default.
        return default

    def generate_login_name(self, data):
        """Generate a login name from data.

        Usually the login name and user id are the same, but this is
        not necessarily true.  When using the email address as login
        name, we may have a different user id, generated by calling
        the generate_user_id method.

        We try a few options for coming up with a good login name:

        1. We query a utility, so integrators can register a hook to
           generate a login name using their own logic.

        2. If a username is given and we do not use email as login,
           then we simply return that username as the login name.

        3. When using email as login, we use the email address.

        In all cases, we call PAS.applyTransform on the login name, if
        that is defined.  This is a recent addition to PAS, currently
        under development.

        When a login name is chosen, the 'login_name' key of the data gets
        set and the login name is returned.
        """
        pas = getToolByName(self.context, 'acl_users')
        generator = queryUtility(ILoginNameGenerator)
        if generator:
            login_name = generator(data)
            if login_name:
                login_name = pas.applyTransform(login_name)
                data['login_name'] = login_name
                return login_name

        # We may have a username already.
        login_name = data.get('username')
        login_name = pas.applyTransform(login_name)
        data['login_name'] = login_name
        settings = self._get_security_settings()
        # If we are not using email as login, then this user name is fine.
        if not settings.use_email_as_login:
            return login_name

        # We use email as login.
        login_name = data.get('email')
        login_name = pas.applyTransform(login_name)
        data['login_name'] = login_name
        return login_name

    # Actions validators
    def validate_registration(self, action, data):
        """Specific business logic for this join form.  Note: all this logic
        was taken directly from the old validate_registration.py script in
        Products/CMFPlone/skins/plone_login/join_form_validate.vpy
        """

        # CSRF protection
        CheckAuthenticator(self.request)

        registration = getToolByName(self.context, 'portal_registration')

        error_keys = [
            error.field.getName()
            for error
            in action.form.widgets.errors
        ]

        form_field_names = [f for f in self.fields]

        portal = getUtility(ISiteRoot)

        # passwords should match
        if 'password' in form_field_names:
            assert('password_ctl' in form_field_names)
            # Skip this check if password fields already have an error
            if not ('password' in error_keys or 'password_ctl' in error_keys):
                password = data.get('password')
                password_ctl = data.get('password_ctl')
                if password != password_ctl:
                    err_str = _(u'Passwords do not match.')
                    notifyWidgetActionExecutionError(action,
                                                     'password', err_str)
                    notifyWidgetActionExecutionError(action,
                                                     'password_ctl', err_str)

        # Password field checked against RegistrationTool
        if 'password' in form_field_names:
            # Skip this check if password fields already have an error
            if 'password' not in error_keys:
                password = data.get('password')
                if password:
                    # Use PAS to test validity
                    err_str = registration.testPasswordValidity(password)
                    if err_str:
                        notifyWidgetActionExecutionError(action,
                                                         'password', err_str)

        settings = self._get_security_settings()
        if settings.use_email_as_login:
            username_field = 'email'
        else:
            username_field = 'username'

        # The term 'username' is not clear.  It may be the user id or
        # the login name.  So here we try to be explicit.

        # Generate a nice user id and store that in the data.
        user_id = self.generate_user_id(data)
        # Generate a nice login name and store that in the data.
        login_name = self.generate_login_name(data)

        # Do several checks to see if the user id and the login name
        # are valid.
        #
        # Skip these checks if username was already in error list.
        #
        # Note that if we cannot generate a unique user id, it is not
        # necessarily the fault of the username field, but it
        # certainly is the most likely cause in a standard Plone
        # setup.

        # check if username is valid
        # Skip this check if username was already in error list
        if username_field not in error_keys:
            # user id may not be the same as the portal id.
            if user_id == portal.getId():
                err_str = _(u"This username is reserved. Please choose a "
                            "different name.")
                notifyWidgetActionExecutionError(action,
                                                 username_field, err_str)

        # Check if user id is allowed by the member id pattern.
        if username_field not in error_keys:
            if not registration.isMemberIdAllowed(user_id):
                err_str = _(u"The login name you selected is already in use "
                            "or is not valid. Please choose another.")
                notifyWidgetActionExecutionError(action,
                                                 username_field, err_str)

        if username_field not in error_keys:
            # Check the uniqueness of the login name, not only when
            # use_email_as_login is true, but always.
            pas = getToolByName(self, 'acl_users')
            results = pas.searchUsers(name=login_name, exact_match=True)
            if results:
                err_str = _(u"The login name you selected is already in use "
                            "or is not valid. Please choose another.")
                notifyWidgetActionExecutionError(action,
                                                 username_field, err_str)

        if 'password' in form_field_names and 'password' not in error_keys:
            # Admin can either set a password or mail the user (or both).
            if not (data['password'] or data['mail_me']):
                err_str = _('msg_no_password_no_mail_me',
                            default=u"You must set a password or choose to "
                            "send an email.")

                # set error on password field
                notifyWidgetActionExecutionError(action, 'password', err_str)
                notifyWidgetActionExecutionError(action, 'mail_me', err_str)

    @button.buttonAndHandler(
        _(u'label_register', default=u'Register'), name='register'
    )
    def action_join(self, action):
        data, errors = self.extractData()

        # extra password validation
        self.validate_registration(action, data)

        if action.form.widgets.errors:
            self.status = self.formErrorsMessage
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

        # user_id and login_name should be in the data, but let's be safe.
        user_id = data.get('user_id', data.get('username'))
        login_name = data.get('login_name', data.get('username'))
        # I have seen a unicode user id.  I cannot reproduce it, but
        # let's make them strings, otherwise you run into trouble with
        # plone.session when trying to login.
        if isinstance(user_id, unicode):
            user_id = user_id.encode('utf8')
        if isinstance(login_name, unicode):
            login_name = login_name.encode('utf8')

        # Set the username for good measure, as some code may expect
        # it to exist and contain the user id.
        data['username'] = user_id

        # The login name may already be in the form, but not
        # necessarily, for example when using email as login.  This is
        # at least needed for logging in immediately when password
        # reset is bypassed.  We need the login name here, not the
        # user id.
        self.request.form['form.username'] = login_name

        password = data.get('password') or registration.generatePassword()
        if isinstance(password, unicode):
            password = password.encode('utf8')

        try:
            registration.addMember(user_id, password, REQUEST=self.request)
        except (AttributeError, ValueError), err:
            logging.exception(err)
            IStatusMessage(self.request).addStatusMessage(err, type="error")
            return

        if user_id != login_name:
            # The user id differs from the login name.  Set the login
            # name correctly.
            pas = getToolByName(self.context, 'acl_users')
            pas.updateLoginName(user_id, login_name)

        # set member properties
        self.applyProperties(user_id, data)

        settings = self._get_security_settings()
        if data.get('mail_me') or (not settings.enable_user_pwd_choice and
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

        # Set any fields that are simply properties for the new user, rather
        # than fields to help create the new user
        register_fields = getFieldNames(IRegisterSchema) + \
            getFieldNames(IAddUserSchema)
        for k, value in data.items():
            # skip fields not available in the schema
            if k in ['login_name', 'user_id']:
                continue

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
                adapter.schema = schema

            # finally set value
            setattr(adapter, k, value)


class RegistrationForm(BaseRegistrationForm):
    """Dynamically get fields from user data, through admin config settings.
    """
    label = _(u'heading_registration_form', default=u'Registration form')
    description = u""
    template = ViewPageTemplateFile('register_form.pt')

    @property
    def showForm(self):
        """The form should not be displayed to the user if the system is
           incapable of sending emails and email validation is switched on
           (users are not allowed to select their own passwords).
        """
        portal = getUtility(ISiteRoot)
        ctrlOverview = getMultiAdapter((portal, self.request),
                                       name='overview-controlpanel')

        settings = self._get_security_settings()
        # hide form if mailhost_warning == True and
        # enable_user_pwd_choice == False
        return not (ctrlOverview.mailhost_warning() and
                    not settings.enable_user_pwd_choice)

    def updateFields(self):
        if not self.showForm:
            # We do not want to spend time calculating fields that
            # will never get displayed.
            return

        super(RegistrationForm, self).updateFields()
        defaultFields = field.Fields(self.fields)

        # Can the user actually set his/her own password?
        settings = self._get_security_settings()
        if not settings.enable_user_pwd_choice:
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
        settings = self._get_security_settings()
        if not settings.enable_user_pwd_choice:
            # Show a message indicating that a password reset link
            # will be mailed to the user.
            widget = self.widgets['mail_me']
            widget.mode = DISPLAY_MODE
            widget.value = ['selected']
            widget.label = _(
                u'label_password_change_mail',
                default=u"A URL will be generated and e-mailed to you; "
                        u"follow the link to reach a page where you can "
                        u"change your password and complete the registration "
                        u"process.")
            widget.terms = None
            widget.updateTerms()


class AddUserForm(BaseRegistrationForm):
    label = _(u'heading_add_user_form', default=u'Add New User')
    description = u""
    template = ViewPageTemplateFile('newuser_form.pt')

    def updateFields(self):
        super(AddUserForm, self).updateFields()
        defaultFields = field.Fields(self.fields)

        # The mail_me field needs special handling depending on the
        # enable_user_pwd_choice setting and on the correctness of the mail
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
            settings = self._get_security_settings()
            if not settings.enable_user_pwd_choice:
                defaultFields['mail_me'].field.default = True
            else:
                defaultFields['mail_me'].field.default = False

        # Append the manager-focused fields
        portal_props = getToolByName(self.context, 'portal_properties')
        props = portal_props.site_properties
        many_groups = props.getProperty('many_groups', False)
        if not many_groups:
            allFields = defaultFields + field.Fields(IAddUserSchema)
            allFields['groups'].widgetFactory = CheckBoxFieldWidget
        else:
            allFields = defaultFields
        self.fields = allFields

    def updateWidgets(self):
        super(AddUserForm, self).updateWidgets()

        # set display mode for mail_me field if no mailhost is configured
        portal = getUtility(ISiteRoot)
        ctrlOverview = getMultiAdapter(
            (portal, self.request), name='overview-controlpanel'
        )
        mail_settings_correct = not ctrlOverview.mailhost_warning()
        if not mail_settings_correct:
            widget = self.widgets['mail_me']
            widget.mode = DISPLAY_MODE
            widget.value = ['selected']
            widget.label = _(
                u'label_cant_mail_password_reset',
                default=u"Normally we would offer to send the user an email "
                        u"with instructions to set a password on completion "
                        u"of this form. But this site does not have a valid "
                        u"email setup. You can fix this in the Mail settings."
            )
            widget.terms = None
            widget.updateTerms()

    @button.buttonAndHandler(
        _(u'label_register', default=u'Register'), name='register'
    )
    def action_join(self, action):
        data, errors = self.extractData()

        # extra password validation
        self.validate_registration(action, data)

        if action.form.widgets.errors:
            self.status = self.formErrorsMessage
            return

        self.handle_join_success(data)

        portal_groups = getToolByName(self.context, 'portal_groups')
        user_id = data['user_id']
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
