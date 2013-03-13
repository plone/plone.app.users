import types
import logging

import copy
from zope.component import getUtility, provideAdapter, adapter, adapts, queryUtility, provideUtility, getAllUtilitiesRegisteredFor, getUtilitiesFor
from zope.component.hooks import getSite
from zope.annotation.interfaces import IAnnotations
from zope.interface import Interface, implements
from zope import schema
from zope.schema.interfaces import IField, IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from plone.i18n.normalizer.base import baseNormalize
from plone.schemaeditor.browser.schema.traversal import SchemaContext
from z3c.form import form, button, field, validator
from plone.schemaeditor.interfaces import IFieldEditorExtender
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFCore.utils import getToolByName

from userdataschema import IUserDataSchemaProvider, SCHEMA_ANNOTATION, checkEmailAddress

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


class MemberFieldAdapter(object):
    adapts(IField)

    def __init__(self, field):
        self.field = field

    def _get_in_registration(self):
        in_registration = self.field.queryTaggedValue('in_registration', False)
        return in_registration

    def _set_in_registration(self, value):
        self.field.setTaggedValue('in_registration', value)

    in_registration = property(_get_in_registration, _set_in_registration)

    def _get_validators(self):
        validators = self.field.queryTaggedValue('validators', {})
        return validators

    def _set_validators(self, value):
        self.field.setTaggedValue('validators', value)

    validators = property(_get_validators, _set_validators)

provideAdapter(MemberFieldAdapter, provides=IMemberField)

class MemberSchemaContext(SchemaContext):
    implements(IMemberSchemaContext)

    def __init__(self, context, request):
        # be sure not to have any constraint set 
        # for data to be pickled
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
    annotations = IAnnotations(site)
    old_schema = annotations.get(SCHEMA_ANNOTATION, {})
    new_schema = object.schema._InterfaceClass__attrs
    for i in new_schema:
        # be sure to persist only persistable values
        if isinstance(new_schema[i].constraint,
                      types.FunctionType):
            delattr(new_schema[i], 'constraint')

    # store the extra schema in an annotation
    annotations[SCHEMA_ANNOTATION] = new_schema

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


def get_ttw_edited_schema(register=False):
    schema = {}
    site = getSite()
    annotations = IAnnotations(site)
    funcs = get_validators(site)
    for fe in annotations.get(SCHEMA_ANNOTATION).values():
        # dont directly deal with  the zope.schema.Field
        # as it would not be pickled as part of the
        # persistent schema later !
        f = copy.deepcopy(fe)
        schema[f.__name__] = f
        if (register
            and not f.queryTaggedValue('in_registration', False)):
            continue
        validators = f.queryTaggedValue('validators', [])
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
    return schema



def get_ttw_edited_fields(register=False):
    extraFields = field.Fields()
    schema = get_ttw_edited_schema(register=register)
    for name in schema:
        extraFields += field.Fields(schema[name])
    return extraFields


