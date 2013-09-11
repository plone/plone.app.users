import re
import logging
import hashlib
import copy
import traceback

from zope.component import (
    getUtility,
    provideAdapter,
    adapter,
    adapts,
    provideUtility,
    getUtilitiesFor,
)
from zope.component.hooks import getSite
from zope.annotation.interfaces import IAnnotations
from zope.interface import Interface, implements
from zope import schema as mschema
from zope.schema.interfaces import IField

from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFCore.utils import getToolByName

from plone.memoize import ram
from plone.schemaeditor.browser.schema.traversal import SchemaContext
from plone.schemaeditor.interfaces import IFieldEditorExtender
from plone.supermodel.model import Model, finalizeSchemas, SchemaClass
from plone.supermodel.parser import IFieldMetadataHandler
from plone.supermodel.serializer import serialize
from plone.supermodel.utils import ns
from plone.supermodel import loadString

from userdataschema import (
    IUserDataSchemaProvider,
    SCHEMA_ANNOTATION,
    checkEmailAddress,
    SCHEMATA_KEY,
)


USERS_NAMESPACE = 'http://namespaces.plone.org/supermodel/users'
USERS_PREFIX = 'users'
VALIDATORS_KEY = 'validators'
SPLITTER = '_//_'


field_type_mapping = {
    "ASCIILine": 'text',
    "TextLine": 'text',
    "Text": 'text',
    "Int": 'int',
    "Float": 'float',
    "Bool": 'boolean',
    "Datetime": 'date',
    "Date": 'date',
    "Choice": 'text',
    "List": 'text',
}


re_flags = re.S|re.U|re.X


def log(message,
        level='info', id='plone.app.users.schemaeditor'):
    logger = logging.getLogger(id)
    getattr(logger, level)(message)


class IMemberField(Interface):

    validators = mschema.Set(
        title=_("Validators"),
        description=_(
            u"help_userfield_validators",
            default=u'Select the validators to use on this field'),
        required=False,
        value_type=mschema.Choice(
            vocabulary="plone.app.users.validators"),
    )

class IMemberFieldValidator(Interface):
    """Base marker for field validators"""

class IMemberSchemaContext(Interface):
    """ """


@adapter(IMemberSchemaContext, IField)
def get_member_field_schema(schema_context, field):
    return IMemberField

provideAdapter(
    get_member_field_schema,
    provides=IFieldEditorExtender,
    name='plone.app.users.memberfield')


class MemberFieldAdapter(object):
    adapts(IField)

    def __init__(self, field):
        self.field = field

    def _get_validators(self):
        validators = self.field.queryTaggedValue(VALIDATORS_KEY, {})
        return validators

    def _set_validators(self, value):
        self.field.setTaggedValue(VALIDATORS_KEY, value)

    validators = property(_get_validators, _set_validators)

provideAdapter(MemberFieldAdapter, provides=IMemberField)


def copy_schema(schema, filter_serializable=False):
    fields = {}
    for item in schema:
        if (filter_serializable
            and not is_serialisable_field(schema[item])):
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

    def __init__(self, context, request):
        self.baseSchema = getUtility(IUserDataSchemaProvider).getSchema()
        schema = copy_schema(self.baseSchema, filter_serializable=True)
        super(MemberSchemaContext, self).__init__(
            schema,
            request,
            name=SCHEMATA_KEY
        )

    def label(self):
        return _("Edit member fields")


def updateSchema(object, event):
    site = getSite()

    # get the old schema (currently stored in the annotation)
    old_schema = get_ttw_edited_schema()

    # serialize the current schema
    snew_schema = serialize_ttw_schema(object.schema)

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
        if field_id in existing:
            pm._delProperty(field_id)
        pm._setProperty(field_id, '', field_type)

    if old_schema:
        to_remove = [field_id
                     for field_id in [a for a in old_schema]
                     if field_id not in [a for a in new_schema]]
        for field_id in to_remove:
            pm._delProperty(field_id)


def get_validators(site=None):
    validators = {}
    if not site:
        site = getSite()
    for name, ut in getUtilitiesFor(IMemberFieldValidator, site):
        validators[name] = {
            'func': ut,
            'doc': _(ut,
                     default=getattr(ut, '__doc__', None))
        }
    return validators


# Base validators
provideUtility(checkEmailAddress,
               provides=IMemberFieldValidator,
               name='check_email')


def chain_validators(vals):
    def validate(value):
        for v in vals:
            return v(value)
    return validate

def model_key(*a, **kw):
    site = getSite()
    psite = '/'.join(site.getPhysicalPath())
    annotations = IAnnotations(site)
    schema = annotations.get(SCHEMA_ANNOTATION, '')
    key = hashlib.sha224(schema).hexdigest()
    return (psite, key)


@ram.cache(model_key)
def get_ttw_edited_schema():
    site = getSite()
    annotations = IAnnotations(site)
    funcs = get_validators(site)
    data = ''
    oschema = None
    try:
        data = get_schema()
        oschema = load_ttw_schema(data)
        for name in oschema:
            f = oschema[name]
            validators = f.queryTaggedValue(
                VALIDATORS_KEY, [])
            if not validators: validators = []
            vfuncs = []
            for v in validators:
                fval = funcs.get(v, None)
                if fval:
                    vfuncs.append(fval['func'])
                else:
                    log('Unexistant validator for %s' % v)
            if vfuncs:
                val = chain_validators(vfuncs)
                f.constraint = val
    except Exception, e:
        oschema = None
        if data:
            log(traceback.format_exc())
    return oschema


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
        try:
            val = self.load(
                fieldNode.get(
                    ns(VALIDATORS_KEY, self.ns), []))
        except:
            val = []
        field.setTaggedValue(VALIDATORS_KEY, val)
        for attr in self.if_attrs:
            value = self.load(
                fieldNode.get(ns(attr, self.ns),
                                  None))
            if value is not None:
                setattr(field, attr, value)

    def write(self, fieldNode, schema, field):
        val = field.queryTaggedValue(VALIDATORS_KEY, [])
        for attr in self.if_attrs:
            value = getattr(field, attr, None)
            if value is not None:
                v = self.serialize(value)
                fieldNode.set(ns(attr, self.ns), v)
        if val:
            fieldNode.set(ns(VALIDATORS_KEY, self.ns),
                          self.serialize(val))

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
                value = {"bool:true":True,
                         "bool:false":False}.get(
                             value.lower(), value)
        return value

    def serialize(self, value):
        if isinstance(value, bool):
            value = value  and "bool:true" or "bool:false"
        elif isinstance(value, (list, set, tuple)):
            value = u"%s:%s" % (type(value).__name__,
                                 SPLITTER.join(value))
        elif value is not None:
            value = u"int:%s" % unicode(value)
        return value

def is_serialisable_field(field):
    ret = False
    if field.__class__.__name__ in field_type_mapping:
        ret = True
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
    model = Model({SCHEMATA_KEY:smember})
    sschema = serialize(model)
    return sschema


def load_ttw_schema(string = None):
    if not string:
        string = get_schema()
    schema = loadString(string).schemata.get(SCHEMATA_KEY, None)
    return schema


def get_schema(site=None):
    if site is None: site = getSite()
    annotations = IAnnotations(site)
    schema = annotations.get(SCHEMA_ANNOTATION, '')
    # be sure to have something serialized in storage
    if not isinstance(schema, basestring):
        schema = ""
    return schema


def set_schema(string, site=None):
    if site is None: site = getSite()
    annotations = IAnnotations(site)
    annotations[SCHEMA_ANNOTATION] = string


