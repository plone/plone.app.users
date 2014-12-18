# -*- coding: utf-8 -*-
from plone.uuid.interfaces import IUUIDGenerator
from z3c.form.action import ActionErrorOccurred
from z3c.form.interfaces import WidgetActionExecutionError
from zope.component import getUtility
from zope.interface import Invalid

import zope.event


def uuid_userid_generator(data=None):
    # Generate a unique user id.  This can be used as
    # IUserIdGenerator if wanted.
    generator = getUtility(IUUIDGenerator)
    return generator()


def notifyWidgetActionExecutionError(action, widget, err_str):
    zope.event.notify(
        ActionErrorOccurred(
            action,
            WidgetActionExecutionError(widget, Invalid(err_str))
        )
    )
