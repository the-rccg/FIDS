# -*- coding: utf-8 -*-

import dash_html_components as html


def hide_unhide_div(truth_statement, base_style={}, debug=False, show='block'):
    """ Return style with display if true """
    if truth_statement or debug:
        return {**base_style, 'display':show}
    else:
        return {**base_style, 'display':'none'}


def update_status(status, variable, text, formats=["[ ]", "[x]"]):
    """ NOTE: ugly. div does not allow: \n, linesep, <br> """
    if type(status) != list:
        status = list(status)
    if variable:
        return [*status, html.Div('{} {}: {}'.format(formats[1], text, variable))]
    else: 
        return [*status, html.Div('{} No {}'.format(formats[0], text))]
