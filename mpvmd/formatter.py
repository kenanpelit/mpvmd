from typing import Optional, Dict
import parsimonious


_GRAMMAR = r"""
    expression  = (token/alternative)*
    token       = group/raw_text/variable
    group       = group_start (alternative/token)* group_end
    alternative = token("|"token)+
    raw_text    = word
    variable    = "%"word"%"

    word        = ~"[^%\[\]\|]+"i
    group_start = "["
    group_end   = "]"
"""


class FormatError(ValueError):
    pass


def flatten(items):
    if not isinstance(items, (list, tuple)):
        return [items]
    return [
        i for sublist in items
        for i in flatten(sublist)
    ]


class EntryParser(parsimonious.nodes.NodeVisitor):
    def __init__(self, templates):
        self.templates = templates

    def visit_expression(self, _node, visited_children):
        flattened = flatten(visited_children)
        return ''.join(
            child
            for child in flattened
            if child)

    def visit_group(self, _node, visited_children):
        flattened = flatten(visited_children)
        return (
            ''.join(flattened)
            if all(flattened)
            else '')

    def visit_alternative(self, _node, visited_children):
        flattened = flatten(visited_children)
        for child in flattened:
            if child:
                return child
        return ''

    def visit_variable(self, node, _visited_children):
        var_name = node.children[1].text
        return self.templates.get(var_name, '')

    def visit_raw_text(self, node, _visited_children):
        return node.text

    def visit_word(self, node, _visited_children):
        return node.text

    def generic_visit(self, _node, visited_children):
        return visited_children


def format_templates(format_str: str, templates: Dict[str, str]) -> str:
    try:
        ast = parsimonious.Grammar(_GRAMMAR).parse(format_str)
        return EntryParser(templates).visit(ast)
    except (
            parsimonious.exceptions.ParseError,
            parsimonious.exceptions.IncompleteParseError):
        raise FormatError('Bad format string')


def format_duration(seconds: Optional[float]) -> Optional[str]:
    if seconds is None:
        return None
    seconds = int(seconds)
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    if hours:
        return '{:02}:{:02}:{:02}'.format(hours, minutes, seconds)
    return '{:02}:{:02}'.format(minutes, seconds)
