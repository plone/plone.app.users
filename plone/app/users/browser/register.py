from zope.interface import Interface
from zope.component import getUtility, getAdapter, queryUtility
from zope.schema import getFieldNamesInOrder

from five.formlib.formbase import PageForm
from zope import schema
from zope.formlib import form
from zope.formlib.boolwidgets import CheckBoxWidget
from zope.formlib.interfaces import InputErrors
from zope.formlib.interfaces import WidgetInputError
from zope.formlib.textwidgets import ASCIIWidget
from zope.component import getMultiAdapter

from AccessControl import getSecurityManager
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import normalizeString, safe_unicode
from Products.CMFPlone import PloneMessageFactory as _
from Products.PlonePAS.interfaces.plugins import IUserManagement

from ZODB.POSException import ConflictError
from zExceptions import Forbidden

from Products.statusmessages.interfaces import IStatusMessage

from plone.app.users.userdataschema import IUserDataSchemaProvider

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.controlpanel.widgets import MultiCheckBoxVocabularyWidget

from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.site.hooks import getSite
from plone.protect import CheckAuthenticator

from plone.app.users.browser.interfaces import IUserIdGenerator
from plone.app.users.browser.interfaces import ILoginNameGenerator

import logging

# Define constants from the Join schema that should be added to the
# vocab of the join fields setting in usergroupssettings controlpanel.
JOIN_CONST = ['username', 'password', 'email', 'mail_me']
# Number of retries for creating a user id like bob-jones-42:
RENAME_AFTER_CREATION_ATTEMPTS = 100


class IRegisterSchema(Interface):

    username = schema.ASCIILine(
        title=_(u'label_user_name', default=u'User Name'),
        description=_(u'help_user_name_creation_casesensitive',
                      default=u"Enter a user name, usually something "
                               "like 'jsmith'. "
                               "No spaces or special characters. "
                               "Usernames and passwords are case sensitive, "
                               "make sure the caps lock key is not enabled. "
                               "This is the name used to log in."))

    password = schema.Password(
        title=_(u'label_password', default=u'Password'),
        description=_(u'help_password_creation',
                      default=u'Minimum 5 characters.'))

    password_ctl = schema.Password(
        title=_(u'label_confirm_password',
                default=u'Confirm password'),
        description=_(u'help_confirm_password',
                      default=u"Re-enter the password. "
                      "Make sure the passwords are identical."))

    mail_me = schema.Bool(
        title=_(u'label_mail_password',
                default=u"Send a confirmation mail with a link to set the "
                u"password"),
        required=False,
        default=False)


class IAddUserSchema(Interface):

    groups = schema.List(
        title=_(u'label_add_to_groups',
                default=u'Add to the following groups:'),
        description=u'',
        required=False,
        value_type=schema.Choice(vocabulary='Group Ids'))


def EmailWidget(field, request):
    """Widget for email field.

    Note that the email regular expression that is used for validation
    only allows ascii, so we also use the ASCIIWidget here.
    """
    field.description = _(
        u'help_email_creation',
        default=u"Enter an email address. "
        "This is necessary in case the password is lost. "
        "We respect your privacy, and will not give the address "
        "away to any third parties or expose it anywhere.")
    widget = ASCIIWidget(field, request)
    return widget


def EmailAsLoginWidget(field, request):
    """Widget for email field when emails are used as login names.
    """
    field.description = _(
        u'help_email_creation_for_login',
        default=u"Enter an email address. This will be your login name. "
        "We respect your privacy, and will not give the address away to any "
        "third parties or expose it anywhere.")
    widget = ASCIIWidget(field, request)
    return widget


class NoCheckBoxWidget(CheckBoxWidget):
    """ A widget used for _not_ displaying the checkbox.
    """

    def __call__(self):
        """Render the widget to HTML."""
        return ""


def CantChoosePasswordWidget(field, request):
    """ Change the mail_me field widget so it doesn't display the checkbox """

    field.title = u''
    field.readonly = True
    field.description = _(
        u'label_password_change_mail',
        default=u"A URL will be generated and e-mailed to you; "
        "follow the link to reach a page where you can change your "
        "password and complete the registration process.")
    widget = NoCheckBoxWidget(field, request)
    return widget


def CantSendMailWidget(field, request):
    """ Change the mail_me field widget so it displays a warning.

    This is meant for use in the 'add new user' form for admins to
    tell them that a confirmation email with a password reset link
    cannot be sent because the mailhost has not been setup.
    """

    field.title = u''
    field.readonly = True
    field.description = _(
        u'label_cant_mail_password_reset',
        default=u"Normally we would offer to send the user an email with "
        "instructions to set a password on completion of this form. But this "
        "site does not have a valid email setup. You can fix this in the "
        "Mail settings.")
    widget = NoCheckBoxWidget(field, request)
    return widget


