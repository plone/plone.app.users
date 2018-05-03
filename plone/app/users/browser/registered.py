# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from zope.component import getMultiAdapter

import datetime


class RegisteredView(BrowserView):

    def expire_date(self):
        ppr = getToolByName(self.context, 'portal_password_reset')
        expire_length = datetime.timedelta(days=ppr.getExpirationTimeout())
        expiration_date = datetime.datetime.now() + expire_length
        ploneview = getMultiAdapter((self.context, self.request), name='plone')
        return ploneview.toLocalizedTime(expiration_date, long_format=1)
