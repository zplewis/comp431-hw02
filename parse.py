#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HW1: Parsing in Python
"""

class ParserError(Exception):
    """
    Raised when a parsing error occurs.
    """
    def __init__(self, nonterminal: str):
        self.nonterminal = nonterminal
        super().__init__(f"ERROR -- {nonterminal}")


class Parser:
    """
    This will process a string and determine whether that string conforms to a
    particular grammar. Each function in this class corresponds to a
    non-terminal in the grammar.

    The professor said that this is a "context-free" grammar; what does that
    mean?

    This parser does NOT require backtracking. There won't be any ambiguities
    in this. This grammar will be LL(1). The "1" is the number of "lookahead",
    where "lookahead" represents the number of tokens (in this class,
    characters) that the parser will see in advance before making a decision.

    Based on the HW1 writeup,
    """

    def __init__(self, input_string: str):
        """
        Constructor for the Parser class.

        :param self: Description
        :param input_string: String from stdin to be parsed as a "MAIL FROM:" command.
        """
        self.input_string = input_string
        """
        The position of the "cursor", like in SQL, of the current character.
        """
        self.position = 0
        """
        A constant representing when the position has reached the end of the input string.
        """
        self.OUT_OF_BOUNDS = len(input_string)

    def current_char(self) -> str:
        """
        Returns the current character that the parser is looking at.

        :param self: Description
        :return: Description
        :rtype: str
        """

        if self.position >= self.OUT_OF_BOUNDS:
            return ""
        return self.input_string[self.position]

    def advance(self):
        """
        Advances the "cursor" for the parser forward by one character.

        :param self: Description
        """

        if self.is_at_end():
            return

        self.position += 1

    def is_at_end(self) -> bool:
        """
        Returns True if the parser has reached the end of the input string.

        :param self: Description
        :return: Description
        :rtype: bool
        """
        return self.position >= self.OUT_OF_BOUNDS

    def mail_from_cmd(self):
        """
        The <mail-from-cmd> non-terminal serves as the entry point for the
        parser.

        :param self: Description
        """
        if not self.match_chars("MAIL"):
            raise ParserError("mail-from-cmd")
        self.whitespace()
        if not self.match_chars("FROM:"):
            raise ParserError("mail-from-cmd")
        self.nullspace()

    def is_ascii(self, char: str) -> bool:
        """
        Checks if a character is an ASCII character.

        :param self: Description
        :param char: The character to check.
        :return: True if the character is ASCII, False otherwise.
        :rtype: bool
        """
        return 0 <= ord(char) <= 127

    def is_ascii_printable(self, char: str) -> bool:
        """
        Checks if a character is an ASCII printable character.
        https://www.ascii-code.com/characters/printable-characters

        32 is space. <char> will omit space based on the rule.

        :param self: Description
        :param char: The character to check.
        :return: True if the character is ASCII printable, False otherwise.
        :rtype: bool
        """
        return 32 <= ord(char) <= 126

    def rewind(self, new_position: int):
        """
        Rewinds the parser's position to a specified index.

        :param self: Description
        :param new_position: The position to rewind to.
        """

        if not (0 <= new_position <= self.OUT_OF_BOUNDS):
            raise ValueError(f"""new_position must be within the bounds of the input string.
                             actual: {new_position}, expected: [0, {self.OUT_OF_BOUNDS - 1}]""")

        self.position = new_position

    def match_chars(self, expected: str) -> bool:
        """
        Docstring for match_chars

        :param self: Description
        :param expected: Description
        :type expected: list[str]
        :return: Description
        :rtype: bool
        """

        if self.is_at_end():
            return False

        if not expected:
            raise ValueError("Expected must be a non-empty string.")

        for ch in expected:
            if not self.is_ascii(ch):
                raise ValueError("Expected character must be an ASCII character.")

            matched = self.is_ascii(self.current_char()) and self.current_char() == ch

            if not matched:
                return False

            self.advance()

        return True

    def whitespace(self):
        """
        Matches one or more <sp> characters. Since this non-terminal does
        generate a ParserError upon failure, there is no need to return a
        value.

        :param self: Description
        """

        if not self.sp():
            raise ParserError("whitespace")

        while self.sp():
            pass

    def nullspace(self):
        """
        Matches zero or more <sp> characters. Based on the video, because this
        non-terminal is in the starting rule (<i>mail-from-cmd</i>), it DOES
        generate a ParserError upon failure. After thinking about it, though,
        since this non-terminal can match zero characters, it will never fail.
        It is also NOT found in the list of non-terminals that DO generate an
        error in the HW1 writeup.

        :param self: Description
        """

        while self.sp():
            pass

    def reverse_path(self):
        """
        The function that handles the <reverse-path> non-terminal.

        :param self: Description
        """

    def domain(self) -> bool:
        """
        Docstring for domain

        :param self: Description
        :return: Description
        :rtype: bool
        """

        start = self.position
        original_start = self.position

        if not self.element():
            print("Domain element failed")
            self.rewind(start)
            return False

        # Update the starting position since this succeeded!
        start = self.position

        print(f"element matched; current position is {self.position}, start: {start}, original_start: {original_start}, char is {self.current_char()}")

        if not self.match_chars("."):
            # Since there is no period, rewind and stop here
            print("Domain period not found, rewinding")
            self.rewind(start)
            return True

        print(f"Domain period is found; saved position is {start}")

        # Since there is a period, see if there is another element. If not,
        # rewind again and return True. We are rewinding to before the period
        # since the period by itself is not enough for the "right-side" of the
        # "or" operator in the <domain> non-terminal. Calling this checks
        # for another element after the period.
        if not self.domain():

            self.rewind(start)
            print(f"Rewinding after failed domain check; current position is {self.position}, start: {start}")
            return False

        return True


    def element(self) -> bool:
        """
        The function that handles the <element> non-terminal, which is:
        <letter> | <name>

        This means that an element can be a single letter. However, it is
        possible since <name> starts with <letter> that we check for <name>
        first to get the longest match possible. For this to work, I'll need
        to account for the possibility that <name> could fail.

        :param self: Description
        :return: Description
        :rtype: bool
        """

        start = self.position

        if self.name():
            return True

        # If name failed, that means there were only 0 or 1 letters. Rewind
        # the cursor so that we can check for <letter>.
        self.rewind(start)
        return self.letter()

    def name(self):
        """
        The function that handles the <name> non-terminal, which is:
        <letter> <let-dig-str>

        :param self: Description
        """

        return self.letter() and self.let_dig_str()

    def let_dig_str(self) -> bool:
        """
        The function that handles the <let-dig-str> non-terminal. This works
        just like the <whitespace> non-terminal, where at least 1 letter or
        digit is required.

        :param self: Description
        :return: Description
        :rtype: bool
        """

        if not self.let_dig():
            return False

        while self.let_dig():
            pass

        return True

    def let_dig(self):
        """
        The function that handles the <let-dig> non-terminal.

        :param self: Description
        """

        return self.letter() or self.digit()

    def char_in_set(self, char_set: set) -> bool:
        """
        Reusable function that checks if the current character is in the
        provided set of characters. This helps reduce code duplication for a
        number of trivial non-terminals.
        """
        if self.is_at_end():
            return False

        if len(char_set) == 0:
            raise ValueError("char_set must be a non-empty set of characters.")

        if self.current_char() in char_set:
            self.advance()
            return True

        return False

    def is_string(self) -> bool:
        """
        Function for the <string> non-terminal. This seems to mean
        "one or more <char> characters".

        :param self: Description
        :return: Description
        :rtype: bool
        """

        start = self.position
        if not self.char():
            self.rewind(start)
            return False

        while self.char():
            pass

        return True

    def is_char(self) -> bool:
        """
        Returns True if the current character is any ASCII character expect
        those in <special> or those in <sp>.

        :param self: Description
        :return: Description
        :rtype: bool
        """

        start = self.position
        if self.special() or self.sp():
            self.rewind(start)
            return False

        if not self.is_ascii_printable(self.current_char()):
            return False

        self.advance()
        return True



    def sp(self) -> bool:
        """
        Matches a single space or tab (\t) character. This is one of the
        "non-trivial" non-terminals, so it would not generate a ParserError.

        :param self: Description
        :return: Description
        :rtype: bool
        """
        special_chars = set(" \t")
        return self.char_in_set(special_chars)

    def letter(self) -> bool:
        """
        Returns True if the current character is a letter (A-Z, a-z).

        :param self: Description
        :return: Description
        """

        special_chars = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        )
        return self.char_in_set(special_chars)

    def digit(self) -> bool:
        """
        Returns True if the current character is a digit (0-9).

        :param self: Description
        :return: Description
        :rtype: bool
        """

        # WARNING: Do NOT use str.isdigit because it includes more than just 0-9!
        # https://docs.python.org/3/library/stdtypes.html#str.isdigit
        special_chars = set("0123456789")
        return self.char_in_set(special_chars)

    def crlf(self) -> bool:
        """
        According to the grammar, matches a single newline character, \n.
        I suppose we don't have to worry about \r.

        :param self: Description
        :return: Description
        :rtype: bool
        """
        special_chars = set("\n")
        return self.char_in_set(special_chars)

    def special(self) -> bool:
        """
        Matches a single "special" character as defined in the HW1 writeup.

        :param self: Description
        :return: Description
        :rtype: bool
        """
        # This is a cool trick: calling set() on a string creates a unique
        # list of characters in that string
        # The slash had to be escaped for this to work, just like the double
        # quote.
        special_chars = set("<>()[]\\.,;:@\"")
        return self.char_in_set(special_chars)


if __name__ == "__main__":
    while True:
        try:
            # read one line from standard input
            line = input()

            # Create a Parser object to parse this line
            parser = Parser(line)
            print(line)
            # Actually invoke the parser to start with the <mail-from-cmd> non-terminal
            parser.mail_from_cmd()
            # parser.domain()
            # If we reach here, the line was successfully parsed
            print("Sender OK")
        except EOFError:
            # Ctrl+D (Unix) or end-of-file from a pipe
            break
        except KeyboardInterrupt:
            # Ctrl+C
            break
        except ParserError as pe:
            "If a parsing error occurs, print it and continue to the next line."
            print(pe)
            continue
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break
