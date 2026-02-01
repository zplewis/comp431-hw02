#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patrick Lewis for COMP 431 Spring 2026
HW2: More Baby-steps Towards the Construction of an SMTP Server
"""

from pathlib import Path
import sys



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

    COMMAND_UNRECOGNIZED = 500
    SYNTAX_ERROR_IN_PARAMETERS = 501
    BAD_SEQUENCE_OF_COMMANDS = 503

    def __init__(self, error_no: int):
        self.error_no = error_no

        super().__init__(self.get_error_message())

    def get_error_message(self) -> str:
        """
        Returns the error message corresponding to the error number.
        """

        if self.error_no == self.SYNTAX_ERROR_IN_PARAMETERS:
            return "501 Syntax error in parameters or arguments"

        if self.error_no == self.BAD_SEQUENCE_OF_COMMANDS:
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

        :param input_string: String from stdin to be parsed as a "MAIL FROM:" command.
        """
        self.input_string = input_string

        self.BEGINNING_POSITION = 0
        self.position = self.BEGINNING_POSITION
        """
        The position of the "cursor", like in SQL, of the current character.
        """


        self.OUT_OF_BOUNDS = len(input_string)
        """
        A constant representing when the position has reached the end of the input string.
        """

        self.command_identified = False
        """
        A flag indicating whether the command has been identified. This does NOT mean that the
        command has been successfully parsed; it only means that the parser has gotten past the
        string literals at the beginning of the command line.
        """

        self.command_name = ""
        """
        The name of the command being parsed, e.g., "MAIL FROM", "RCPT TO", "DATA".
        """

        self.command_parsed = False
        """
        A flag indicating whether the command has been successfully parsed. To reiterate, a command
        can be identified but not successfully parsed.
        """

    def set_command_parsed(self):
        """
        Sets the command_parsed flag.
        """
        self.command_parsed = True

    def get_command_name(self) -> str:
        """
        Returns the name of the command being parsed, e.g., "MAIL FROM", "RCPT TO", "DATA".
        """

        return self.command_name

    def is_command_identified(self) -> bool:
        """
        Returns True if the command has been identified.
        """

        return self.command_identified

    def set_command_identified(self, command_name: str = ""):
        """
        Sets the command_identified flag and command_name.
        """

        self.command_identified = True
        self.command_name = command_name

    def check_for_commands(self) -> bool:
        """
        Checks the input string for known commands and sets the command_identified
        flag and command_name accordingly.
        """

        self.reset()

        # Check for MAIL FROM
        # The second part is not needed; if this non-terminal function returns true with
        # check_only=True, that means either the command was identified or identified and parsed.
        if self.mail_from_cmd(check_only=True):
            return True

        self.reset()
        if self.rcpt_to_cmd(check_only=True):
            return True

        self.reset()
        if self.data_cmd(check_only=True):
            return True

        # This means no commands have been identified, which can mean a number of things but not
        # necessarily a problem (depending on the state of the SMTP Server)
        return False


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
        string literal ("FROM:" or "TO:") from a command line. This only works if the
        command has been successfully parsed (MAIL FROM or RCPT TO).
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

    def print_success(self, msg_no: int = 250) -> bool:
        """
        Prints the success message when a line is successfully parsed.
        """

        if msg_no == 250:
            print("250 OK")

        if msg_no == 354:
            print("354 Start mail input; end with <CRLF>.<CRLF>")

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

    def raise_parser_error(self, error_no: int, check_only: bool = False):
        """
        Raises a ParserError with the given error number if check_only is False.
        """
        if not check_only:
            raise ParserError(error_no)
        return False

    def mail_from_cmd(self, check_only: bool = False) -> bool:
        """
        The <mail-from-cmd> non-terminal serves as the entry point for the
        parser. In other words, this non-terminal handles the entire
        "MAIL FROM:" command.

        <mail-from-cmd> ::= "MAIL" <whitespace> "FROM:" <nullspace> <reverse-path> <nullspace> <CRLF>
        """
        if not self.match_chars("MAIL"):
            self.raise_parser_error(ParserError.COMMAND_UNRECOGNIZED, check_only)
        self.whitespace()
        if not self.match_chars("FROM:"):
            self.raise_parser_error(ParserError.COMMAND_UNRECOGNIZED, check_only)
        # Flag that the command has been identified
        self.set_command_identified("MAIL FROM")

        # If we are only checking for command recognition, we can stop here and return
        if check_only:
            return True


        if not (self.nullspace() and self.reverse_path() and self.nullspace() and self.crlf()):
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        # If we reach here, the line was successfully parsed
        self.set_command_parsed()
        return self.print_success()

    def rcpt_to_cmd(self, check_only: bool = False):
        """
        The <rcpt-to-cmd> non-terminal handles the "RCPT TO:" command.

        <rcpt-to-cmd> ::= "RCPT" <whitespace> "TO:" <nullspace> <forward-path> <nullspace> <CRLF>
        """

        if not self.match_chars("RCPT"):
            raise ParserError(ParserError.COMMAND_UNRECOGNIZED)
        self.whitespace()
        if not self.match_chars("TO:"):
            raise ParserError(ParserError.COMMAND_UNRECOGNIZED)

        # Flag that the command has been identified
        self.set_command_identified("RCPT TO")

        # If we are only checking for command recognition, we can stop here and return
        if check_only:
            return True

        self.nullspace()
        self.forward_path()
        self.nullspace()
        if not self.crlf():
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        # If we reach here, the line was successfully parsed
        self.set_command_parsed()
        self.print_success()

    def data_cmd(self, check_only: bool = False):
        """
        The <data-cmd> non-terminal handles the "DATA" command.

        <data-cmd> ::= "DATA" <nullspace> <CRLF>
        """

        # This is an example of a literal string in a production rule
        # If an error occurs here, it is a 500 error
        if not self.match_chars("DATA"):
            raise ParserError(ParserError.COMMAND_UNRECOGNIZED)

        # Flag that the command has been identified
        self.set_command_identified("DATA")

        # If we are only checking for command recognition, we can stop here and return
        if check_only:
            return True

        self.nullspace()
        if not self.crlf():
            raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

        # If we reach here, the line was successfully parsed
        self.set_command_parsed()
        self.print_success(354)

    def data_read_msg_line(self):
        """
        Handles the reading of mail input lines after a successful DATA command.
        """

        # This means to loop until we match <CRLF>.<CRLF>, or until we
        # encounter an invalid character.
        # I think this should work because data_end_cmd() rewinds the position
        # if it fails to match.
        while not self.data_end_cmd():
            # What characters are allowed here?
            # There are no limits or constraints on what, how much text can be
            # entered after a correct DATA message other than we'll assume that
            # text is limited to printable text, whitespace, and newlines.
            if (not self.match_ascii_printable() and not self.whitespace()
                and not self.crlf()):
                return False

        return True

    def data_end_cmd(self):
        """
        The <data-end-cmd> non-terminal handles the end of mail input,
        represented by a line containing only a period. This non-terminal has
        to work with both keyboard input and reading a file.

        If reading from a file, the line will only contain a period and a newline.
        If reading from keyboard input, the user will type a period and press Enter.

        Maybe it goes like this:
        If the current position == 0 (beginning of a new line), and the next two characters are
        a period and a newline, then we have matched <data-end-cmd>.

        If the current position != 0, then we are not at the beginning of a new line. We can
        check whether <CRLF> "." <CRLF> matches from the current position.

        The reason this should work is because this function is not managing the state; it is
        only reading from the current position. This means that the code calling this function
        is responsible for calling it only after the "DATA" command has been successfully parsed.

        <data-end-cmd> ::= <CRLF> "." <CRLF>
        """

        # The line must begin with a period and nothing else
        # The beginning of a new line implies <CRLF> as defined by the
        # production rule.
        start = self.position

        if self.position == self.BEGINNING_POSITION:
            if not (self.match_chars(".") and self.crlf()):
                self.rewind(start)
                return False

            return self.print_success()

        # If we are not at the beginning of a new line, then we need to check for
        # <CRLF> "." <CRLF> from the current position.
        if not (self.crlf() and self.match_chars(".") and self.crlf()):
            self.rewind(start)
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


    def reset(self):
        """
        Resets the parser's position to the beginning of the input string.
        """

        self.command_identified = False
        self.command_name = ""
        self.command_parsed = False
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

    def whitespace(self) -> bool:
        """
        Matches one or more <sp> characters. Since this non-terminal does
        generate a ParserError upon failure, there is no need to return a
        value.
        """

        if not self.sp():
            return False

        while self.sp():
            pass

        return True

    def nullspace(self) -> bool:
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

        return True

    def reverse_path(self):
        """
        The function that handles the <reverse-path> non-terminal.
        """

        return self.is_path()

    def forward_path(self) -> bool:
        """
        The function that handles the <forward-path> non-terminal. I imagine
        that this is a separate non-terminal in case it has to change later.

        <forward-path> ::= <path>
        """
        return self.is_path()

    def domain(self) -> bool:
        """
        The function that handles the <domain> non-terminal, which is:
        <domain> ::= <element> | <element> "." <domain>
        """

        start = self.position

        if not self.element():
            # print("Domain element failed")
            self.rewind(start)
            return False

        # Update the starting position since this succeeded!
        start = self.position

        if not self.match_chars("."):
            # Since there is no period, rewind and stop here
            # print("Domain period not found, rewinding")
            self.rewind(start)
            return True

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
            return False

        return True

    def name(self) -> bool:
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

    def let_dig(self) -> bool:
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
            return False

        if not self.mailbox():
            self.rewind(start)
            return False

        if not self.match_chars(">"):
            self.rewind(start)
            return False
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
            return False

        if not self.match_chars("@"):
            self.rewind(start)
            return False
        if not self.domain():
            self.rewind(start)
            return False

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
            return False

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
            return False

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

