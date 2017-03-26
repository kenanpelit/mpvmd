from enum import Enum
from typing import Optional, Tuple, Dict
import parsimonious


class SeekMode:
    ABSOLUTE = 'absolute'
    RELATIVE = 'relative'
    ABSOLUTE_PERCENT = 'absolute-percent'
    RELATIVE_PERCENT = 'relative-percent'


class FormatError(ValueError):
    pass


def flatten(items):
    if not isinstance(items, (list, tuple)):
        return [items]
    return [
        i for sublist in items
        for i in flatten(sublist)
    ]


def format_templates(format_str: str, templates: Dict[str, str]) -> str:
    grammar = r'''
        expression  = (token/alternative)*
        token       = group/raw_text/variable
        group       = group_start (alternative/token)* group_end
        alternative = token("|"token)+
        raw_text    = word
        variable    = "%"word"%"

        word        = ~"[^%\[\]\|]+"i
        group_start = "["
        group_end   = "]"
    '''

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

    try:
        ast = parsimonious.Grammar(grammar).parse(format_str)
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


def parse_seek(seek_str: str) -> Tuple[int, SeekMode]:
    grammar = r'''
        seek_mode  = sign? (time/fraction/integer) percent?
        time       = integer colon (integer colon)? (fraction/integer)

        fraction   = integer point integer
        integer    = ~"[0-9]+"
        sign       = "+"/"-"
        point      = "."
        percent    = "%"
        colon      = ":"
    '''

    class EntryParser(parsimonious.nodes.NodeVisitor):
        def __init__(self):
            self.mode = None
            self.value = None

        def visit_seek_mode(self, node, visited_children):
            is_relative = False
            is_percent = False
            multiplier = 1
            if visited_children[0]:
                is_relative = True
                multiplier = visited_children[0][0]
            value = visited_children[1][0]
            if visited_children[2]:
                is_percent = True
            mode = {
                (False, False): SeekMode.ABSOLUTE,
                (True, False): SeekMode.RELATIVE,
                (False, True): SeekMode.ABSOLUTE_PERCENT,
                (True, True): SeekMode.RELATIVE_PERCENT,
            }[is_relative, is_percent]
            if is_percent and value > 100:
                raise FormatError('Invalid percentage value')
            return (value * multiplier, mode)

        def visit_integer(self, node, visited_children):
            return int(node.text)

        def visit_fraction(self, node, visited_children):
            return float(node.text)

        def visit_time(self, node, visited_children):
            parts = node.text.split(':')
            ret = 0
            for part in parts:
                ret *= 60
                ret += float(part)
            return ret

        def visit_sign(self, node, visited_children):
            return int(node.text + '1')

        def generic_visit(self, _node, visited_children):
            return visited_children

    try:
        ast = parsimonious.Grammar(grammar).parse(seek_str)
        return EntryParser().visit(ast)
    except parsimonious.VisitationError as error:
        raise FormatError(str(error))
    except (
            parsimonious.exceptions.ParseError,
            parsimonious.exceptions.IncompleteParseError):
        raise FormatError('Bad format string')
