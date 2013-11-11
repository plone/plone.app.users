from plone.app.users.browser.register import JOIN_CONST
from plone.app.users.browser.register import RegistrationForm
from zope.interface import implements
from zope.schema import getFieldNames
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm


class UserRegistrationFieldsVocabulary(object):
    """Returns list of fields available for registration form.

    It gets fields from z3c.form adopted Registration form schema.
    FormExtender fields are not included.

      >>> from zope.component import queryUtility
      >>> from zope.schema.interfaces import IVocabularyFactory

      >>> name = 'plone.app.users.user_registration_fields'
      >>> util = queryUtility(IVocabularyFactory, name)

      >>> fields = util(None)
      >>> fields
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> len(fields.by_token)
      10
      >>> [k.value for k in fields] # doctest: +NORMALIZE_WHITESPACE
      ['username', 'description', 'home_page', 'email', 'password_ctl',
      'portrait', 'fullname', 'password', 'mail_me', 'location']

      >>> email = fields.by_token['email']
      >>> email.title, email.token, email.value
      ('email', 'email', 'email')

    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        # default list of Registration Form fields
        values = getFieldNames(RegistrationForm.schema)

        # make sure required minimum number of fields is present
        for val in JOIN_CONST:
            if val not in values:
                values.append(val)

        return SimpleVocabulary([SimpleTerm(v, v, v) for v in values])

UserRegistrationFieldsVocabularyFactory = UserRegistrationFieldsVocabulary()
