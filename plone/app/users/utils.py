from zope.component import getUtility
import zope.event
from zope.interface import Invalid

from z3c.form.action import ActionErrorOccurred
from z3c.form.interfaces import WidgetActionExecutionError

from plone.uuid.interfaces import IUUIDGenerator


def uuid_userid_generator(data=None):
    # Generate a unique user id.  This can be used as
    # IUserIdGenerator if wanted.
    generator = getUtility(IUUIDGenerator)
    return generator()


def notifyWidgetActionExecutionError(action, widget, err_str):
    zope.event.notify(ActionErrorOccurred(action, WidgetActionExecutionError(widget, Invalid(err_str))))
