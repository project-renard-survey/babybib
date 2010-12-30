""" Parser for bibtex files """
import sys

import ply.yacc

from .btlex import tokens, lexer
from .parsers import Macro


class BibTeXEntries(object):
    def __init__(self, entries = None,
                 preamble = None,
                 defined_macros = None,
                 undefined_macros = None):
        if entries is None:
            entries = {}
        if preamble is None:
            preamble = []
        if defined_macros is None:
            defined_macros = {}
        if undefined_macros is None:
            undefined_macros = {}
        self.entries = entries
        self.preamble = preamble
        self.defined_macros = defined_macros
        self.undefined_macros = undefined_macros

    def __eq__(self, other):
        return (self.entries == other.entries and
                self.preamble == other.preamble)


class BibTeXParser(object):
    def __init__(self,
                 tabmodule='babybib.parsetab',
                 lexer=lexer,
                 tokens=tokens):
        self.tabmodule = tabmodule
        self.lexer = lexer
        self.tokens = tokens
        self.parser = ply.yacc.yacc(
            module=self,
            tabmodule=self.tabmodule)

    def parse(self, txt, debug=False):
        self._results = BibTeXEntries()
        self._results.entries = self.parser.parse(txt, lexer=self.lexer,
                                                  debug=debug)
        return self._results

    def p_start(self, p):
        """ definitions : entry
                        | throwout
                        | empty
        """
        p[0] = {}
        if not p[1] is None: # entry is tuple, others return None
            key, value = p[1]
            p[0][key] = value

    def p_empty(self, p):
        "empty :"
        pass

    def p_definitions_throwout(self, p):
        " definitions : definitions throwout "
        p[0] = p[1]

    def p_definitionss_entry(self, p):
        " definitions : definitions entry "
        p[0] = p[1]
        key, value = p[2]
        p[0][key] = value

    def p_throwouts(self, p):
        """ throwout : macro
                    | preamble
                    | IMPLICIT_COMMENT
                    | EXPLICIT_COMMENT
        """

    def p_entry(self, p):
        """ entry : AT ENTRY LBRACKET CITEKEY COMMA fieldlist RBRACKET
                | AT ENTRY LBRACKET CITEKEY COMMA fieldlist COMMA RBRACKET
        """
        # entries are (citekey, dict) tuples.  Entry types are in ENTRY, and are not
        # case senstive. They go in the fieldlist dictionary as key 'entry type'.
        # The space in the key makes it an illegal bibtex field name, so it can't
        # clash with bibtex fields.  Citekeys are case sensitive
        p[6]['entry type'] = p[2].lower()
        p[0] = (p[4], p[6])

    def p_macro(self, p):
        "macro : AT MACRO LBRACKET NAME EQUALS expression RBRACKET"
        name = p[4].lower()
        self._results.defined_macros[name] = p[6]

    def p_preamble(self, p):
        "preamble : AT PREAMBLE LBRACKET expression RBRACKET"
        self._results.preamble += p[4]

    def p_fieldlist_from_def(self, p):
        """ fieldlist : fielddef """
        # fieldef is a tuple
        p[0] = dict((p[1],))

    def p_fieldlist_from_list_def(self, p):
        """ fieldlist : fieldlist COMMA fielddef
        """
        # fielddef is a tuple, fieldlist is a dictionary
        key, value = p[3]
        p[0] = p[1]
        p[0][key] = value

    def p_fielddef(self, p):
        """ fielddef : NAME EQUALS expression"""
        p[0] = (p[1].lower(), p[3])

    def p_expr_name(self, p):
        " expression : NAME "
        # reference to a macro
        name = p[1].lower()
        d_macros = self._results.defined_macros
        if name in d_macros:
            p[0] = d_macros[name]
            return
        # Placeholder and reference to undefined macros
        p[0] = [Macro(name)]
        ud_macros = self._results.undefined_macros
        if name not in ud_macros:
            ud_macros[name] = [p[0]]
        else:
            ud_macros[name].append(p[0])

    def p_expr_number(self, p):
        """ expression : NUMBER """
        p[0] = [p[1]]

    def p_expr_string(self, p):
        """ expression : quotedstring
                    | curlystring
        """
        p[0] = p[1]

    def p_string_quoted(self, p):
        " quotedstring : QUOTE stringcontents QUOTE "
        p[0] = p[2]

    def p_string_curlied(self, p):
        " curlystring : LCURLY stringcontents RCURLY "
        p[0] = p[2]

    def p_scont_basic(self, p):
        """ stringcontents : STRING
                        | curlystring
        """
        p[0] = [p[1]]

    def p_scont_empty(self, p):
        " stringcontents : empty "
        p[0] = []

    def p_scont_appending(self, p):
        """ stringcontents : stringcontents STRING
                        | stringcontents curlystring
        """
        p[0] = p[1] + [p[2]]

    def p_expr_hash(self, p):
        """ expression : expression HASH expression """
        p[0] = p[1] + p[3]

    def p_error(self, t):
        print "Syntax error at token %s, value %s, line no %d" % (
            t.type, t.value, t.lineno)
