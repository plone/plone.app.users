from plone.base import PloneMessageFactory as _
from plone.formwidget.namedfile.widget import NamedImageWidget
from plone.namedfile.interfaces import INamedImageField
from plone.schema.email import Email
from plone.schemaeditor.fields import FieldFactory
from plone.schemaeditor.interfaces import IFieldFactory
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.RegistrationTool import EmailAddressInvalid
from z3c.form.interfaces import IFieldWidget
from z3c.form.interfaces import IFormLayer
from z3c.form.widget import FieldWidget
from zope import schema
from zope.component import adapter
from zope.component import getUtility
from zope.interface import implementer
from zope.interface import Interface
from ZTUtils import make_query


SCHEMA_ANNOTATION = "plone.app.users.schema"
# must match the browser view name !
SCHEMATA_KEY = "member-fields"


def checkEmailAddress(value):
    portal = getUtility(ISiteRoot)

    reg_tool = getToolByName(portal, "portal_registration")
    if value and reg_tool.isValidEmail(value):
        pass
    else:
        # TODO: check if there is a z3c validator
        raise EmailAddressInvalid
    return True


class ProtectedTextLine(schema.TextLine):
    """TextLine field which cannot be edited via schema editor"""

    pass


class ProtectedEmail(Email):
    """Email field which cannot be edited via schema editor"""

    pass


@implementer(IFieldFactory)
class NotEditableFieldFactory(FieldFactory):
    title = _("(protected)")

    def protected(self, field):
        return True


FullnameFieldFactory = NotEditableFieldFactory(
    ProtectedTextLine,
    _("label_full_name", default="Full Name"),
)

EmailFieldFactory = NotEditableFieldFactory(
    ProtectedEmail,
    _("label_email", default="Email"),
)


class IUserDataSchema(Interface):
    """ """

    fullname = ProtectedTextLine(
        title=_("label_full_name", default="Full Name"),
        description=_(
            "help_full_name_creation",
            default="Enter full name, for example, John Smith.",
        ),
        required=False,
    )

    email = ProtectedEmail(
        title=_("label_email", default="Email"),
        description=_("We will use this address if you need to recover your password"),
        required=True,
        constraint=checkEmailAddress,
    )


class IRegisterSchema(Interface):
    username = schema.ASCIILine(
        title=_("label_user_name", default="User Name"),
        description=_(
            "help_user_name_creation_casesensitive",
            default="Enter a user name, usually something like 'jsmith'. "
            "No spaces or special characters. Usernames and "
            "passwords are case sensitive, make sure the caps lock "
            "key is not enabled. This is the name used to log in.",
        ),
    )

    password = schema.Password(
        title=_("label_password", default="Password"),
        description=_("help_password_creation", default="Enter your new password."),
    )

    password_ctl = schema.Password(
        title=_("label_confirm_password", default="Confirm password"),
        description=_(
            "help_confirm_password",
            default="Re-enter the password. Make sure the passwords are identical.",
        ),
    )

    mail_me = schema.Bool(
        title=_(
            "label_mail_password",
            default="Send a confirmation mail with a link to set the password",
        ),
        required=False,
        default=False,
    )


class ICombinedRegisterSchema(IRegisterSchema, IUserDataSchema):
    """Collect all register fields under the same interface"""


class IAddUserSchema(Interface):
    groups = schema.List(
        title=_("label_add_to_groups", default="Add to the following groups:"),
        description="",
        required=False,
        value_type=schema.Choice(vocabulary="plone.app.users.group_ids"),
    )


class PortraitWidget(NamedImageWidget):
    # Cheat around 2 bugs:
    # * You are not authenticated during traversal, so fetching
    #   the current user does not work.
    # * download_url won't append our querystring, so fetching
    #   another user's image does not work.
    @property
    def download_url(self):
        userid = self.request.form.get("userid")
        if not userid:
            mt = getToolByName(self.form.context, "portal_membership")
            userid = mt.getAuthenticatedMember().getId()

        # anonymous
        if not userid:
            return None

        url = super().download_url
        if not url:
            return None

        return "{}?{}".format(url, make_query({"userid": userid}))


@implementer(IFieldWidget)
@adapter(INamedImageField, IFormLayer)
def PortraitFieldWidget(field, request):
    return FieldWidget(field, PortraitWidget(request))


class IRegistrationSettingsSchema(Interface):
    user_registration_fields = schema.Tuple(
        title=_("title_user_registration_fields", default="User registration fields"),
        description=_(
            "description_user_registration_fields",
            default=(
                "Select the fields for the join form. Fields in the "
                "right box will be shown on the form, fields on the "
                "left are disabled. Use the left/right buttons to move "
                "a field from right to left (to disable it) and vice "
                "versa. Use the up/down buttons to change the order in "
                "which the fields appear on the form."
            ),
        ),
        value_type=schema.Choice(vocabulary="plone.app.users.user_registration_fields"),
    )


class IUserSchemaProvider(Interface):
    pass
