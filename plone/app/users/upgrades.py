import copy
from plone.app.users.browser import schemaeditor
from plone.namedfile.field import NamedBlobImage
from plone.schemaeditor.interfaces import IEditableSchema
from plone.supermodel.model import finalizeSchemas, Schema, SchemaClass
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from zope import schema
from zope.interface import Interface

import logging
log = logging.getLogger("plone.app.users:upgrade")


def copySchemaAttrs(sch):
    fields = {}
    for id in sch:
        field = copy.deepcopy(sch[id])
        field.forms_selection = [u'In User Profile']
        fields[id] = field
    return fields


class IEmpty(Schema):
    pass


class IHomePageSchema(Interface):
    """
    """

    home_page = schema.TextLine(
        title=_(u'label_homepage', default=u'Home page'),
        description=_(u'help_homepage',
                      default=u"The URL for your external home page, "
                      "if you have one."),
        required=False)


class IDescriptionSchema(Interface):
    """
    """

    description = schema.Text(
        title=_(u'label_biography', default=u'Biography'),
        description=_(u'help_biography',
                      default=u"A short overview of who you are and what you "
                      "do. Will be displayed on your author page, linked "
                      "from the items you create."),
        required=False)


class ILocationSchema(Interface):
    """
    """

    location = schema.TextLine(
        title=_(u'label_location', default=u'Location'),
        description=_(u'help_location',
                      default=u"Your location - either city and "
                      "country - or in a company setting, where "
                      "your office is located."),
        required=False)


class IPortraitSchema(Interface):
    """
    """

    portrait = NamedBlobImage(
        title=_(u'label_portrait', default=u'Portrait'),
        description=_(
            u'help_portrait',
            default=u'To add or change the portrait: click the "Browse" '
                    u'button; select a picture of yourself. Recommended '
                    u'image size is 75 pixels wide by 100 pixels tall.'
        ),
        required=False)


def upgrade_to_ttw(context):
    # the new default schema only contains fullname and email fields
    # so we put the missing ones (home_page, description, location, portrait)
    # into the ttw schema
    if schemaeditor.get_schema() == '':
        finalizeSchemas(IEmpty)
        current_ttw = IEditableSchema(IEmpty)
    else:
        current_ttw = IEditableSchema(schemaeditor.load_ttw_schema())

    attrs = copySchemaAttrs(current_ttw.schema)
    current_fields = current_ttw.schema.names()
    pm = getToolByName(context, "portal_memberdata")
    existing = pm.propertyIds()

    if 'home_page' in existing and 'home_page' not in current_fields:
        attrs.update(copySchemaAttrs(IHomePageSchema))

    if 'description' in existing and 'description' not in current_fields:
        attrs.update(copySchemaAttrs(IDescriptionSchema))

    if 'location' in existing and 'location' not in current_fields:
        attrs.update(copySchemaAttrs(ILocationSchema))

    if 'portrait' in existing and 'portrait' not in current_fields:
        attrs.update(copySchemaAttrs(IPortraitSchema))

    sch = SchemaClass(schemaeditor.SCHEMATA_KEY,
        bases=(current_ttw.schema,),
        attrs=attrs
    )
    finalizeSchemas(sch)

    xml_model = schemaeditor.serialize_ttw_schema(sch)
    schemaeditor.set_schema(xml_model)
    log.info('Old member fields migrated into TTW schema')
