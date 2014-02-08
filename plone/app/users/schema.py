from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.exceptions import EmailAddressInvalid
from Products.CMFPlone import PloneMessageFactory as _
from plone.autoform import directives as form
from plone.namedfile.field import NamedBlobImage
from zope import schema
from zope.component import getUtility
from zope.interface import Interface
from plone.formwidget.namedfile.widget import NamedImageWidget
from plone.namedfile.interfaces import INamedImageField
from ZTUtils import make_query
from z3c.form.interfaces import IFieldWidget, IFormLayer
from z3c.form.widget import FieldWidget
from zope.component import adapter
from zope.interface import implementer

SCHEMA_ANNOTATION = "plone.app.users.schema"
# must match the browser view name !
SCHEMATA_KEY = "member-fields"

def checkEmailAddress(value):
    portal = getUtility(ISiteRoot)

    reg_tool = getToolByName(portal, 'portal_registration')
    if value and reg_tool.isValidEmail(value):
        pass
    else:
        # TODO: check if there is a z3c validator
        raise EmailAddressInvalid
    return True


class IUserDataSchema(Interface):
    """
    """

    fullname = schema.TextLine(
        title=_(u'label_full_name', default=u'Full Name'),
        description=_(u'help_full_name_creation',
                      default=u"Enter full name, e.g. John Smith."),
        required=False)

    email = schema.ASCIILine(
        title=_(u'label_email', default=u'E-mail'),
        description=u'',
        required=True,
        constraint=checkEmailAddress)

    home_page = schema.TextLine(
        title=_(u'label_homepage', default=u'Home page'),
        description=_(u'help_homepage',
                      default=u"The URL for your external home page, "
                      "if you have one."),
        required=False)

    description = schema.Text(
        title=_(u'label_biography', default=u'Biography'),
        description=_(u'help_biography',
                      default=u"A short overview of who you are and what you "
                      "do. Will be displayed on your author page, linked "
                      "from the items you create."),
        required=False)

    location = schema.TextLine(
        title=_(u'label_location', default=u'Location'),
        description=_(u'help_location',
                      default=u"Your location - either city and "
                      "country - or in a company setting, where "
                      "your office is located."),
        required=False)

    portrait = NamedBlobImage(
        title=_(u'label_portrait', default=u'Portrait'),
        description=_(
            u'help_portrait',
            default=u'To add or change the portrait: click the "Browse" '
                    u'button; select a picture of yourself.  Recommended '
                    u'image size is 75 pixels wide by 100 pixels tall.'
        ),
        required=False)
    form.widget(portrait='plone.app.users.schema.PortraitFieldWidget')


class IRegisterSchema(Interface):

    username = schema.ASCIILine(
        title=_(u'label_user_name', default=u'User Name'),
        description=_(
            u'help_user_name_creation_casesensitive',
            default=u"Enter a user name, usually something like 'jsmith'. "
                    u"No spaces or special characters. Usernames and "
                    u"passwords are case sensitive, make sure the caps lock "
                    u"key is not enabled. This is the name used to log in."
        )
    )

    password = schema.Password(
        title=_(u'label_password', default=u'Password'),
        description=_(u'help_password_creation',
                      default=u'Enter your new password.'))

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


class ICombinedRegisterSchema(IRegisterSchema, IUserDataSchema):
    """Collect all register fields under the same interface"""


class IAddUserSchema(Interface):

    groups = schema.List(
        title=_(u'label_add_to_groups',
                default=u'Add to the following groups:'),
        description=u'',
        required=False,
        value_type=schema.Choice(vocabulary='plone.app.users.group_ids'))


class PortraitWidget(NamedImageWidget):
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
            userid = mt.getAuthenticatedMember().getId()

        # anonymous
        if not userid:
            return None

        url = super(PortraitWidget, self).download_url
        if not url:
            return None

        return '%s?%s' % (url, make_query({'userid': userid}))


@implementer(IFieldWidget)
@adapter(INamedImageField, IFormLayer)
def PortraitFieldWidget(field, request):
    return FieldWidget(field, PortraitWidget(request))


class IRegistrationSettingsSchema(Interface):

    user_registration_fields = schema.Tuple(
        title=_(
            u'title_user_registration_fields',
            default=u'User registration fields'
        ),
        description=_(
            u"description_user_registration_fields",
            default=(u"Select the fields for the join form. Fields in the "
                     u"right box will be shown on the form, fields on the "
                     u"left are disabled. Use the left/right buttons to move "
                     u"a field from right to left (to disable it) and vice "
                     u"versa. Use the up/down buttons to change the order in "
                     u"which the fields appear on the form."),
        ),
        value_type=schema.Choice(
            vocabulary='plone.app.users.user_registration_fields'),
    )


class IUserDataSchemaProvider(Interface):
    """
    """

    def getSchema():
        """
        Return base user schema + TTW Fields
        """


class IRegisterSchemaProvider(Interface):
    """
    """

    def getSchema():
        """
        Return base register schema + TTW Fields
        """
