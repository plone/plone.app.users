from Acquisition import aq_inner
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import set_own_login_name
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PlonePAS.tools.membership import default_portrait
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.users.browser.account import AccountPanelForm
from plone.app.users.browser.account import AccountPanelSchemaAdapter
from plone.app.users.schema import IUserDataSchema
from z3c.form import button
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.interfaces import IErrorViewSnippet
from zope import schema
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.interface import Interface
from zope.interface import Invalid
from zope.schema import Bool
from zope.schema import Choice
from zope.schema import ValidationError


class IPersonalPreferences(Interface):
    """Provide schema for personalize form."""

    visible_ids = Bool(
        title=_(
            u'label_edit_short_names',
            default=u'Allow editing of Short Names'
        ),
        description=_(
            u'help_display_names',
            default=(u'Determines if Short Names (also known '
                     u'as IDs) are changable when editing items. If Short '
                     u'Names are not displayed, they will be generated '
                     u'automatically.')),
            required=False
        )

    wysiwyg_editor = Choice(
        title=_(u'label_wysiwyg_editor', default=u'Wysiwyg editor'),
        description=_(
            u'help_wysiwyg_editor',
            default=u'Wysiwyg editor to use.'
        ),
        vocabulary="plone.app.vocabularies.AvailableEditors",
        required=False,
        )

    ext_editor = Bool(
        title=_(u'label_ext_editor', default=u'Enable external editing'),
        description=_(
            u'help_content_ext_editor',
            default=u'When checked, an option will be made visible on each '
            'page which allows you to edit content with your favorite editor '
            'instead of using browser-based editors. This requires an '
            'additional application, most often ExternalEditor or '
            'ZopeEditManager, installed client-side. Ask your administrator '
            'for more information if needed.'
        ),
    )

    language = Choice(
        title=_(u'label_language', default=u'Language'),
        description=_(u'help_preferred_language', u'Your preferred language.'),
        vocabulary="plone.app.vocabularies.AvailableContentLanguages",
        required=False
        )

    timezone = Choice(
        title=_(u'label_timezone', default=u'Time zone'),
        description=_(u'help_timezone', default=u'Your time zone'),
        vocabulary='plone.app.event.AvailableTimezones',
        required=False,
        )


class PersonalPreferencesPanelAdapter(AccountPanelSchemaAdapter):
    schema = IPersonalPreferences


class PersonalPreferencesPanel(AccountPanelForm):
    """Implementation of personalize form that uses z3c.form."""

    label = _(u"heading_my_preferences", default=u"Personal Preferences")
    form_name = _(u'legend_personal_details', u'Personal Details')
    schema = IPersonalPreferences

    @property
    def description(self):
        userid = self.request.form.get('userid')
        mt = getToolByName(self.context, 'portal_membership')
        if userid and (userid != mt.getAuthenticatedMember().getId()):
            #editing someone else's profile
            return _(
                u'description_preferences_form_otheruser',
                default='Personal settings for $name',
                mapping={'name': userid}
            )
        else:
            #editing my own profile
            return _(
                u'description_my_preferences',
                default='Your personal settings.'
            )

    def updateWidgets(self):
        """ Hide the visible_ids field based on portal_properties.
        """
        context = aq_inner(self.context)
        properties = getToolByName(context, 'portal_properties')
        siteProperties = properties.site_properties

        super(PersonalPreferencesPanel, self).updateWidgets()

        self.widgets['language'].noValueMessage = _(
            u"vocabulary-missing-single-value-for-edit",
            u"Language neutral (site default)"
        )
        self.widgets['wysiwyg_editor'].noValueMessage = _(
            u"vocabulary-available-editor-novalue",
            u"Use site default"
        )
        if not siteProperties.visible_ids:
            self.widgets['visible_ids'].mode = HIDDEN_MODE


class PersonalPreferencesConfiglet(PersonalPreferencesPanel):
    """Control panel version of the personal preferences panel"""
    template = ViewPageTemplateFile('account-configlet.pt')


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

