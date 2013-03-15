import types
import logging
import hashlib
import copy
import traceback

from zope.component import (
    getUtility,
    provideAdapter,
    adapter,
    adapts,
    queryUtility,
    provideUtility,
    getAllUtilitiesRegisteredFor,
    getUtilitiesFor)
from zope.component.hooks import getSite
from zope.annotation.interfaces import IAnnotations
from zope.interface import Interface, implements
from zope import schema
from zope.schema.interfaces import IField, IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from z3c.form import form, button, field, validator

from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFCore.utils import getToolByName

from plone.i18n.normalizer.base import baseNormalize
from plone.memoize import ram
from plone.schemaeditor.browser.schema.traversal import SchemaContext
from plone.schemaeditor.interfaces import IFieldEditorExtender
from plone.supermodel.model import Model, finalizeSchemas, SchemaClass
from plone.supermodel.parser import IFieldMetadataHandler, parse
from plone.supermodel.serializer import serialize
from plone.supermodel.utils import ns
from plone.supermodel import loadString

from userdataschema import (
    IUserDataSchemaProvider,
    SCHEMA_ANNOTATION,
    checkEmailAddress,
    SCHEMATA_KEY,
    IUserDataBaseSchema)

USERS_NAMESPACE = 'http://namespaces.plone.org/supermodel/users'
USERS_PREFIX = 'users'
BOOLS = {'1':True, '0':False}
SPLITTER = '_//_'

logger = logging.getLogger('plone.app.users.schemaeditor')


def log(message, level='info'):
    getattr(logger, level)(message)


class IMemberField(Interface):

    in_registration = schema.Bool(
        title=_(
            u'label_also_in_registration',
            default=u'Display in registration form'),
        description=u'',
        required=False)

    validators = schema.Set(
        title=_("Validators"),
        description=_(
            u"help_userfield_validators",
            default=u'Select the validators to use on this field'),
        required=False,
        value_type=schema.Choice(
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


IN_REGISTRATION_KEY = 'in_registration'
VALIDATORS_KEY = 'validators'
class MemberFieldAdapter(object):
    adapts(IField)

    def __init__(self, field):
        self.field = field

    def _get_in_registration(self):
        in_registration = self.field.queryTaggedValue(IN_REGISTRATION_KEY, False)
        return in_registration

    def _set_in_registration(self, value):
        self.field.setTaggedValue(IN_REGISTRATION_KEY, value)

    in_registration = property(_get_in_registration, _set_in_registration)

    def _get_validators(self):
        validators = self.field.queryTaggedValue(VALIDATORS_KEY, {})
        return validators

    def _set_validators(self, value):
        self.field.setTaggedValue(VALIDATORS_KEY, value)

    validators = property(_get_validators, _set_validators)

provideAdapter(MemberFieldAdapter, provides=IMemberField)

class MemberSchemaContext(SchemaContext):
    implements(IMemberSchemaContext)

    def __init__(self, context, request):
        schema = getUtility(IUserDataSchemaProvider).getSchema()
        super(MemberSchemaContext, self).__init__(
            schema,
            request,
            name='member-fields'
        )

    def label(self):
        return _("Edit member fields")


def updateSchema(object, event):
    site = getSite()
    old_schema = get_ttw_edited_schema()

    # serialise
    snew_schema = serialize_ttw_schema(object.schema)

    # store the extra schema in an annotation
    set_schema(snew_schema)

    # load the new schema
    new_schema = get_ttw_edited_schema()

    # update portal_memberdata properties
    pm = getToolByName(site, "portal_memberdata")
    field_type_mapping = {
        "TextLine": 'text',
        "Text": 'lines',
        "Int": 'int',
        "Float": 'float',
        "Bool": 'boolean',
        "Datetime": 'date',
        "Date": 'date',
        "Choice": 'text',
        "List": 'text',
    }
    existing = pm.propertyIds()
    for field_id in new_schema.keys():
        field_type = field_type_mapping.get(
            new_schema[field_id].__class__.__name__,
            None)
        if not field_type:
            continue
        if field_id in existing:
            pm._delProperty(field_id)
        pm._setProperty(field_id, '', field_type)

    to_remove = [field_id
                 for field_id in old_schema.keys()
                 if field_id not in new_schema.keys()]
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
    register = kw.get('register', False)
    site = getSite()
    psite = '/'.join(site.getPhysicalPath())
    annotations = IAnnotations(site)
    schema = annotations.get(SCHEMA_ANNOTATION, '')
    key = hashlib.sha224(schema).hexdigest() 
    return (psite, key, register)


@ram.cache(model_key)
def get_ttw_edited_schema(register=False):
    schema = {}
    site = getSite()
    annotations = IAnnotations(site)
    funcs = get_validators(site)
    data = ''
    try:
        data = get_schema()
        oschema = load_ttw_schema(data)
        bschema = getUtility(IUserDataSchemaProvider).baseSchema
        bfields = [a for a in bschema]
        for name in oschema:
            f = oschema[name]
            if name in bfields: continue
            if (register
                and not f.queryTaggedValue(IN_REGISTRATION_KEY, False)):
                continue
            schema[name] = f
            validators = f.queryTaggedValue(VALIDATORS_KEY, [])
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
        if data:
            logger.info(traceback.format_exc())
    return schema


def get_ttw_edited_fields(register=False):
    extraFields = field.Fields()
    schema = get_ttw_edited_schema(register=register)
    for name in schema:
        extraFields += field.Fields(schema[name])
    return extraFields


class UsersMetadataSchemaExporter(object):
    """Support the security: namespace in model definitions.
    """
    implements(IFieldMetadataHandler)

    namespace = USERS_NAMESPACE
    prefix = USERS_PREFIX

    def read(self, fieldNode, schema, field):
        reg = BOOLS.get(
            fieldNode.get(
                ns('registration', self.namespace),
                '0'), False)
        val = fieldNode.get(ns('validators', self.namespace))
        regs = field.queryTaggedValue(IN_REGISTRATION_KEY, False)
        vals = field.queryTaggedValue(VALIDATORS_KEY, [])
        if reg != regs:
            field.setTaggedValue(IN_REGISTRATION_KEY, reg)
        if val:
            val = val.split(SPLITTER)
            field.setTaggedValue(VALIDATORS_KEY, val)

    def write(self, fieldNode, schema, field):
        reg = bool(field.queryTaggedValue(IN_REGISTRATION_KEY, False)) and '1' or '0'
        val = field.queryTaggedValue(VALIDATORS_KEY, [])
        fieldNode.set(ns('registration', self.namespace), reg)
        if val:
            fieldNode.set(ns('validators', self.namespace), SPLITTER.join(val))


def serialize_ttw_schema(schema=None):
    if not schema:
        schema = copy.deepcopy(get_ttw_edited_schema())
    bfields = IUserDataBaseSchema.names()
    attrs = {}
    for name in schema:
        f = schema[name]
        if name in bfields: continue
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
    return schema


def set_schema(string, site=None):
    if site is None: site = getSite()
    annotations = IAnnotations(site)
    annotations[SCHEMA_ANNOTATION] = string


