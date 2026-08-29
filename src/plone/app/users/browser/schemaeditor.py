from plone.app.users.schema import IRegisterSchema
from plone.app.users.schema import IUserDataSchema
from plone.app.users.schema import SCHEMA_ANNOTATION
from plone.app.users.schema import SCHEMATA_KEY
from plone.base import PloneMessageFactory as _
from plone.base.interfaces import IPloneSiteRoot
from plone.supermodel import loadString
from plone.supermodel.model import finalizeSchemas
from plone.supermodel.model import Model
from plone.supermodel.model import SchemaClass
from plone.supermodel.serializer import serialize
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import get_portal
from zope.annotation.interfaces import IAnnotations
from zope.component import getGlobalSiteManager

import copy
import logging
import re
import zope.deferredimport

zope.deferredimport.initialize()

zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.schemaeditor import MemberSchemaContext instead.",
    MemberSchemaContext="plone.app.layout.users.schemaeditor:MemberSchemaContext",
)
zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.schemaeditor import SchemaListingPage instead.",
    SchemaListingPage="plone.app.layout.users.schemaeditor:SchemaListingPage",
)

ALLOWED_FIELDS = [
    "zope.schema._bootstrapfields.TextLine",
    "zope.schema._bootstrapfields.Text",
    "zope.schema._bootstrapfields.Bool",
    "zope.schema._bootstrapfields.Int",
    "zope.schema._field.Float",
    "zope.schema._field.Set",
    "zope.schema._field.Choice",
    "zope.schema._field.Date",
    "zope.schema._field.Datetime",
    "plone.namedfile.field.NamedBlobImage",
    "zope.schema._field.URI",
]
field_type_mapping = {
    "ProtectedEmail": "string",
    "ProtectedTextLine": "string",
    "TextLine": "string",
    "Text": "text",
    "Bool": "boolean",
    "Int": "int",
    "Float": "float",
    "Set": "lines",
    "Choice": "string",
    "Date": "date",
    "Datetime": "date",
    "NamedBlobImage": "__portrait__",
    "URI": "text",
}

DEFAULT_VALUES = {
    "text": "",
    "int": 0,
    "float": 0.0,
    "boolean": False,
}

re_flags = re.S | re.U | re.X


def log(message, level="info", id="plone.app.users.browser.schemaeditor"):
    logger = logging.getLogger(id)
    getattr(logger, level)(message)


def updateSchema(object, event):
    snew_schema = serialize_ttw_schema(object.schema)
    applySchema(snew_schema)


def applySchema(snew_schema):
    site = get_portal()

    # get the old schema (currently stored in the annotation)
    old_schema = get_ttw_edited_schema()

    # check if more than 2 image fields:
    if snew_schema.count("NamedBlobImage") > 1:
        site.plone_utils.addPortalMessage(_("One image field maximum."), "error")
        return

    # store the current schema in the annotation
    set_schema(snew_schema)

    # load the new schema
    new_schema = get_ttw_edited_schema()

    # update portal_memberdata properties
    pm = getToolByName(site, "portal_memberdata")
    existing = pm.propertyIds()
    for field_id in [a for a in new_schema]:
        field_type = field_type_mapping.get(
            new_schema[field_id].__class__.__name__, None
        )
        if not field_type:
            log(
                "Unsupported field: {} ({})".format(
                    field_id, new_schema[field_id].__class__.__name__
                )
            )
            continue
        if field_type == "__portrait__":
            continue
        if field_id in existing:
            pm._delProperty(field_id)
        pm._setProperty(field_id, DEFAULT_VALUES.get(field_type, ""), field_type)

    if old_schema:
        to_remove = [
            field_id
            for field_id in [a for a in old_schema]
            if field_id not in [a for a in new_schema]
        ]
        for field_id in to_remove:
            field_type = field_type_mapping.get(
                old_schema[field_id].__class__.__name__, None
            )
            if field_type == "__portrait__":
                continue
            pm._delProperty(field_id)

    invalidateSchemasInCache(site)


def get_ttw_edited_schema():
    data = get_schema()
    if data:
        ttwschema = load_ttw_schema(data)
        if ttwschema is None:
            return ""
        return ttwschema
    return ""


def is_serialisable_field(field):
    ret = False
    if field.__class__.__name__ in field_type_mapping:
        ret = True
    else:
        raise TypeError("type not serializable %s" % field.__class__.__name__)
    return ret


def serialize_ttw_schema(schema=None):
    if not schema:
        schema = get_ttw_edited_schema()
    bfields = [a for a in IUserDataSchema]
    attrs = {}
    for name in schema:
        f = schema[name]
        if is_serialisable_field(f) and name not in bfields:
            attrs[name] = f
    smember = SchemaClass(SCHEMATA_KEY, attrs=attrs)
    finalizeSchemas(smember)
    model = Model({SCHEMATA_KEY: smember})
    sschema = serialize(model)
    return sschema


def load_ttw_schema(string=None):
    if not string:
        string = get_schema()
    schema = loadString(string).schemata.get(SCHEMATA_KEY, None)
    return schema


def get_schema(site=None):
    if site is None:
        site = get_portal()
    annotations = IAnnotations(site)
    return annotations.get(SCHEMA_ANNOTATION, "")


def set_schema(string, site=None):
    if site is None:
        site = get_portal()
    annotations = IAnnotations(site)
    annotations[SCHEMA_ANNOTATION] = string


def invalidateSchemasInCache(portal):
    gsm = getGlobalSiteManager()

    schema = getattr(portal, "_v_register_schema", None)
    if schema is not None:
        from .account import AccountPanelSchemaAdapter

        gsm.unregisterAdapter(AccountPanelSchemaAdapter, (IPloneSiteRoot,), schema)
    portal._v_register_schema = None

    schema = getattr(portal, "_v_userdata_schema", None)
    if schema is not None:
        from .userdatapanel import UserDataPanelAdapter

        gsm.unregisterAdapter(UserDataPanelAdapter, (IPloneSiteRoot,), schema)
    portal._v_userdata_schema = None

    # kill volatile attributes in all threads
    portal._p_changed = 1


def getFromBaseSchema(baseSchema, form_name=None):
    attrs = copySchemaAttrs(baseSchema, form_name)
    ttwschema = get_ttw_edited_schema()
    if ttwschema:
        attrs.update(copySchemaAttrs(ttwschema, form_name))
    schema = SchemaClass(SCHEMATA_KEY, bases=(baseSchema,), attrs=attrs)
    finalizeSchemas(schema)
    return schema


def copySchemaAttrs(schema, form_name):
    return {
        a: copy.deepcopy(schema[a])
        for a in schema
        if field_in_form(schema[a], form_name)
    }


default_fields = list(IUserDataSchema.names()) + list(IRegisterSchema.names())


def field_in_form(field, form_name=None):
    if form_name is None:
        return True
    if field.__name__ in default_fields:
        return True
    forms_selection = getattr(field, "forms_selection", [])
    return form_name in forms_selection
