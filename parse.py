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

    def is_ascii(self, char: str) -> bool:
        """
        Checks if a character is an ASCII character.

        :param self: Description
        :param char: The character to check.
        :return: True if the character is ASCII, False otherwise.
        :rtype: bool
        """
        return 0 <= ord(char) <= 127

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
            raise ValueError("Input string has already been fully processed.")

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

    def sp(self) -> bool:
        """
        Matches a single space or tab (\t) character. This is one of the
        "non-trivial" non-terminals, so it would not generate a ParserError.

        :param self: Description
        :return: Description
        :rtype: bool
        """
        if self.is_at_end():
            return False

        current = self.current_char()
        if current == " " or current == "\t":
            self.advance()
            return True

        return False

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




if __name__ == "__main__":
    while True:
        try:
            # read one line from standard input
            line = input()

            # Create a Parser object to parse this line
            parser = Parser(line)
            # Actually invoke the parser to start with the <mail-from-cmd> non-terminal
            parser.mail_from_cmd()
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
