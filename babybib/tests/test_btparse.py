""" Testing btparse module
"""

from ..btparse import BibTeXParser, BibTeXEntries as BTE, Macro

from nose.tools import assert_true, assert_equal, assert_raises

parser = BibTeXParser()

def test_comment():
    assert_equal(parser.parse('test/n   @comment some text'),
                 BTE())


def test_preamble_macro():
    assert_equal(parser.parse('@string{TEst = 1989}'),
                 BTE(defined_macros=dict(test=['1989'])))
    assert_equal(parser.parse('@preamble{"some text"}'),
                 BTE(preamble=['some text']))
    assert_equal(parser.parse('@string{TEst="a macro"}'
                              '@preamble("some text" # test)'
                              '@preamble{"more text"}'),
                BTE(defined_macros=dict(test=['a macro']),
                    preamble = ['some text', 'a macro', 'more text']))
    # Macro not defined
    res = parser.parse("@preamble(a_macro)")
    exp_macro = Macro('a_macro')
    assert_equal(res,
                 BTE(undefined_macros=dict(a_macro=[[exp_macro]]),
                     preamble=[exp_macro]))


def test_preamble_error():
    res = parser.parse("""@preamble(two words)
                       @entry(Me2012, author="Me")
                       """)
    assert_equal(res, BTE({'Me2012': {'author': ['Me'],
                                      'entry type': 'entry'}}))


def test_macro_error():
    res = parser.parse("""@string(two words)
                       @entry(Me2012, author="Me")
                       """)
    assert_equal(res, BTE({'Me2012': {'author': ['Me'],
                                      'entry type': 'entry'}}))


def test_entry_error():
    res = parser.parse("""@some_entry(two words)
                       @entry(Me2012, author="Me")
                       """)
    assert_equal(res, BTE({'Me2012': {'author': ['Me'],
                                      'entry type': 'entry'}}))
    res = parser.parse("""@some_entry(akey, words)
                       @entry(Me2012, author="Me")
                       """)
    assert_equal(res, BTE({'Me2012': {'author': ['Me'], 'entry type': 'entry'},
                           'akey': {'entry type': 'some_entry'}}))
    res = parser.parse('@entry(key, author="Me", bad text)')
    assert_equal(res,
                 BTE({'key': {'author': ['Me'], 'entry type': 'entry'}}))
    # later bad something does not wipe out earlier good
    res = parser.parse('@entry(key,author="Me")\n@2thou(something)')
    assert_equal(res,
                 BTE({'key': {'author': ['Me'], 'entry type': 'entry'}}))
    # Early errors in entry definition - only citekey valid
    res = parser.parse('@entry(key,))')
    assert_equal(res, BTE({'key': {'entry type': 'entry'}}))
    # Entries survive later invalid entries
    res = parser.parse('@entry(key,) @2thou(key2,)')
    assert_equal(res, BTE({'key': {'entry type': 'entry'}}))


def test_lexer_reset():
    # With a trailing bad bracket, the lexer used to get out of sync
    res = parser.parse("@preamble(a_macro}")
    # This generated a syntax error because of the bad } above.
    res = parser.parse('@an_entry{Me2014, author="Myself"}')
    assert_equal(len(res.entries), 1)


def test_entries():
    assert_equal(parser.parse('@an_entry{Me2014, author="Myself"}'),
                 BTE({'Me2014':
                      {'author': ['Myself'], 'entry type': 'an_entry'}}))
    # Optional comma
    assert_equal(parser.parse('@an_entry{Me2014, author="Myself",}'),
                 BTE({'Me2014':
                      {'author': ['Myself'], 'entry type': 'an_entry'}}))
    # Can be enclosed by comments, and contain numeric fields.  Field names
    # converted to lower case
    res = parser.parse("""
                       Some text
                       @another_entry{Me2014,
                       AUTHOR={Myself},
                       YEAR=1989
                       }
                       @comment text
                       """)
    assert_equal(res,
                 BTE({'Me2014': {'author': ['Myself'],
                             'entry type': 'another_entry',
                             'year': ['1989']}}))
    # Can be empty
    assert_equal(parser.parse(''), BTE())
    # Have parentheses (and entry types are converted to lower case)
    assert_equal(parser.parse('@EnTrY(2012, author="me")'),
                              BTE({'2012':
                                   {'author': ['me'],
                                    'entry type': 'entry'}}))
    # Strings can be nested
    assert_equal(parser.parse('@entry(2012, author="me {too}")'),
                 BTE({'2012': {'author': ['me ', ['too']],
                           'entry type': 'entry'}}))
    # Be in single curlies
    assert_equal(parser.parse('@entry(2012, author={me})'),
                 BTE({'2012': {'author': ['me'],
                           'entry type': 'entry'}}))
    # Nested curlies
    assert_equal(parser.parse('@entry(2012, author={me {too {nested}}})'),
                 BTE({'2012': {'author': ['me ',['too ', ['nested']]],
                           'entry type': 'entry'}}))
    # Macro substitution
    assert_equal(parser.parse("""
                              @string{myname="Myself"}
                              @entry(2012, author={me } # myname)"""),
                 BTE({'2012': {'author': ['me ', 'Myself'],
                               'entry type': 'entry'}},
                    defined_macros=dict(myname='Myself')))
