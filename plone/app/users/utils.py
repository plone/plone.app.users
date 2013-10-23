from plone.uuid.interfaces import IUUIDGenerator
from zope.component import getUtility


def uuid_userid_generator(data=None):
    # Generate a unique user id.  This can be used as
    # IUserIdGenerator if wanted.
    generator = getUtility(IUUIDGenerator)
    return generator()
