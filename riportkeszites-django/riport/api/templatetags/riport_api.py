from __future__ import absolute_import, unicode_literals

from django import template
from django.utils.safestring import mark_safe

from rest_framework.templatetags.rest_framework import format_value

register = template.Library()

@register.filter
def cust_format_value(value):
    if value is None or isinstance(value, bool):
        return mark_safe('<span class="glyphicon glyphicon-%s text-%s large" aria-hidden="true"></span>' % {
            True: ('ok-sign', 'success'), False: ('remove-sign', 'danger'), None: ('question-sign', 'warning')}[value])
    return format_value(value)
