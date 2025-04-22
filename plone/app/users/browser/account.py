from AccessControl import Unauthorized
from Acquisition import aq_inner
from PIL import Image
from PIL import UnidentifiedImageError
from plone.app.users.browser.interfaces import IAccountPanelForm
from plone.app.users.browser.schemaeditor import getFromBaseSchema
from plone.app.users.utils import notifyWidgetActionExecutionError
from plone.autoform.form import AutoExtensibleForm
from plone.base import PloneMessageFactory as _
from plone.base.interfaces import INavigationRoot
from plone.base.interfaces import IPloneSiteRoot
from plone.base.interfaces import ISecuritySchema
from plone.base.utils import safe_text
from plone.namedfile.file import NamedBlobImage
from plone.protect import CheckAuthenticator
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.controlpanel.events import ConfigurationChangedEvent
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PlonePAS.tools.membership import default_portrait
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from z3c.form import form
from z3c.form.interfaces import NOT_CHANGED
from zope import schema
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import provideAdapter
from zope.event import notify
from zope.globalrequest import getRequest
from zope.interface import implementer
from ZTUtils import make_query


MESSAGE_EMAIL_CANNOT_CHANGE = _(
    "message_email_cannot_change",
    default=("Sorry, you are not allowed to change your email address."),
)

MESSAGE_EMAIL_IN_USE = _(
    "message_email_in_use",
    default=(
        "The email address you selected is "
        "already in use or is not valid as login "
        "name. Please choose another."
    ),
)

MESSAGE_IMAGE_NOT_SUPPORTED = _(
    "message_image_not_supported",
    "The file you selected is not supported by Pillow. Please choose another.",
)


def getSchema(schema_interface, schema_adapter, form_name=None):
    request = getRequest()
    form_name_to_request_attr_name = {
        "In User Profile": "_userdata_schema",
        "On Registration": "_register_schema",
        None: "_userdata_manager_schema",
    }
    request_attr_name = form_name_to_request_attr_name.pop(form_name, None)
    if request_attr_name is not None:
        schema = getattr(request, request_attr_name, None)
    else:
        schema = None
    if schema is None:
        schema = getFromBaseSchema(schema_interface, form_name=form_name)
        # Unset all request attr names.
        # We do not want other caches to linger.
        # See https://github.com/plone/plone.app.users/issues/76
        # This is in the unlikely case that you visit both the add-user/register form
        # and the user/personal-information form in one request,
        # maybe during a migration.
        for name in form_name_to_request_attr_name.values():
            try:
                delattr(request, name)
            except AttributeError:
                pass
        if request_attr_name is not None:
            setattr(request, request_attr_name, schema)
        # As schema is a generated supermodel,
        # needed adapters can only be registered at run time.
        # Note that this overrides previous adapters for the same interfaces.
        provideAdapter(schema_adapter, (IPloneSiteRoot,), schema)
        provideAdapter(schema_adapter, (INavigationRoot,), schema)
    return schema


def isDefaultPortrait(value, portal):
    default_portrait_value = getattr(portal, default_portrait, None)
    return aq_inner(value) == aq_inner(default_portrait_value)


