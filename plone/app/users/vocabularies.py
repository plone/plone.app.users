from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.site.hooks import getSite

from .browser.z3cpersonalpreferences import UserDataPanel
from .browser.register import JOIN_CONST


class UserRegistrationFieldsVocabulary(object):
    """Returns list of fields available for registration form.
    
    It gets fields from z3c.form adopted Personal Information form.
    IFormExtender fields will be included automatically if any.
    
    TODO: add tests on this vocabulary.
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        # prepare user data form fields, this is probably the only way to get
        # final list of available fields taking into account IFormExtender
        # adapters
        site = getSite()
        form = UserDataPanel(site, site.REQUEST)
        form.updateFields()
        values = [f for f in form.fields]
        
        # make sure required minimum number of fields is present
        values = list(set(values) | set(JOIN_CONST))

        return SimpleVocabulary([SimpleTerm(v, v, v) for v in values])

UserRegistrationFieldsVocabularyFactory = UserRegistrationFieldsVocabulary()
