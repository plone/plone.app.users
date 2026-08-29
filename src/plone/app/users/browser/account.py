from AccessControl import Unauthorized
from Acquisition import aq_inner
from PIL import Image
from PIL import UnidentifiedImageError
from plone.app.users.browser.interfaces import IAccountPanelForm
from plone.app.users.browser.schemaeditor import getFromBaseSchema
from plone.base import PloneMessageFactory as _
from plone.base.interfaces import INavigationRoot
from plone.base.interfaces import IPloneSiteRoot
from plone.base.interfaces import ISecuritySchema
from plone.base.utils import safe_text
from plone.namedfile.file import NamedBlobImage
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.tools.membership import default_portrait
from z3c.form.interfaces import NOT_CHANGED
from zope import schema
from zope.component import getUtility
from zope.component import provideAdapter
from zope.globalrequest import getRequest

import zope.deferredimport

zope.deferredimport.initialize()

zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.account import AccountPanelForm instead.",
    AccountPanelForm="plone.app.layout.users.account:AccountPanelForm",
)

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


class AccountPanelValidation:

    def validate_email(self, data):
        context = aq_inner(self.context)
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
        return err_str

    def validate_portrait(self, action, data):
        """Portrait validation.
        Checks if image is supported by Pillow.
        SVG files are not yet supported.
        """
        portrait_file = data["portrait"]
        if portrait_file is None or portrait_file is NOT_CHANGED:
            return
        with portrait_file.open() as portrait:
            try:
                Image.open(portrait)
            except UnidentifiedImageError:
                return MESSAGE_IMAGE_NOT_SUPPORTED
            except Exception as exc:
                raise exc
