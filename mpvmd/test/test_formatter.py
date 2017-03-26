from mpvmd import formatter
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
    actual_output = formatter.format_templates(format_str, templates)
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
    with pytest.raises(formatter.FormatError):
        formatter.format_templates(format_str, {})


@pytest.mark.parametrize('seek_str,expected_time,expected_mode', [
    ('0',         0,     formatter.SeekMode.ABSOLUTE),
    ('0.5',       0.5,   formatter.SeekMode.ABSOLUTE),
    ('1',         1,     formatter.SeekMode.ABSOLUTE),
    ('90',        90,    formatter.SeekMode.ABSOLUTE),
    ('00:00',     0,     formatter.SeekMode.ABSOLUTE),
    ('00:00.5',   0.5,   formatter.SeekMode.ABSOLUTE),
    ('00:01',     1,     formatter.SeekMode.ABSOLUTE),
    ('01:00',     60,    formatter.SeekMode.ABSOLUTE),
    ('01:01:01',  3661,  formatter.SeekMode.ABSOLUTE),
    ('+0',        0,     formatter.SeekMode.RELATIVE),
    ('+0.5',      0.5,   formatter.SeekMode.RELATIVE),
    ('+1',        1,     formatter.SeekMode.RELATIVE),
    ('+90',       90,    formatter.SeekMode.RELATIVE),
    ('+00:00',    0,     formatter.SeekMode.RELATIVE),
    ('+00:00.5',  0.5,   formatter.SeekMode.RELATIVE),
    ('+00:01',    1,     formatter.SeekMode.RELATIVE),
    ('+01:00',    60,    formatter.SeekMode.RELATIVE),
    ('+01:01:01', 3661,  formatter.SeekMode.RELATIVE),
    ('-0',        0,     formatter.SeekMode.RELATIVE),
    ('-0.5',      -0.5,  formatter.SeekMode.RELATIVE),
    ('-1',        -1,    formatter.SeekMode.RELATIVE),
    ('-90',       -90,   formatter.SeekMode.RELATIVE),
    ('-00:00',    0,     formatter.SeekMode.RELATIVE),
    ('-00:00.5',  -0.5,  formatter.SeekMode.RELATIVE),
    ('-00:01',    -1,    formatter.SeekMode.RELATIVE),
    ('-01:00',    -60,   formatter.SeekMode.RELATIVE),
    ('-01:01:01', -3661, formatter.SeekMode.RELATIVE),
    ('0%',        0,     formatter.SeekMode.ABSOLUTE_PERCENT),
    ('0.5%',      0.5,   formatter.SeekMode.ABSOLUTE_PERCENT),
    ('1%',        1,     formatter.SeekMode.ABSOLUTE_PERCENT),
    ('100%',      100,   formatter.SeekMode.ABSOLUTE_PERCENT),
    ('+0%',       0,     formatter.SeekMode.RELATIVE_PERCENT),
    ('+0.5%',     0.5,   formatter.SeekMode.RELATIVE_PERCENT),
    ('+1%',       1,     formatter.SeekMode.RELATIVE_PERCENT),
    ('+100%',     100,   formatter.SeekMode.RELATIVE_PERCENT),
    ('-0%',       0,     formatter.SeekMode.RELATIVE_PERCENT),
    ('-0.5%',     -0.5,  formatter.SeekMode.RELATIVE_PERCENT),
    ('-1%',       -1,    formatter.SeekMode.RELATIVE_PERCENT),
    ('-100%',     -100,  formatter.SeekMode.RELATIVE_PERCENT),
])
def test_parse_seek_good(seek_str, expected_time, expected_mode):
    actual_time, actual_mode = formatter.parse_seek(seek_str)
    assert actual_time == expected_time
    assert actual_mode == expected_mode


@pytest.mark.parametrize('seek_str', [
    '.5',
    '.',
    '0.',
    '-101%',
    '+101%',
    '101%',
    '-%',
    '+%',
    '%',
    '-',
    '+',
])
def test_parse_seek_bad(seek_str):
    with pytest.raises(formatter.FormatError):
        formatter.parse_seek(seek_str)
