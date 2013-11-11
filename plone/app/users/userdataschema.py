from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.exceptions import EmailAddressInvalid
from Products.CMFPlone import PloneMessageFactory as _
from plone.autoform import directives as form
from plone.namedfile.field import NamedBlobImage
from zope import schema
from zope.component import getUtility
from zope.interface import Interface, implements
from plone.formwidget.namedfile.widget import NamedImageWidget
from plone.namedfile.interfaces import INamedImageField
from ZTUtils import make_query
from z3c.form.interfaces import IFieldWidget, IFormLayer
from z3c.form.widget import FieldWidget
from zope.component import adapter
from zope.interface import implementer


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
    form.widget(portrait='plone.app.users.userdataschema.PortraitFieldWidget')


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
