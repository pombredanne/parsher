import logging

QUOTE_TYPES = '\'"'
NEWLINE_CHARS = '\n;'
REGULAR_WHITESPACE = '\t '
WHITE_SPACE_TYPES = REGULAR_WHITESPACE + NEWLINE_CHARS


class WithVariables(object):
    def __init__(self):
        self.variables = []

    def variable(self, name, value):
        self.variables.append((name, value))

class WithCommands(object):
    def __init__(self):
        self.commands = []

    def command(self, name, value):
        self.commands.append((name, value))

class Buffered(object):
    def __init__(self):
        self._buffer = []

    @property
    def buffer(self):
        return self._buffer


class BashScript(WithVariables, WithCommands, Buffered):
    def __init__(self, path_or_file):
        self.logger = logging.getLogger("Parsher")
        if hasattr(path_or_file, 'read'):
            self._file = path_or_file
        else:
            self._file = open(path_or_file, 'r')
        self.quoted = False
        self.quoted_type = ''
        self.in_variable_value = False
        self.segment_so_far = ''
        self.commented = False
        self.in_function = False
        self.parsh()

    def _add_command(self, cmd):
        stripped = cmd.strip(WHITE_SPACE_TYPES)
        if not stripped == "export":
            self.command(stripped)

    def _done(self, c):
        # variable assignment on this
        if '=' in self.segment_so_far and self.in_variable_value:
            var_name = self.segment_so_far.split('=', 1)[0]
            var_value = self.segment_so_far.split('=', 1)[1].strip(WHITE_SPACE_TYPES)
            self.variable(var_name, var_value)
            self.in_variable_value = False
            self.segment_so_far = ''
        # end of a command
        elif not self.quoted and not self.in_variable_value:
            possible_command = self.segment_so_far.strip(WHITE_SPACE_TYPES)
            if possible_command:
                self._add_command(possible_command)
            self.segment_so_far = ''
        # done with file
        elif not c:
            possible_command = self.segment_so_far.strip(WHITE_SPACE_TYPES)
            if possible_command:
                self._add_command(possible_command)
            self.segment_so_far = ''

    def _handle_previous_commands(self, c):
        am_quoted = False
        reversed_segment = str_reverse(self.segment_so_far)
        result = ""
        for index, revc in enumerate(reversed_segment):
            if revc in QUOTE_TYPES:
                am_quoted = True
                result += revc
            elif am_quoted:
                result += revc
            elif not am_quoted and revc in WHITE_SPACE_TYPES:
                #      the actual variable name   the command preceding that
                return str_reverse(result), str_reverse(reversed_segment[index + 1:])
            else:
                result += revc
        return str_reverse(result), None


    def parsh(self):
        char = ' '

        def _handle_various_look_ahead_s__that_we_need():
            if not self.buffer:
                char = f.read(1)
            else:
                char = self.buffer.pop(0)
            if not char:
                self._done(char)
                break

        def _handle_states():
            if self.commented:
                if char == '\n':
                    self.commented = False
                else:
                    pass

            elif self.quoted:
                if char == self.quoted_type:
                    # handle escaped quotes in quoted strings
                    if self.segment_so_far[-1] == '\\':
                        self.segment_so_far += char
                    else:
                        self.segment_so_far += char
                        self.quoted = False
                else:
                    self.segment_so_far += char

            elif self.in_function:
                if char == '}':
                    self.segment_so_far += char
                    self.command(self.segment_so_far)
                    self.segment_so_far = ''
                    self.in_function = False
                else:
                    self.segment_so_far += char

        def _handle_state_changes():
            if char in QUOTE_TYPES and not self.quoted:
                self.quoted = True
                self.quoted_type = char
                self.segment_so_far += char

            elif char == '{':
                self.in_function = True
                self.segment_so_far += char

            elif char in WHITE_SPACE_TYPES and not self.quoted and self.in_variable_value:
                # we want to only split on variables... commands should be strung together more
                look_ahead_1 = f.read(1)
                if look_ahead_1 == '\\':
                    look_ahead_2 = f.read(2)
                    if look_ahead_2 == '\n':
                        pass
                else:
                    self.buffer.append(look_ahead_1)

                self.segment_so_far += char
                self._done(char)

            elif char == '#':
                self.commented = True

        def _handle_variable_assignment():
            if char == '=' and not self.in_variable_value:
                self.segment_so_far += char
                self.in_variable_value = True
                identifier_assignment, previous_command = self._handle_previous_commands(char)
                if previous_command:
                    if previous_command.strip(WHITE_SPACE_TYPES):
                        self._add_command(previous_command)
                self.segment_so_far = identifier_assignment

        def _handle_white_space():
            if char in WHITE_SPACE_TYPES and not self.quoted and not self.in_variable_value:
                # backslash newline at end of line
                look_ahead_1 = f.read(1)
                # we see an escaped char in front...

                if look_ahead_1 == '\\':
                    self.logger.debug('lookahead 1 hit')
                    look_ahead_2 = f.read(1)
                    if look_ahead_2 in '\n':
                        self.logger.debug('lookahead 2 hit')
                        # ok this is the pattern "blah\s\\n"
                        # drop all 3 chars on the floor, we don't need to keep them
                        self.segment_so_far += char
                        pass
                    else:
                        # we found a pattern "blah \char" odd, but ok ...
                        self.buffer.append(look_ahead_1)
                        self.buffer.append(look_ahead_2)

                elif char in NEWLINE_CHARS:
                    # This is just a newline
                    # Because not quoted and we're not in a variable value, this is probably a command and its done
                    # we keep all the args together, cause reasons...
                    self.buffer.append(look_ahead_1)
                    self._done(char)
                else:
                    # This is just a space followed by a non newline char
                    # because we're not quoted and we're not in a variable value
                    # we keep all the args together, cause reasons...
                    self.buffer.append(look_ahead_1)
                    self.segment_so_far += char
                else:
                    self.segment_so_far += char

        with self._file as f:
            while True:
                _handle_various_look_ahead_s__that_we_need()
                _handle_states()
                _handle_state_changes()
                _handle_variable_assignment()
                _handle_white_space()

def str_reverse(string):
    arr = []
    for each in string:
        arr += [each]
    arr.reverse()
    return ''.join(arr)
