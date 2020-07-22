from figcli.config.style.palette import Palette
from pygments.lexer import RegexLexer
from pygments.style import Style
from pygments.token import *


# class PromptLexer(RegexLexer):
#     name = 'prompt'
#     aliases = ['diff']
#     filenames = []
#
#     tokens = {
#         'root': [
#             (r' .*\n', Text),
#             (r'[[.*]]\n', Generic.Inserted),
#             (r'-.*\n', Generic.Deleted),
#             (r'@.*\n', Generic.Subheading),
#             (r'Index.*\n', Generic.Heading),
#             (r'=.*\n', Generic.Heading),
#             (r'.*\n', Text),
#         ]
#     }


class FigLexer(RegexLexer):
    name = 'fig'
    alias = []
    filenames = []

    tokens = {
        'root': [
            (r' ', Error),
            (r'^/$', Text),
            (r'/$', Error),
            (r'^/[\w\-_]+/[\w\-_]+/[\w\-_/]{2,}', Name),
            (r'^/[\w\-_]+/[\w\-_]+', Keyword.Namespace),
            (r'^/[\w\-_]+', Keyword.Namespace),
        ]
    }


class FiggyPygment(Style):
    default_style = ""
    styles = {
        Comment: Palette.BL_HX,
        Keyword.Namespace: f'noinherit',
        Keyword.Other: Palette.YL_HX,
        Name: Palette.GR_HX,
        Text: 'noinherit',
        Error: f'underline {Palette.RD_HX}'
    }
