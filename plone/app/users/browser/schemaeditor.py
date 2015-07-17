import re
import logging
import hashlib

from zope.component import getUtility
from zope.component.hooks import getSite
from zope.annotation.interfaces import IAnnotations
from zope.interface import Interface, implements

from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.schemaeditor.browser.schema.traversal import SchemaContext
from plone.schemaeditor.browser.schema.listing import SchemaListing
from plone.supermodel.model import Model, finalizeSchemas, SchemaClass
from plone.supermodel.parser import IFieldMetadataHandler
from plone.supermodel.serializer import serialize
from plone.supermodel.utils import ns
from plone.supermodel import loadString
from plone.z3cform.layout import FormWrapper

from plone.app.users.schema import (
    IUserDataSchemaProvider,
    SCHEMA_ANNOTATION,
    SCHEMATA_KEY,
)


CACHE_CONTAINER = {}
USERS_NAMESPACE = 'http://namespaces.plone.org/supermodel/users'
USERS_PREFIX = 'users'
SPLITTER = '_//_'

ALLOWED_FIELDS = [
    u'zope.schema._bootstrapfields.TextLine',
    u'zope.schema._bootstrapfields.Text',
    u'zope.schema._bootstrapfields.Bool',
    u'zope.schema._bootstrapfields.Int',
    u'zope.schema._field.Float',
    u'zope.schema._field.Set',
    u'zope.schema._field.Choice',
    u'zope.schema._field.Date',
    u'zope.schema._field.Datetime',
    u'plone.namedfile.field.NamedBlobImage',
    u'zope.schema._field.URI',
]
field_type_mapping = {
    "ProtectedEmail": 'string',
    "ProtectedTextLine": 'string',
    "TextLine": 'string',
    "Text": 'text',
    "Bool": 'boolean',
    "Int": 'int',
    "Float": 'float',
    "Set": 'lines',
    "Choice": 'string',
    "Date": 'date',
    "Datetime": 'date',
    "NamedBlobImage": '__portrait__',
    "URI": 'text',
}

DEFAULT_VALUES = {
    'text': '',
    'int': 0,
    'float': 0.0,
    'boolean': False,
}

re_flags = re.S | re.U | re.X


def log(message,
        level='info', id='plone.app.users.browser.schemaeditor'):
    logger = logging.getLogger(id)
    getattr(logger, level)(message)


class IMemberFieldValidator(Interface):
    """Base marker for field validators"""


class IMemberSchemaContext(Interface):
    """ """


class SchemaListingPage(FormWrapper):

    form = SchemaListing
    index = ViewPageTemplateFile('schema_layout.pt')


def copy_schema(schema, filter_serializable=False):
    fields = {}
    for item in schema:
        if (filter_serializable and not is_serialisable_field(schema[item])):
            continue
        fields[item] = schema[item]
    oschema = SchemaClass(SCHEMATA_KEY, attrs=fields)
    # copy base tagged values
    for i in schema.getTaggedValueTags():
        oschema.setTaggedValue(
            item, schema.queryTaggedValue(i))
    finalizeSchemas(oschema)
    return oschema


class MemberSchemaContext(SchemaContext):
    implements(IMemberSchemaContext)

    label = _(u"Edit Member Form Fields")

    def __init__(self, context, request):
        schema = getUtility(IUserDataSchemaProvider).getCopyOfSchema()
        self.fieldsWhichCannotBeDeleted = ['fullname', 'email']
        self.showSaveDefaults = False
        self.enableFieldsets = False
        self.allowedFields = ALLOWED_FIELDS
        super(MemberSchemaContext, self).__init__(
            schema,
            request,
            name=SCHEMATA_KEY,
            title=_(u"Member Fields"),
        )


def updateSchema(object, event):
    snew_schema = serialize_ttw_schema(object.schema)
    applySchema(snew_schema)


def applySchema(snew_schema):
    CACHE_CONTAINER.clear()
    site = getSite()

    # get the old schema (currently stored in the annotation)
    old_schema = get_ttw_edited_schema()

    # check if more than 2 image fields:
    if snew_schema.count('NamedBlobImage') > 1:
        site.plone_utils.addPortalMessage(
            _(u'One image field maximum.'), 'error')
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
            new_schema[field_id].__class__.__name__,
            None)
        if not field_type:
            log('Unsupported field: %s (%s)' % (
                field_id,
                new_schema[field_id].__class__.__name__))
            continue
        if field_type == '__portrait__':
            continue
        if field_id in existing:
            pm._delProperty(field_id)
        pm._setProperty(
            field_id,
            DEFAULT_VALUES.get(field_type, ''),
            field_type)

    if old_schema:
        to_remove = [field_id
                     for field_id in [a for a in old_schema]
                     if field_id not in [a for a in new_schema]]
        for field_id in to_remove:
            field_type = field_type_mapping.get(
                old_schema[field_id].__class__.__name__,
                None)
            if field_type == '__portrait__':
                continue
            pm._delProperty(field_id)


def model_key(*a, **kw):
    site = getSite()
    psite = '/'.join(site.getPhysicalPath())
    annotations = IAnnotations(site)
    schema = annotations.get(SCHEMA_ANNOTATION, '')
    key = hashlib.sha224(schema).hexdigest()
    return (psite, key)


# @ram.cache(model_key)
def get_ttw_edited_schema():
    data = get_schema()
    if data:
        ttwschema = load_ttw_schema(data)
        if ttwschema is None:
            return ''
        return ttwschema
    return ''


class UsersMetadataSchemaExporter(object):
    """Support the security: namespace in model definitions.
    """
    implements(IFieldMetadataHandler)
    namespace = ns = USERS_NAMESPACE
    prefix = USERS_PREFIX
    if_attrs = (
        'min', 'max', 'order',
        'min_length', 'max_length',
        'required',
    )

    def read(self, fieldNode, schema, field):
        for attr in self.if_attrs:
            value = self.load(
                fieldNode.get(ns(attr, self.ns), None))
            if value is not None:
                setattr(field, attr, value)

    def write(self, fieldNode, schema, field):
        for attr in self.if_attrs:
            value = getattr(field, attr, None)
            if value is not None:
                v = self.serialize(value)
                fieldNode.set(ns(attr, self.ns), v)

    def load(self, value):
        listre = re.compile('(?P<type>list|set|tuple)'
                            ':(?P<list>.*)', re_flags)
        ltypes = {
            'list': list,
            'set': set,
            'tuple': tuple,
        }
        if isinstance(value, basestring):
            listm = listre.search(value)
            if value.startswith("int:"):
                value = int(value.split('int:')[1])
            elif listm:
                i = listm.groupdict()
                try:
                    tp = i["type"]
                    value = i["list"].split(SPLITTER)
                    if tp not in ['list']:
                        value = ltypes[tp](value)
                except:
                    value = []
            else:
                value = {"bool:true": True,
                         "bool:false": False}.get(value.lower(), value)
        return value

    def serialize(self, value):
        if isinstance(value, bool):
            value = value and "bool:true" or "bool:false"
        elif isinstance(value, (list, set, tuple)):
            value = u"%s:%s" % (type(value).__name__, SPLITTER.join(value))
        elif value is not None:
            value = u"int:%s" % unicode(value)
        return value


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
    bschema = getUtility(IUserDataSchemaProvider).baseSchema
    bfields = [a for a in bschema]
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
        site = getSite()
    annotations = IAnnotations(site)
    return annotations.get(SCHEMA_ANNOTATION, '')


def set_schema(string, site=None):
    if site is None:
        site = getSite()
    annotations = IAnnotations(site)
    annotations[SCHEMA_ANNOTATION] = string
