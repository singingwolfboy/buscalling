"""
WTForms
=======

WTForms is a flexible forms validation and rendering library for python web
development.

:copyright: Copyright (c) 2010 by Thomas Johansson, James Crasta and others.
:license: BSD, see LICENSE.txt for details.
"""
from wtforms import validators, widgets
from wtforms.fields import *
from wtforms.form import Form
from wtforms.validators import ValidationError

from wtforms.fields import __all__ as fields_all
from wtforms.widgets import __all__ as widgets_all
__all__ = fields_all + widgets_all

__version__ = '0.6.4dev'
