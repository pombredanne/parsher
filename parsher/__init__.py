QUOTE_TYPES = '\'"'
NEWLINE_CHARS = '\n;'
REGULAR_WHITESPACE = '\t '
WHITE_SPACE_TYPES = REGULAR_WHITESPACE + NEWLINE_CHARS

class BashScript:
    def __init__(self, path):
        self.file_path = path
        self.vars = []
        self.commands = []
        self.bufferedChars = []
        self.quoted = False
        self.quoted_type = ''
        self.in_variable_value = False
        self.segment_so_far = ''
        self.commented = False
        self.parse()

    def parse(self):
        with open(self.file_path) as f:
            while True:
                # handle various look ahead(s) that we need
                if not self.bufferedChars:
                    c = f.read(1)
                else:
                    c = self.bufferedChars.pop(0)
                if not c:
                    self.done(c)
                    break

                # Handle States
                elif self.commented:
                    if c == '\n':
                        self.commented = False
                    else:
                        pass

                elif self.quoted:
                    if c == self.quoted_type:
                        # handle escaped quotes in quoted strings
                        if self.segment_so_far[-1] == '\\':
                            self.segment_so_far += c
                        else:
                            self.segment_so_far += c
                            self.quoted = False
                    else:
                        self.segment_so_far += c

                # STATE CHANGES
                elif c in QUOTE_TYPES and not self.quoted:
                    self.quoted = True
                    self.quoted_type = c
                    self.segment_so_far += c

                elif c in WHITE_SPACE_TYPES and not self.quoted and self.in_variable_value:
                    # we want to only split on variables... commands should be strung together more
                    look_ahead_1 = f.read(1)
                    if look_ahead_1 == '\\':
                        look_ahead_2 = f.read(2)
                        if look_ahead_2 == '\n':
                            pass
                    else:
                        self.bufferedChars.append(look_ahead_1)

                    self.segment_so_far += c
                    self.done(c)


                elif c == '#':
                    self.commented = True

                # found variable assignment
                elif c == '=' and not self.in_variable_value:
                    self.segment_so_far += c
                    self.in_variable_value = True
                    identifier_assignment, previous_command = self.handle_previous_commands(c)
                    if previous_command:
                        if previous_command.strip(WHITE_SPACE_TYPES):
                            self.commands += [previous_command.strip(WHITE_SPACE_TYPES)]
                    self.segment_so_far = identifier_assignment

                elif c in WHITE_SPACE_TYPES and not self.quoted and not self.in_variable_value:
                    # backslash newline at end of line
                    look_ahead_1 = f.read(1)
                    # we see an escaped char in front...

                    if look_ahead_1 == '\\':
                        print 'lookahead 1 hit'
                        look_ahead_2 = f.read(1)
                        if look_ahead_2 in '\n':
                            print 'lookahead 2 hit'
                            # ok this is the pattern "blah\s\\n"
                            # drop all 3 chars on the floor, we don't need to keep them
                            self.segment_so_far += c
                            pass
                        else:
                            # we found a pattern "blah \c" odd, but ok ...
                            self.bufferedChars.append(look_ahead_1)
                            self.bufferedChars.append(look_ahead_2)

                    elif c in NEWLINE_CHARS:
                        # This is just a newline
                        # Because not quoted and we're not in a variable value, this is probably a command and its done
                        # we keep all the args together, cause reasons...
                        self.bufferedChars.append(look_ahead_1)
                        self.done(c)
                    else:
                        # This is just a space followed by a non newline char
                        # because we're not quoted and we're not in a variable value
                        # we keep all the args together, cause reasons...
                        self.bufferedChars.append(look_ahead_1)
                        self.segment_so_far += c
                else:
                    self.segment_so_far += c

    def done(self, c):
        # variable assignment on this
        if '=' in self.segment_so_far and self.in_variable_value:
            var_name = self.segment_so_far.split('=', 1)[0]
            var_value = self.segment_so_far.split('=', 1)[1].strip(WHITE_SPACE_TYPES)
            self.vars += [[var_name, var_value]]
            self.in_variable_value = False
            self.segment_so_far = ''
        # end of a command
        elif not self.quoted and not self.in_variable_value:
            possible_command = self.segment_so_far.strip(WHITE_SPACE_TYPES)
            if possible_command:
                self.commands += [possible_command]
            self.segment_so_far = ''
        # done with file
        elif not c:
            possible_command = self.segment_so_far.strip(WHITE_SPACE_TYPES)
            if possible_command:
                self.commands += [possible_command]
            self.segment_so_far = ''

    def handle_previous_commands(self, c):
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
                #      the actual var name   the command preceding that
                return str_reverse(result), str_reverse(reversed_segment[index+1:])
            else:
                result += revc
        return str_reverse(result), None


def str_reverse(string):
    arr = []
    for each in string:
        arr += [each]
    arr.reverse()
    return ''.join(arr)
