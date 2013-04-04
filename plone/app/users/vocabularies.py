from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.schema import getFieldNames
from zope.component import getUtility

from .browser.register import JOIN_CONST
from plone.i18n.normalizer.base import baseNormalize

from .schemaeditor import get_validators
from .userdataschema import IUserDataSchemaProvider


class UserRegistrationFieldsVocabulary(object):
    """Returns list of fields available for registration form.

    It gets fields from UserDataSchemaProvider (which includes
    TTW defined fields).

      >>> from zope.component import queryUtility
      >>> from zope.schema.interfaces import IVocabularyFactory

      >>> name = 'plone.app.users.user_registration_fields'
      >>> util = queryUtility(IVocabularyFactory, name)

      >>> fields = util(None)
      >>> fields
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> len(fields.by_token)
      10
      >>> [k.value for k in fields]
      ['username', 'description', 'home_page', 'email', 'password_ctl', 'portrait', 'fullname', 'password', 'mail_me', 'location']

      >>> email = fields.by_token['email']
      >>> email.title, email.token, email.value
      ('email', 'email', 'email')

    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        # complete list of user data form fields
        util = getUtility(IUserDataSchemaProvider)
        schema = util.getSchema()
        values = getFieldNames(schema)

        # make sure required minimum number of fields is present
        for val in JOIN_CONST:
            if val not in values:
                values.append(val)

        return SimpleVocabulary([SimpleTerm(v, v, v) for v in values])

UserRegistrationFieldsVocabularyFactory = UserRegistrationFieldsVocabulary()


class AdaptersVocabulary(object):
    """MemberField validators vocabulary"""
    implements(IVocabularyFactory)
    def __call__(self, context, key=None):
        funcs = get_validators()
        validators = dict([(a, funcs[a]['doc'])
                           for a in funcs])
        terms = [SimpleTerm(baseNormalize(validator),
                            baseNormalize(validator),
                            validators[validator])
                 for validator in validators]
        return SimpleVocabulary(terms)

AdaptersVocabularyFactory = AdaptersVocabulary()
