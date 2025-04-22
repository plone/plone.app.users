from Acquisition import aq_inner
from plone.app.users.browser.account import AccountPanelForm
from plone.app.users.utils import notifyWidgetActionExecutionError
from plone.base import PloneMessageFactory as _
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from zope import schema
from zope.interface import Interface


class IPasswordSchema(Interface):
    """Provide schema for password form"""

    current_password = schema.Password(
        title=_("label_current_password", default="Current password"),
        description=_("help_current_password", default="Enter your current password."),
        # constraint=checkCurrentPassword,
    )

    new_password = schema.Password(
        title=_("label_new_password", default="New password"),
        description=_("help_new_password", default="Enter your new password."),
    )

    new_password_ctl = schema.Password(
        title=_("label_confirm_password", default="Confirm password"),
        description=_(
            "help_confirm_password",
            default="Re-enter the password. Make sure the passwords are identical.",
        ),
    )


class PasswordPanelAdapter:
    def __init__(self, context):
        self.context = getToolByName(context, "portal_membership")

    def get_dummy(self):
        """We don't actually need to 'get' anything ..."""
        return ""

    current_password = property(get_dummy)

    new_password = property(get_dummy)

    new_password_ctl = property(get_dummy)


class PasswordPanel(AccountPanelForm):
    """Implementation of password reset form that uses z3c.form."""

    description = _("Change Password")
    form_name = _("legend_password_details", default="Password Details")
    schema = IPasswordSchema

    def updateFields(self):
        super().updateFields()
        # Change the password description based on PAS Plugin The user needs a
        # list of instructions on what kind of password is required.  We'll
        # reuse password errors as instructions e.g. "Must contain a letter and
        # a number".  Assume PASPlugin errors are already translated
        registration = getToolByName(self.context, "portal_registration")
        err_str = registration.testPasswordValidity("")
        if err_str:
            msg = _("Enter your new password. ${errors}", mapping=dict(errors=err_str))
            self.fields["new_password"].field.description = msg

    def validate_password(self, action, data):
        context = aq_inner(self.context)
        registration = getToolByName(context, "portal_registration")
        membertool = getToolByName(context, "portal_membership")

        # check if password is correct
        current_password = data.get("current_password")
        if current_password:
            if not membertool.testCurrentPassword(current_password):
                # add error to current_password widget
                err_str = _("Incorrect value for current password")
                notifyWidgetActionExecutionError(action, "current_password", err_str)

        # check if passwords are same and valid according to plugin
        new_password = data.get("new_password")
        new_password_ctl = data.get("new_password_ctl")
        if new_password and new_password_ctl:
            err_str = registration.testPasswordValidity(new_password, new_password_ctl)

            if err_str:
                # add error to new_password widget
                notifyWidgetActionExecutionError(action, "new_password", err_str)
                notifyWidgetActionExecutionError(action, "new_password_ctl", err_str)

    @button.buttonAndHandler(
        _("label_change_password", default="Change Password"), name="reset_passwd"
    )
    def action_reset_passwd(self, action):
        data, errors = self.extractData()

        # extra password validation
        self.validate_password(action, data)

        if action.form.widgets.errors:
            self.status = self.formErrorsMessage
            return

        membertool = getToolByName(self.context, "portal_membership")

        password = data["new_password"]

        try:
            membertool.setPassword(password, None, REQUEST=self.request)
        except AttributeError:
            failMessage = _(
                "While changing your password an AttributeError "
                "occurred. This is usually caused by your user "
                "being defined outside the portal."
            )

            IStatusMessage(self.request).addStatusMessage(_(failMessage), type="error")
            return

        IStatusMessage(self.request).addStatusMessage(
            _("Password changed"), type="info"
        )

    # hide inherited Save and Cancel buttons
    @button.buttonAndHandler(_("Save"), condition=lambda form: False)
    def handleSave(self, action):
        pass

    @button.buttonAndHandler(_("Cancel"), condition=lambda form: False)
    def cancel(self, action):
        pass
