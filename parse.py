#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patrick Lewis for COMP 431 Spring 2026
HW2: More Baby-steps Towards the Construction of an SMTP Server
"""

import sys

class ParserState:
    """
    Class that will operate like a state machine to keep track of what command
    is being handled next.
    """
    # Call parser.mail_from_cmd() first
    EXPECTING_MAIL_FROM = 0
    EXPECTING_RCPT_TO = 1
    EXPECTING_RCPT_TO_OR_DATA = 2
    EXPECTING_DATA_END = 3

    def __init__(self, parser: Parser = None):
        self.state = ParserState.EXPECTING_MAIL_FROM
        self.parser = parser
        self.email_addresses = []
        self.email_text = ""

    def get_state(self) -> int:
        return self.state

    def add_email_address(self):
        if self.state in (ParserState.EXPECTING_RCPT_TO, ParserState.EXPECTING_RCPT_TO_OR_DATA):
            email_address = self.parser.get_email_address()
            self.email_addresses.append(email_address)

    def add_line_to_email(self):
        # Deal with special lines first
        if self.state == self.EXPECTING_MAIL_FROM:
            from_line = self.parser.get_from_line_for_email()
            self.add_email_address()
            self.email_text += from_line + "\n"
            return

        if self.state in (self.EXPECTING_RCPT_TO, self.EXPECTING_RCPT_TO_OR_DATA):
            # Stop here if we do not read a RCPT TO line
            to_line = self.parser.get_to_line_for_email()
            self.add_email_address()
            self.email_text += to_line + "\n"
            return

        if self.state == self.EXPECTING_DATA_END and self.parser.rewind() and \
            self.parser.data_end_cmd():
            return

        self.email_text += self.parser.input_string + "\n"

    def is_cmd_expected(self) -> bool:
        return self.state == ParserState.EXPECTING_MAIL_FROM or \
        self.state == ParserState.EXPECTING_RCPT_TO or \
        self.state == ParserState.EXPECTING_RCPT_TO_OR_DATA

    def reset(self):
        self.state = ParserState.EXPECTING_MAIL_FROM
        self.email_addresses = []
        self.email_text = ""

    def advance(self):
        if self.state < ParserState.EXPECTING_DATA_END:
            self.state += 1
            return

        self.reset()


class ParserError(Exception):
    """
    Raised when a parsing error occurs. With HW2, whenver the first parsed
    token(s) on an input line do not match the literal string(s) in the
    production rule for any message in the grammar, a type 500 error message
    is generated. Operationally, a 500 error means that your parser could not
    uniquely recognize which SMTP message it should be parsing.

    If the correct message token(s) are recognized (i.e., your parser "knows"
    what message it's parsing), but some other error occurs on the line, a type
    501 error message is generated.
    """
    def __init__(self, error_no: int):

        self.COMMAND_UNRECOGNIZED = 500
        self.SYNTAX_ERROR_IN_PARAMETERS = 501
        self.BAD_SEQUENCE_OF_COMMANDS = 503

        self.error_no = error_no

        super().__init__(self.get_error_message())

    def get_error_message(self) -> str:
        """
        Returns the error message corresponding to the error number.
        """

        if self.error_no == 501:
            return "501 Syntax error in parameters or arguments"

        if self.error_no == 503:
            return "503 Bad sequence of commands"

        # Assume 500 for anything else
        return "500 Syntax error, command unrecognized"


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
        self.BEGINNING_POSITION = 0
        self.position = self.BEGINNING_POSITION
        """
        A constant representing when the position has reached the end of the input string.
        """
        self.OUT_OF_BOUNDS = len(input_string)

    def get_email_address(self) -> str:
        """
        Extracts and returns the email address from the input string.
        """

        start_index = self.input_string.find("<") + 1
        end_index = self.input_string.find(">", start_index)
        return self.input_string[start_index:end_index].strip()


    def get_address_line_for_email(self, string_literal: str) -> str:
        """
        Extracts and returns an address line for email based on the provided
        string literal ("FROM:" or "TO:") from a command line.
        """

        if not self.is_at_end() or not string_literal or string_literal not in self.input_string:
            raise ValueError(f"Input string does not contain '{string_literal}' literal.")

        start_index = self.input_string.find(string_literal) + len(string_literal)
        end_index = self.input_string.find(">", start_index) + 1
        return f"{string_literal[:-1].capitalize()}: {self.input_string[start_index:end_index].strip()}"

    def get_from_line_for_email(self) -> str:
        """
        Extracts and returns "From: <reverse-path>"from a "MAIL FROM:" command line.
        Assumes that the line has already been successfully parsed.
        """

        # I think there is an easy way to do this without rewinding the parser.
        return self.get_address_line_for_email("FROM:")
        # from_literal = "FROM:"

        # if not self.is_at_end() or from_literal not in self.input_string:
        #     raise ValueError("Input string does not contain 'FROM:' literal.")

        # start_index = self.input_string.find(from_literal) + len(from_literal)
        # end_index = self.input_string.find(">", start_index) + 1
        # return f"From: {self.input_string[start_index:end_index].strip()}"

    def get_to_line_for_email(self) -> str:
        """
        Extracts and returns "To: <forward-path-n>" from a "RCPT TO:" command line.
        """

        return self.get_address_line_for_email("TO:")

    def print_success(self) -> bool:
        """
        Prints the success message when a line is successfully parsed.
        """

        print("250 OK")

        return True

    def current_char(self) -> str:
        """
        Returns the current character that the parser is looking at.
        """

        if self.position >= self.OUT_OF_BOUNDS:
            return ""
        return self.input_string[self.position]

    def advance(self):
        """
        Advances the "cursor" for the parser forward by one character.
        """

        if self.is_at_end():
            return

        self.position += 1

    def is_at_end(self) -> bool:
        """
        Returns True if the parser has reached the end of the input string.
        """
        return self.position >= self.OUT_OF_BOUNDS

    def mail_from_cmd(self) -> bool:
        """
        The <mail-from-cmd> non-terminal serves as the entry point for the
        parser. In other words, this non-terminal handles the entire
        "MAIL FROM:" command.

        <mail-from-cmd> ::= "MAIL" <whitespace> "FROM:" <nullspace> <reverse-path> <nullspace> <CRLF>
        """
        if not self.match_chars("MAIL"):
            raise ParserError(ParserError.COMMAND_UNRECOGNIZED)
        self.whitespace()
        if not self.match_chars("FROM:"):
            raise ParserError(ParserError.COMMAND_UNRECOGNIZED)
        self.nullspace()
        self.reverse_path()
        self.nullspace()
        if not self.crlf():
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        # If we reach here, the line was successfully parsed
        self.print_success()

    def rcpt_to_cmd(self):
        """
        The <rcpt-to-cmd> non-terminal handles the "RCPT TO:" command.

        <rcpt-to-cmd> ::= "RCPT" <whitespace> "TO:" <nullspace> <forward-path> <nullspace> <CRLF>
        """

        if not self.match_chars("RCPT"):
            raise ParserError(ParserError.COMMAND_UNRECOGNIZED)
        self.whitespace()
        if not self.match_chars("TO:"):
            raise ParserError(ParserError.COMMAND_UNRECOGNIZED)
        self.nullspace()
        self.forward_path()
        self.nullspace()
        if not self.crlf():
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        # If we reach here, the line was successfully parsed
        self.print_success()

    def data_cmd(self):
        """
        The <data-cmd> non-terminal handles the "DATA" command.

        <data-cmd> ::= "DATA" <nullspace> <CRLF>
        """

        # This is an example of a literal string in a production rule
        # If an error occurs here, it is a 500 error
        if not self.match_chars("DATA"):
            raise ParserError(ParserError.COMMAND_UNRECOGNIZED)
        self.nullspace()
        if not self.crlf():
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        # If we reach here, the line was successfully parsed
        print("354 Start mail input; end with <CRLF>.<CRLF>")

    def data_read_msg_line(self):
        """
        Handles the reading of mail input lines after a successful DATA command.
        """

        # This means to loop until we match <CRLF>.<CRLF>, or until we
        # encounter an invalid character.
        while not (self.crlf() and self.match_chars(".") and self.crlf()):
            # What characters are allowed here?
            # There are no limits or constraints on what, how much text can be
            # entered after a correct DATA message other than we'll assume that
            # text is limited to printable text, whitespace, and newlines.
            if (not self.match_ascii_printable() and not self.whitespace()
                and not self.crlf()):
                raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        return True


    def data_end_cmd(self):
        """
        The <data-end-cmd> non-terminal handles the end of mail input,
        represented by a line containing only a period. Keep in mind that
        <data-cmd> has its own <CRLF> before this non-terminal.

        <data-end-cmd> ::= "." <CRLF>
        """

        # The line must begin with a period and nothing else
        # The beginning of a new line implies <CRLF> as defined by the
        # production rule.
        if not self.position == self.BEGINNING_POSITION:
            return False

        if not (self.match_chars(".") and self.crlf()):
            return False

        return self.print_success()

    def is_ascii(self, char: str) -> bool:
        """
        Checks if a character is an ASCII character.

        :param self: Description
        :param char: The character to check.
        :return: True if the character is ASCII, False otherwise.
        :rtype: bool
        """
        if self.is_at_end():
            return False

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
        if self.is_at_end():
            return False

        return 32 <= ord(char) <= 126

    def match_ascii_printable(self) -> bool:
        """
        Attempts to match a single ASCII printable character. If it matches,
        then advance the parser's position by one.
        """

        if self.is_at_end():
            return False

        if not self.is_ascii_printable(self.current_char()):
            return False

        self.advance()
        return True

    def rewind(self, new_position: int) -> bool:
        """
        Rewinds the parser's position to a specified index.

        :param self: Description
        :param new_position: The position to rewind to.
        """

        if not (self.BEGINNING_POSITION <= new_position <= self.OUT_OF_BOUNDS):
            raise ValueError(f"""new_position must be within the bounds of the input string.
                             actual: {new_position}, expected: [0, {self.OUT_OF_BOUNDS - 1}]""")

        self.position = new_position

        return True


    def reset_parser(self):
        """
        Resets the parser's position to the beginning of the input string.
        """

        return self.rewind(self.BEGINNING_POSITION)

    def match_chars(self, expected: str) -> bool:
        """
        Attempts to match a sequence of characters in the input string. This is
        good for matching fixed strings like "MAIL", "FROM:", "<", ">", etc.
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
        """

        if not self.sp():
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

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
        """

        return self.is_path()

    def forward_path(self):
        """
        The function that handles the <forward-path> non-terminal.
        """
        return self.is_path()

    def domain(self) -> bool:
        """
        The function that handles the <domain> non-terminal, which is:
        <domain> ::= <element> | <element> "." <domain>
        """

        start = self.position
        original_start = self.position

        if not self.element():
            # print("Domain element failed")
            self.rewind(start)
            return False

        # Update the starting position since this succeeded!
        start = self.position

        # print(f"element matched; current position is {self.position}, start: {start}, original_start: {original_start}, char is {self.current_char()}")

        if not self.match_chars("."):
            # Since there is no period, rewind and stop here
            # print("Domain period not found, rewinding")
            self.rewind(start)
            return True

        # print(f"Domain period is found; saved position is {start}")

        # Since there is a period, see if there is another element. If not,
        # rewind again and return True. We are rewinding to before the period
        # since the period by itself is not enough for the "right-side" of the
        # "or" operator in the <domain> non-terminal. Calling this checks
        # for another element after the period.
        if not self.domain():

            self.rewind(start)
            # print(f"Rewinding after failed domain check; current position is {self.position}, start: {start}")
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
        if not self.letter():
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        return True

    def name(self):
        """
        The function that handles the <name> non-terminal, which is:
        <letter> <let-dig-str>
        """

        return self.letter() and self.let_dig_str()

    def let_dig_str(self) -> bool:
        """
        The function that handles the <let-dig-str> non-terminal. This works
        just like the <whitespace> non-terminal, where at least 1 letter or
        digit is required.
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

    def is_path(self) -> bool:
        """
        Docstring for is_path

        :param self: Description
        :return: Description
        :rtype: bool
        """

        start = self.position

        if not self.match_chars("<"):
            self.rewind(start)
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        if not self.mailbox():
            self.rewind(start)
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        if not self.match_chars(">"):
            self.rewind(start)
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        return True

    def mailbox(self) -> bool:
        """
        Function for <mailbox>. Is allowed to generate errors under the error detection rule
        defined in HW1 writeup.

        :param self: Description
        :return: Description
        :rtype: bool
        """

        start = self.position

        if not self.local_part():
            self.rewind(start)
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        if not self.match_chars("@"):
            self.rewind(start)
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        if not self.domain():
            self.rewind(start)
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        return True

    def local_part(self) -> bool:
        """
        Seems to be an alias for <string>.

        :param self: Description
        :return: Description
        :rtype: bool
        """

        return self.is_string()


    def is_string(self) -> bool:
        """
        Function for the <string> non-terminal. This seems to mean
        "one or more <char> characters".

        :param self: Description
        :return: Description
        :rtype: bool
        """

        start = self.position
        if not self.is_char():
            self.rewind(start)
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        while self.is_char():
            pass

        return True

    def is_char(self) -> bool:
        """
        Returns True if the current character is any ASCII character except
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
        """
        special_chars = set("\n")
        if not self.char_in_set(special_chars):
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        return True

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

    state = ParserState()

    while True:
        try:
            # read one line from standard input
            # line = input()
            line = sys.stdin.readline()
            if not line or line == "":
                break

            # Create a Parser object to parse this line
            parser = Parser(line)
            print(line.strip())
            # Actually invoke the parser to start with the <mail-from-cmd> non-terminal
            if state == ParserState.EXPECTING_MAIL_FROM and parser.mail_from_cmd():
                state += 1

        except EOFError:
            # Ctrl+D (Unix) or end-of-file from a pipe
            break
        except KeyboardInterrupt:
            # Ctrl+C
            break
        except ParserError as pe:
            # "If a parsing error occurs, print it and continue to the next line."
            print(pe)
            continue
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break