def getGroupIds(context):
    site = getSite()
    groups_tool = getToolByName(site, 'portal_groups')
    groups = groups_tool.listGroups()
    # Get group id, title tuples for each, omitting virtual group
    # 'AuthenticatedUsers'
    terms = []
    for g in groups:
        if g.id == 'AuthenticatedUsers':
            continue
        is_zope_manager = getSecurityManager().checkPermission(
            ManagePortal, context)
        if 'Manager' in g.getRoles() and not is_zope_manager:
            continue

        group_title = safe_unicode(g.getGroupTitleOrName())
        if group_title != g.id:
            title = u'%s (%s)' % (group_title, g.id)
        else:
            title = group_title
        terms.append(SimpleTerm(g.id, g.id, title))
    # Sort by title
    terms.sort(key=lambda x: normalizeString(x.title))
    return SimpleVocabulary(terms)


class BaseRegistrationForm(PageForm):
    label = u""
    description = u""

    @property
    def form_fields(self):
        """ form_fields is dynamic in this form, to be able to handle
        different join styles.
        """
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

        all_fields = form.Fields(schema) + form.Fields(IRegisterSchema)

        if use_email_as_login:
            all_fields['email'].custom_widget = EmailAsLoginWidget
        else:
            all_fields['email'].custom_widget = EmailWidget

        # Make sure some fields are really required; a previous call
        # might have changed the default.
        for name in ('password', 'password_ctl'):
            all_fields[name].field.required = True

        # Pass the list of join form fields as a reference to the
        # Fields constructor, and return.
        return form.Fields(*[all_fields[id] for id in registration_fields])

    def generate_user_id(self, data):
        """Generate a user id from data.

        We try a few options for coming up with a good user id:

        1. We query a utility, so integrators can register a hook to
           generate a user id using their own logic.

        2. If a username is given and we do not use email as login,
           then we simply return that username as the user id.

        3. We create a user id based on the full name, if that is
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

        Another possibility would be to simply generate a uuid, but
        that is ugly.

        When a user id is chosen, the 'user_id' key of the data gets
        set and the user id is returned.
        """
        generator = queryUtility(IUserIdGenerator)
        if generator:
            userid = generator(data)
            if userid:
                data['user_id'] = userid
                return userid

        # We may have a username already.
        userid = data.get('username')
        if userid:
            # If we are not using email as login, then this user name is fine.
            portal_props = getToolByName(self.context, 'portal_properties')
            props = portal_props.site_properties
            if not props.getProperty('use_email_as_login'):
                data['user_id'] = userid
                return userid

        # First get a default value that we can return if we cannot
        # find anything better.
        default = data.get('username') or data.get('email') or ''
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
                try:
                    login_name = pas.applyTransform(login_name)
                except AttributeError:
                    pass
                data['login_name'] = login_name
                return login_name

        # We may have a username already.
        login_name = data.get('username')
        try:
            login_name = pas.applyTransform(login_name)
        except AttributeError:
            pass
        data['login_name'] = login_name
        portal_props = getToolByName(self.context, 'portal_properties')
        props = portal_props.site_properties
        use_email_as_login = props.getProperty('use_email_as_login')
        # If we are not using email as login, then this user name is fine.
        if not use_email_as_login:
            return login_name

        # We use email as login.
        login_name = data.get('email')
        try:
            login_name = pas.applyTransform(login_name)
        except AttributeError:
            pass
        data['login_name'] = login_name
        return login_name

    # Actions validators
    def validate_registration(self, action, data):
        """
        specific business logic for this join form
        note: all this logic was taken directly from the old
        validate_registration.py script in
        Products/CMFPlone/skins/plone_login/join_form_validate.vpy
        """

        # CSRF protection
        CheckAuthenticator(self.request)

        registration = getToolByName(self.context, 'portal_registration')

        errors = super(BaseRegistrationForm, self).validate(action, data)
        # ConversionErrors have no field_name attribute... :-(
        error_keys = [error.field_name for error in errors
                      if hasattr(error, 'field_name')]

        form_field_names = [f.field.getName() for f in self.form_fields]

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
                password = self.widgets['password'].getInputValue()
                password_ctl = self.widgets['password_ctl'].getInputValue()
                if password != password_ctl:
                    err_str = _(u'Passwords do not match.')
                    errors.append(WidgetInputError('password',
                                  u'label_password', err_str))
                    errors.append(WidgetInputError('password_ctl',
                                  u'label_password', err_str))
                    self.widgets['password'].error = err_str
                    self.widgets['password_ctl'].error = err_str

        # Password field should have a minimum length of 5
        if 'password' in form_field_names:
            # Skip this check if password fields already have an error
            if not 'password' in error_keys:
                password = self.widgets['password'].getInputValue()
                if password and len(password) < 5:
                    err_str = _(u'Passwords must contain at least 5 letters.')
                    errors.append(WidgetInputError(
                            'password', u'label_password', err_str))
                    self.widgets['password'].error = err_str

        email = ''
        try:
            email = self.widgets['email'].getInputValue()
        except InputErrors, exc:
            # WrongType?
            errors.append(exc)
        if use_email_as_login:
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

        if not username_field in error_keys:
            # user id may not be the same as the portal id.
            if user_id == portal.getId():
                err_str = _(u"This username is reserved. Please choose a "
                            "different name.")
                errors.append(WidgetInputError(
                        username_field, u'label_username', err_str))
                self.widgets[username_field].error = err_str

        if not username_field in error_keys:
            # Check if user id is allowed by the member id pattern.
            if not registration.isMemberIdAllowed(user_id):
                err_str = _(u"The login name you selected is already in use "
                            "or is not valid. Please choose another.")
                errors.append(WidgetInputError(
                        username_field, u'label_username', err_str))
                self.widgets[username_field].error = err_str

        # Skip this check if email was already in error list
        if not 'email' in error_keys:
            if 'email' in form_field_names:
                if not registration.isValidEmail(email):
                    err_str = _(u'You must enter a valid email address.')
                    errors.append(WidgetInputError(
                            'email', u'label_email', err_str))
                    self.widgets['email'].error = err_str

        if not username_field in error_keys:
            # Check the uniqueness of the login name, not only when
            # use_email_as_login is true, but always.
            pas = getToolByName(self, 'acl_users')
            results = pas.searchUsers(name=login_name, exact_match=True)
            if results:
                err_str = _(u"The login name you selected is already in use "
                            "or is not valid. Please choose another.")
                errors.append(WidgetInputError(
                        username_field, u'label_username', err_str))
                self.widgets[username_field].error = err_str

        if 'password' in form_field_names and not 'password' in error_keys:
            # Admin can either set a password or mail the user (or both).
            if not (self.widgets['password'].getInputValue() or
                    self.widgets['mail_me'].getInputValue()):
                err_str = _('msg_no_password_no_mail_me',
                            default=u"You must set a password or choose to "
                            "send an email.")
                errors.append(WidgetInputError(
                        'password', u'label_password', err_str))
                self.widgets['password'].error = err_str
                errors.append(WidgetInputError(
                        'mail_me', u'label_mail_me', err_str))
                self.widgets['mail_me'].error = err_str
        return errors

    @form.action(_(u'label_register', default=u'Register'),
                 validator='validate_registration', name=u'register')
    def action_join(self, action, data):
        self.handle_join_success(data)
        # XXX Return somewhere else, depending on what
        # handle_join_success returns?
        came_from = self.request.form.get('came_from')
        if came_from:
            utool = getToolByName(self.context, 'portal_url')
            if utool.isURLInPortal(came_from):
                self.request.response.redirect(came_from)
                return ''
        return self.context.unrestrictedTraverse('registered')()

    def handle_join_success(self, data):
        # portal should be acquisition wrapped, this is needed for the schema
        # adapter below
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        registration = getToolByName(self.context, 'portal_registration')
        mt = getToolByName(self.context, 'portal_membership')

        # user_id and login_name should be in the data, but let's be safe.
        user_id = data.get('user_id', data.get('username'))
        login_name = data.get('login_name', data.get('username'))

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
            acl_users = getToolByName(self.context, 'acl_users')
            # XXX It would be cleaner to have this in pas.
            for plugin_id, userfolder in acl_users.plugins.listPlugins(IUserManagement):
                if not hasattr(userfolder, 'updateUser'):
                    continue
                try:
                    userfolder.updateUser(user_id, login_name)
                except KeyError:
                    continue
                else:
                    break

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

        # hide form iff mailhost_warning == True and validate_email == True
        return not (ctrlOverview.mailhost_warning() and
                    portal.getProperty('validate_email', True))

    @property
    def form_fields(self):
        if not self.showForm:
            # We do not want to spend time calculating fields that
            # will never get displayed.
            return []
        portal = getUtility(ISiteRoot)
        defaultFields = super(RegistrationForm, self).form_fields
        # Can the user actually set his/her own password?
        if portal.getProperty('validate_email', True):
            # No? Remove the password fields.
            defaultFields = defaultFields.omit('password', 'password_ctl')
            # Show a message indicating that a password reset link
            # will be mailed to the user.
            defaultFields['mail_me'].custom_widget = CantChoosePasswordWidget
        else:
            # The portal is not interested in validating emails, and
            # the user is not interested in getting an email with a
            # link to set his password if he can set this password in
            # the current form already.
            defaultFields = defaultFields.omit('mail_me')

        return defaultFields


class AddUserForm(BaseRegistrationForm):

    label = _(u'heading_add_user_form', default=u'Add New User')
    description = u""
    template = ViewPageTemplateFile('newuser_form.pt')

    @property
    def form_fields(self):
        defaultFields = super(AddUserForm, self).form_fields

        # The mail_me field needs special handling depending on the
        # validate_email property and on the correctness of the mail
        # settings.
        portal = getUtility(ISiteRoot)
        ctrlOverview = getMultiAdapter((portal, self.request),
                                       name='overview-controlpanel')
        mail_settings_correct = not ctrlOverview.mailhost_warning()
        if not mail_settings_correct:
            defaultFields['mail_me'].custom_widget = CantSendMailWidget
        else:
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
        allFields = defaultFields + form.Fields(IAddUserSchema)

        allFields['groups'].custom_widget = MultiCheckBoxVocabularyWidget

        return allFields

    @form.action(_(u'label_register', default=u'Register'),
                 validator='validate_registration', name=u'register')
    def action_join(self, action, data):
        super(AddUserForm, self).handle_join_success(data)

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