class AccountPanelSchemaAdapter:
    """Data manager that gets and sets any property mentioned
    in the schema to the property sheet
    """

    context = None
    schema = IAccountPanelForm

    def __init__(self, context):
        mt = getToolByName(context, "portal_membership")
        userid = context.REQUEST.form.get("userid")
        if userid and mt.checkPermission("Plone Site Setup: Users and Groups", context):
            self.context = mt.getMemberById(userid)
        else:
            self.context = mt.getAuthenticatedMember()

    def _getProperty(self, name):
        value = self.context.getProperty(name, "")
        if value == "":
            value = None
        if value:
            # PlonePAS encodes all unicode coming from PropertySheets.
            return safe_text(value)
        return value

    def _setProperty(self, name, value):
        if isinstance(value, set):
            value = list(value)
        if value and isinstance(self.schema[name], schema.Choice):
            value = str(value)
        return self.context.setMemberProperties({name: value}, force_empty=True)

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
            return super().__setattr__(name, value)
        if isinstance(value, NamedBlobImage):
            # any image is stored as portrait
            return self.set_portrait(value)

        return self._setProperty(name, value)

    @property
    def portal(self):
        return getToolByName(self.context, "portal_url").getPortalObject()

    def get_portrait(self):
        """If user has default portrait, return none"""
        mt = getToolByName(self.context, "portal_membership")
        value = mt.getPersonalPortrait(self.context.getId())
        if isDefaultPortrait(value, self.portal):
            return None
        return NamedBlobImage(
            value.data,
            contentType=value.content_type,
            filename=getattr(value, "filename", None),
        )

    def set_portrait(self, value):
        mt = getToolByName(self.context, "portal_membership")
        member_id = self.context.getId()
        if value is None:
            previous = mt.getPersonalPortrait(member_id)
            if not isDefaultPortrait(previous, self.portal):
                mt.deletePersonalPortrait(str(member_id))
        else:
            portrait_file = value.open()
            portrait_file.filename = value.filename
            mt.changeMemberPortrait(portrait_file, str(self.context.getId()))
            portrait_file.close()

    portrait = property(get_portrait, set_portrait)

    @property
    def wysiwyg_editor(self):
        return self._getProperty("wysiwyg_editor")

    @wysiwyg_editor.setter
    def wysiwyg_editor(self, value):
        if value is None:
            # set property that the site-default from the registry is used
            # since both 'None' and None result in plaintexteditor
            value = ""
        return self._setProperty("wysiwyg_editor", value)

    @property
    def timezone(self):
        return self._getProperty("timezone")

    @timezone.setter
    def timezone(self, value):
        if value is None:
            value = ""
        return self._setProperty("timezone", value)