###


class CurrentPasswordError(ValidationError):
    __doc__ = _(u"Incorrect value for current password")


# Define validator(s)
#
def checkCurrentPassword(value):
    """ Test current password against given. """

    portal = getUtility(ISiteRoot)
    membertool = getToolByName(portal, 'portal_membership')

    current_password = value.encode('ascii', 'ignore')

    if not membertool.testCurrentPassword(current_password):
        raise ()

    return True


class IPasswordSchema(Interface):
    """Provide schema for password form """

    current_password = schema.Password(
        title=_(u'label_current_password', default=u'Current password'),
        description=_(
            u'help_current_password',
            default=u'Enter your current password.'),
        #constraint=checkCurrentPassword,
        )

    new_password = schema.Password(
        title=_(u'label_new_password', default=u'New password'),
        description=_(
            u'help_new_password',
            default=u"Enter your new password."),
        )

    new_password_ctl = schema.Password(
        title=_(u'label_confirm_password', default=u'Confirm password'),
        description=_(
            u'help_confirm_password',
            default=u"Re-enter the password. "
            u"Make sure the passwords are identical."),
        )


class PasswordPanelAdapter(SchemaAdapterBase):

    def __init__(self, context):
        self.context = getToolByName(context, 'portal_membership')

    def get_dummy(self):
        """ We don't actually need to 'get' anything ..."""
        return ''

    current_password = property(get_dummy)

    new_password = property(get_dummy)

    new_password_ctl = property(get_dummy)


class PasswordPanel(AccountPanelForm):
    """Implementation of password reset form that uses z3c.form."""

    label = _(u'listingheader_reset_password', default=u'Reset Password')
    description = _(u"Change Password")
    form_name = _(u'legend_password_details', default=u'Password Details')
    schema = IPasswordSchema

    def updateFields(self):
        super(PasswordPanel, self).updateFields()
        # Change the password description based on PAS Plugin The user needs a
        # list of instructions on what kind of password is required.  We'll
        # reuse password errors as instructions e.g. "Must contain a letter and
        # a number".  Assume PASPlugin errors are already translated
        registration = getToolByName(self.context, 'portal_registration')
        err_str = registration.testPasswordValidity('')
        if err_str:
            msg = _(
                u'Enter your new password. ${errors}',
                mapping=dict(errors=err_str)
            )
            self.fields['new_password'].field.description = msg

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
                err_view = getMultiAdapter((
                    Invalid(err_str),
                    self.request,
                    widget,
                    widget.field,
                    self,
                    self.context), IErrorViewSnippet)
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
                err_view = getMultiAdapter((
                    Invalid(failMessage),
                    self.request,
                    widget,
                    widget.field,
                    self,
                    self.context), IErrorViewSnippet)
                err_view.update()
                widget.error = err_view
                self.widgets.errors += (err_view,)
                errors += (err_view,)

                # add error to new_password_ctl widget
                widget = self.widgets['new_password_ctl']
                err_view = getMultiAdapter((
                    Invalid(failMessage),
                    self.request,
                    widget,
                    widget.field,
                    self,
                    self.context), IErrorViewSnippet)
                err_view.update()
                widget.error = err_view
                self.widgets.errors += (err_view,)
                errors += (err_view,)

        return errors

    @button.buttonAndHandler(
        _(u'label_change_password', default=u'Change Password'),
        name='reset_passwd'
    )
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

            IStatusMessage(self.request).addStatusMessage(
                _(failMessage), type="error"
            )
            return

        IStatusMessage(self.request).addStatusMessage(
            _("Password changed"), type="info"
        )

    # hide inherited Save and Cancel buttons
    @button.buttonAndHandler(_(u'Save'), condition=lambda form: False)
    def handleSave(self, action):
        pass

    @button.buttonAndHandler(_(u'Cancel'), condition=lambda form: False)
    def cancel(self, action):
        pass
