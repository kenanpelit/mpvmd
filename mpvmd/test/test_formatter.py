from mpvmd.formatter import format_templates
import pytest


@pytest.mark.parametrize('format_str,templates,expected_output', [
    ('', {}, ''),
    ('raw', {}, 'raw'),
    ('%var%', {'var': 'substitute'}, 'substitute'),
    ('prefix %var% suffix', {'var': 'infix'}, 'prefix infix suffix'),
    ('%bad%', {}, ''),
    ('%bad% suffix', {}, ' suffix'),
    ('[]', {}, ''),
    ('[%bad%]', {}, ''),
    ('[%var%]', {'var': 'substitute'}, 'substitute'),
    ('[%bad% suffix]', {}, ''),
    ('[[]]', {}, ''),
    ('prefix[%bad% discard]suffix', {}, 'prefixsuffix'),
    ('prefix[%bad%%var%]suffix', {'var': 'discard'}, 'prefixsuffix'),
    ('prefix[%bad%|infix]suffix', {}, 'prefixinfixsuffix'),
    ('prefix[infix|discard]suffix', {}, 'prefixinfixsuffix'),
    ('prefix[%bad%|%bad2%]suffix', {}, 'prefixsuffix'),
    ('prefix[%bad%|%bad2%|infix]suffix', {}, 'prefixinfixsuffix'),
    ('prefix[%bad%|%bad%|%var%]suffix', {'var': 'infix'}, 'prefixinfixsuffix'),
    ('prefix[]suffix', {}, 'prefixsuffix'),
    ('prefix[[]]suffix', {}, 'prefixsuffix'),
    ('prefix[[]|infix]suffix', {}, 'prefixinfixsuffix'),
    ('prefix[[]|[]|infix]suffix', {}, 'prefixinfixsuffix'),
])
def test_format_templates_good(format_str, templates, expected_output):
    actual_output = format_templates(format_str, templates)
    assert actual_output == expected_output


@pytest.mark.parametrize('format_str', [
    '[|]',
    '[',
    ']',
    '|',
    '%var',
    '[%var]',
])
def test_format_templates_bad(format_str):
    with pytest.raises(ValueError):
        format_templates(format_str, {})