@implementer(IAccountPanelForm)
class AccountPanelForm(AutoExtensibleForm, form.Form):
    """A simple form to be used as a basis for account panel screens."""

    schema = IAccountPanelForm
    template = ViewPageTemplateFile("account-panel.pt")
    enableCSRFProtection = True

    hidden_widgets = []
    successMessage = _("Changes saved.")
    noChangesMessage = _("No changes made.")

    @lazy_property
    def member(self):
        mtool = getToolByName(self.context, "portal_membership")
        if self.request.get("userid"):
            return mtool.getMemberById(self.request.get("userid"))
        return mtool.getAuthenticatedMember()

    @property
    def label(self):
        return self.member.getProperty("fullname") or self.member.getUserName()

    def _differentEmail(self, email):
        """Check if the submitted form email address differs from the existing
        one.

        Keeping your email the same (which happens when you change something
        else on the personalize form) or changing it back to your login name,
        is fine.

        So: we only return True if it is *really* a different email.
        """
        membership = getToolByName(self.context, "portal_membership")
        if self.request.get("userid"):
            member = membership.getMemberById(self.request.get("userid"))
        else:
            member = membership.getAuthenticatedMember()
        if email in (member.getId(), member.getUserName()):
            return False
        # By default, PAS transforms login names to lowercase, at least when
        # email-as-login is used.  So compare the transformed/normalized names.
        pas = getToolByName(self.context, "acl_users")
        email_normalized = pas.applyTransform(email)
        # The user name should already have been normalized, but let's make sure.
        login_normalized = pas.applyTransform(member.getUserName())
        return email_normalized != login_normalized

    def makeQuery(self):
        userid = self.request.form.get("userid", None)
        if userid is not None:
            return "?{}".format(make_query({"userid": userid}))
        return ""

    def action(self):
        return self.request.getURL() + self.makeQuery()

    def validate_email(self, action, data):
        context = aq_inner(self.context)
        error_keys = [error.field.getName() for error in action.form.widgets.errors]
        if "email" in error_keys:
            # There is already a validation error for email,
            # so there is no need for further validation.
            return
        # We only need an extra check if email is used as login.
        registry = getUtility(IRegistry)
        security_settings = registry.forInterface(ISecuritySchema, prefix="plone")
        if not security_settings.use_email_as_login:
            return

        registration = getToolByName(context, "portal_registration")
        err_str = ""
        email = data["email"]
        try:
            if hasattr(registration, "principal_id_or_login_name_exists"):
                # This is a new addition, as isMemberIdAllowed will reject
                # some valid email addresses because they would be bad when
                # used as actual ids, instead of just login names.
                # isMemberIdAllowed also calls this new method now.
                id_allowed = not registration.principal_id_or_login_name_exists(email)
            else:
                id_allowed = registration.isMemberIdAllowed(email)
        except Unauthorized:
            # This try/except Unauthorized may be an unneeded left-over from the
            # days when this code was in a Python skin script.  But hard to be sure.
            err_str = MESSAGE_EMAIL_CANNOT_CHANGE
        else:
            if not id_allowed:
                # A member with this login name already exists.
                # Only allow if unchanged: then that member is us!
                if self._differentEmail(email):
                    err_str = MESSAGE_EMAIL_IN_USE
        if err_str:
            notifyWidgetActionExecutionError(action, "email", err_str)

    def validate_portrait(self, action, data):
        """Portrait validation.
        Checks if image is supported by Pillow.
        SVG files are not yet supported.
        """
        error_keys = [error.field.getName() for error in action.form.widgets.errors]
        if "portrait" in error_keys:
            return
        portrait_file = data["portrait"]
        if portrait_file is None or portrait_file is NOT_CHANGED:
            return
        with portrait_file.open() as portrait:
            try:
                Image.open(portrait)
            except UnidentifiedImageError:
                notifyWidgetActionExecutionError(
                    action, "portrait", MESSAGE_IMAGE_NOT_SUPPORTED
                )
            except Exception as exc:
                raise exc

    @button.buttonAndHandler(_("Save"))
    def handleSave(self, action):
        CheckAuthenticator(self.request)
        data, errors = self.extractData()

        # Extra validation for email, when it is there.  email is not in the
        # data when you are at the personal-preferences page.
        if "email" in data:
            self.validate_email(action, data)

        # Validate portrait, upload image could be not supported
        # by PIL what raises an exception when scaling image.
        if "portrait" in data:
            self.validate_portrait(action, data)

        if action.form.widgets.errors:
            self.status = self.formErrorsMessage
            return
        if self.applyChanges(data):
            IStatusMessage(self.request).addStatusMessage(
                self.successMessage, type="info"
            )
            notify(ConfigurationChangedEvent(self, data))
            self._on_save(data)
        else:
            IStatusMessage(self.request).addStatusMessage(
                self.noChangesMessage, type="info"
            )
        self.request.response.redirect(self.action())

    def updateActions(self):
        super().updateActions()
        if self.actions and "save" in self.actions:
            self.actions["save"].addClass("btn btn-primary")

    @button.buttonAndHandler(_("Cancel"))
    def cancel(self, action):
        IStatusMessage(self.request).addStatusMessage(
            _("Changes canceled."), type="info"
        )
        self.request.response.redirect(
            "{}{}".format(self.request["ACTUAL_URL"], self.makeQuery())
        )

    def _on_save(self, data=None):
        pass

    def prepareObjectTabs(self, default_tab="view", sort_first=["folderContents"]):
        context = self.context
        mt = getToolByName(context, "portal_membership")
        tabs = []
        navigation_root_url = context.absolute_url()

        def _check_allowed(context, request, name):
            """Check, if user has required permissions on view."""
            view = getMultiAdapter((context, request), name=name)
            allowed = True
            for perm in view.__ac_permissions__:
                allowed = allowed and mt.checkPermission(perm[0], context)
            return allowed

        if _check_allowed(context, self.request, "personal-information"):
            tabs.append(
                {
                    "title": _(
                        "title_personal_information_form", "Personal Information"
                    ),
                    "url": navigation_root_url + "/@@personal-information",
                    "selected": (self.__name__ == "personal-information"),
                    "id": "user_data-personal-information",
                }
            )

        if _check_allowed(context, self.request, "personal-preferences"):
            tabs.append(
                {
                    "title": _("Personal Preferences"),
                    "url": navigation_root_url + "/@@personal-preferences",
                    "selected": (self.__name__ == "personal-preferences"),
                    "id": "user_data-personal-preferences",
                }
            )

        member = mt.getAuthenticatedMember()
        if member.canPasswordSet():
            tabs.append(
                {
                    "title": _("label_password", "Password"),
                    "url": navigation_root_url + "/@@change-password",
                    "selected": (self.__name__ == "change-password"),
                    "id": "user_data-change-password",
                }
            )
        return tabs