class SMTPServer:
    """
    Class that will operate like a state machine to keep track of what command
    is being handled next.
    """
    # Call parser.mail_from_cmd() first
    EXPECTING_MAIL_FROM = 0
    EXPECTING_RCPT_TO = 1
    EXPECTING_RCPT_TO_OR_DATA = 2
    EXPECTING_DATA_END = 3

    def __init__(self):
        self.state = self.EXPECTING_MAIL_FROM
        self.to_email_addresses = []
        self.email_text = []
        self.parser = None

    def set_parser(self, current_parser: Parser):
        """
        By the time the parser is set, the line has already been read. That means,
        what we do is check the current state and act accordingly.
        """
        self.parser = current_parser

        if not isinstance(current_parser, Parser):
            raise ValueError("parser must be an instance of Parser class.")

        # Syntax errors in the message name (type 500 errors) should take precedence over all other
        # errors.
        # Out-of-order (type 503 errors) should take precedence over parameter/argument errors
        # (type 501 errors). This means that we can no longer throw a 501 error until we have
        # verified that the command is in the correct sequence.

        # We need to know if any command is recognized
        recognized_command = self.command_id_errors()
        self.parser.reset()

        # STATE == 0
        if self.state == self.EXPECTING_MAIL_FROM:
            # if the command fails, that means a type 501 error occurred.
            if not self.parser.mail_from_cmd():
                raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

            # If we made it here, the command was fully parsed successfully
            # Add the "From: <reverse-path>" line to the list of email text lines
            self.email_text.append(self.parser.get_from_line_for_email())
            return self.advance()

        if self.state == self.EXPECTING_RCPT_TO or \
            (self.state == self.EXPECTING_RCPT_TO_OR_DATA and recognized_command == "RCPT TO"):
            # if the command fails, that means a type 501 error occurred.
            if not self.parser.rcpt_to_cmd():
                raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

            # If we made it here, the command was fully parsed successfully
            # Add the "To: <forward-path>" line to the list of email text lines
            self.email_text.append(self.parser.get_to_line_for_email())
            self.to_email_addresses.append(self.parser.get_email_address())

            # Only advance if this is the first time we are seeing a To: address
            if self.state == self.EXPECTING_RCPT_TO:
                self.advance()

            return

        if self.state == self.EXPECTING_RCPT_TO_OR_DATA:
            # This means that the recognized command must be "DATA", but we'll check anyway
            if recognized_command == "DATA" and not self.parser.data_cmd():
                raise ParserError(ParserError.SYNTAX_ERROR_IN_PARAMETERS)

            # If we made it here, the command was fully parsed successfully
            # Advance so that we can start reading the message
            return self.advance()

        if self.state == self.EXPECTING_DATA_END:
            # This is different because any text that does not create an error that is parsed
            # here is considered valid until the ending comes.
            if self.parser.data_end_cmd():
                self.process_email_message()
                return self.advance()

            if self.parser.data_read_msg_line():
                self.email_text.append(self.parser.input_string)

    def command_id_errors(self) -> str:
        """
        If no command is recognized, then that results in a 500 error.
        If an unexpected command is recognized based on the current state, that results in a 503.
        Return the recognized command. This is helpful for when a state represents an option,
        RCPT TO or DATA.
        """

        if self.state not in [self.EXPECTING_MAIL_FROM, self.EXPECTING_RCPT_TO, self.EXPECTING_RCPT_TO_OR_DATA]:
            return ""

        if not isinstance(self.parser, Parser):
            raise ValueError("parser must be an instance of Parser class.")

        any_command_recognized = self.parser.check_for_commands()
        recognized_command = self.parser.get_command_name()

        if not any_command_recognized or not recognized_command:
            raise ParserError(ParserError.COMMAND_UNRECOGNIZED)

        if self.state == self.EXPECTING_MAIL_FROM and recognized_command != "MAIL FROM":
            raise ParserError(ParserError.BAD_SEQUENCE_OF_COMMANDS)

        if self.state == self.EXPECTING_RCPT_TO and recognized_command != "RCPT TO":
            raise ParserError(ParserError.BAD_SEQUENCE_OF_COMMANDS)

        if self.state == self.EXPECTING_RCPT_TO_OR_DATA and recognized_command not in ["RCPT TO", "DATA"]:
            raise ParserError(ParserError.BAD_SEQUENCE_OF_COMMANDS)

        return recognized_command

    def reset(self):
        """
        Resets the SMTP server state machine to expect a new email.
        """
        self.state = self.EXPECTING_MAIL_FROM
        self.to_email_addresses = []
        self.email_text = []

    def advance(self):
        """
        Advances the state of the SMTP server by 1. If a message is completed,
        then it starts over and waits for the next one.
        """
        if self.state != self.EXPECTING_DATA_END:
            self.state += 1
            return

        self.reset()

    def create_folder(self, folder_name: str) -> Path:
        """
        Create a folder with the specified name in the same location as this
        Python script.
        """

        if not folder_name:
            raise ValueError("create_folder(); must specify a folder name")

        # This is the folder that this Python script lives in.
        current_folder = Path(__file__).resolve().parent
        # This is the "forward" folder I want to create
        new_folder = current_folder / folder_name

        new_folder.mkdir(exist_ok=True)

        return new_folder

    def process_email_message(self) -> bool:
        """
        Docstring for process_email_message
        """

        # 1. Get the text of the message
        email_complete_text = "\n".join(self.email_text)

        # 2. Create the "folder" folder
        self.create_folder("forward")

        # 3. For each recipient of the latest email message, append the text
        # of the email to a file with the email address as the name.
        for email_address in self.to_email_addresses:
            forward_path = Path(email_address)

            with forward_path.open("a", encoding="utf-8") as f:
                f.write(email_complete_text)


if __name__ == "__main__":

    server = SMTPServer()

    while True:
        try:
            # read one line from standard input
            # line = input()
            line = sys.stdin.readline()
            if not line or line == "":
                break

            # Create a Parser object to parse this line
            parser = Parser(line)

            # Pass this parser to the SMTPServer object
            server.set_parser(parser)

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
