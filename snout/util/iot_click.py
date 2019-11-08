import ast
import builtins
import sys

import click

# when forming the params at the end, discard these vars
DISCARD_VARS = ['app', 'env', 'automatic', 'protocol', 'radio']

class ProtocolArg(click.Argument):
    """Handles the Argument for the protocol to test. Also,
    calls the respective command's help screen if --help is given
    """

    def handle_parse_result(self, ctx, opts, args):
        if any(arg in ctx.help_option_names for arg in args):
            help_command = None
            for arg in args:
                if arg in ctx.command.commands:
                    help_command = arg
            for opt in opts.values():
                if opt in ctx.command.commands:
                    help_command = opt
            if help_command is None:
                print(ctx.get_help())
                sys.exit(0)
            return globals()[help_command]()
        return super(ProtocolArg, self).handle_parse_result(ctx, opts, args)


class PythonLiteralOption(click.Option):
    """Tries to evaluate the argument as a python literal

    Raises:
        click.BadParameter: if an invalid argument that cannot be evaluated as a python literal is passed
    """
    # https://stackoverflow.com/questions/47631914/how-to-pass-several-list-of-arguments-to-click-option

    def type_cast_value(self, ctx, value):
        try:
            return ast.literal_eval(value) if value else None
        except:
            raise click.BadParameter(value)


class ChannelsOption(click.Option):
    """Evaluates the option given for the --channels command

    Raises:
        click.BadParameter: Channels not in 1 of the following forms:
            All channels -- ex: "all"
            Range with hypen -- ex: "11-26"
            Range with colon -- ex: "11:26"
            Range as a list -- ex: "[11,26]"
            Single channel as INT or FLOAT -- ex: "11"

    Returns:
        {list} -- A list with [low, high] inclusive. If only one channel (c) is given, then
            it is returned in a list as [c, c]
    """

    def type_cast_value(self, ctx, value):
        try:
            if value:
                if value.lower() == 'all':
                    pass  # return normally
                elif "-" in value:
                    value = value.split("-")
                    assert len(value) == 2
                    value = (int(value[0]), int(value[1]))
                elif ":" in value:
                    value = value.split(":")
                    assert len(value) == 2
                    value = (int(value[0]), int(value[1]))
                else:
                    value = ast.literal_eval(value)
                    if isinstance(value, tuple) or isinstance(value, list):
                        if len(value) == 1:
                            # low and high are the same...value = low.extend(low)
                            value.extend(value)
                        else:
                            value = list(value)
                    elif isinstance(value, int):
                        value = [value]
                    elif isinstance(value, float):
                        value = [value]
                    else:
                        raise click.BadParameter(value)
            # should be in format of [low, high] at this point
            return value
        except:
            raise click.BadParameter(value)


def pos_callback(ctx, param, value):
    """Callback to check to make sure that the value is positive.

    Raises:
        click.BadParameter: if value <= 0

    Returns:
        value
    """
    if value > 0:
        return value
    else:
        raise click.BadParameter(value, param=param)


class IoTClick:
    """Wrapper for Click that helps to handle automatic prompt fillins
    """

    def __init__(self):
        self.automatic = []
        self.initial_automatic = []
        self.prompts = []
        self.use_automatic = False

    def __repr__(self):
        """Creates a string that starts with "--automatic" that 
        has all of the automatic arguments to fillin. This command is
        also CLI friendly (string quotes are replaces with \\" and spaces
        between entities are removed)

        Returns:
            [type] -- [description]
        """
        if self.initial_automatic:
            return "--automatic {}".format(
                str(self.initial_automatic)
                .replace(", ", ",")
                .replace("'", '\\"')  # replace quotes for CLI support
            )
        elif self.automatic:
            return "--automatic {}".format(
                str(self.automatic)
                .replace(", ", ",")
                .replace("'", '\\"')  # replace quotes for CLI support
            )
        else:
            return ""

    def exists(self):
        """Check if an automatic command exists

        Returns:
            {bool} -- True if exists, False if not
        """
        if self.automatic:
            return True
        else:
            return False

    def reset(self):
        """Resets all of the members
        """
        self.use_automatic = False
        self.automatic = []
        self.initial = []
        self.prompts = []

    def set_automatic(self, automatic):
        """Sets the automatic command list

        Arguments:
            automatic {list} -- The new automatic command list
        """
        self.use_automatic = True
        self.prompts = []
        self.automatic = automatic
        self.initial_automatic = automatic.copy()

    def get_automatic(self):
        return self.automatic

    def pop(self, ii=-1):
        """Pops from the prompts and the automatic list

        Keyword Arguments:
            ii {int} -- The index to pop (default: {-1})

        Returns:
            {tuple} -- (prompt, answer)
        """
        return (self.prompts.pop(ii), self.automatic.pop(ii))

    def add(self, prompt, answer):
        """Adds a prompt to the prompts list and an answer to the automatic list.
        If the last prompt (of index -1 in self.prompts) is equal to the prompt param,
        then replace the previous prompt/answer...otherwise, add a new entry to each
        list

        Arguments:
            prompt {str} -- The prompt for the answer
            answer {any} -- The answer given to the prompt
        """
        if self.prompts and self.prompts[-1] == prompt:
            self.pop()  # if the same prompt was given, delete the previous prompt and answer
        self.prompts.append(prompt)
        self.automatic.append(answer)

    def prompt(self, prompt, override=True, *args, **kwargs):
        """If override is False, then return a normal click prompt.
        Otherwise, if self.use_automatic is True, then use the automatic list.
        Finally, if neither of these conditions are filled then prompt normally
        and add the prompt and answer using self.add. 

        Arguments:
            prompt {str} -- The prompt to show to the user

        Keyword Arguments:
            override {bool} -- override the normal click prompt (default: {True})

        Returns:
            {any} -- The result of the click prompt
        """
        if not override:
            return click.prompt(prompt, *args, **kwargs)
        elif self.use_automatic:
            return self.automatic.pop(0)
        else:
            answer = click.prompt(prompt, *args, **kwargs)
            self.add(prompt, answer)
            return answer

    def confirm(self, prompt, override=True, default=False, *args, **kwargs):
        """Similar to self.prompt, but for click confirmations instead
        """
        if not override:
            return click.confirm(prompt, *args, **kwargs)
        elif self.use_automatic:
            return self.automatic.pop(0)
        else:
            answer = click.confirm(prompt, *args, **kwargs)
            self.add(prompt, answer)
            return answer

    def print(self, statement, override=True, *args, **kwargs):
        """Prints a statement only if override is False or automatic
        fillins are not currently being used. This is useful to surpress
        other print messages that are relevant to the prompt if the prompt
        is being filled out automatically.

        Arguments:
            statement {str} -- The statement to print

        Keyword Arguments:
            override {bool} -- override the normal print (default: {True})
        """
        if override:
            if not self.initial_automatic:
                builtins.print(statement, *args, **kwargs)
        else:
            builtins.print(statement, *args, **kwargs)


def form_cli(ctx_obj):
    """Forms the CLI command to duplicate the test

    Arguments:
        ctx_obj {dict} -- A dictionary containing the click context and user variables
            Variables for the root CLI command are first order keys. (ex: ctx_obj['wireshark'] = True) 
            Variables for command operations like scan and transmit are second order keys
            (ex: ctx_obj['scan']['timeout'] = 10) 
    """
    def update_params(params, obj, cmd):
        if not obj:
            params[cmd] = []
            return
        for k, v in obj.items():
            if isinstance(v, dict):
                if k not in DISCARD_VARS:
                    update_params(params, v, k)
            elif v is not None and k not in DISCARD_VARS:
                if not cmd in params:
                    params[cmd] = []
                if isinstance(v, bool):
                    params[cmd].extend(
                        ["--{}".format(k)]
                    )  # don't add the value for flags
                else:
                    params[cmd].extend(
                        ["--{}".format(k), str(v).replace(", ", ",")])
    if 'scan' in ctx_obj:
        if ctx_obj['scan']['timeout'] is not None and ctx_obj['scan']['num'] == 0:
            # if there is a timeout, scanning for unlimited packets is unecessary
            del ctx_obj['scan']['num']
    # don't need channels if all is true present
    if 'all' in ctx_obj:
        del ctx_obj['channels']
    else:
        if ctx_obj.get('scan', False) and ctx_obj['scan'].get('channels', False):
            if len(ctx_obj['scan']['channels']) == 1:
                ctx_obj['scan']['channels'] = ctx_obj['scan']['channels'][0]
        if ctx_obj.get('transmit', False) and ctx_obj['transmit'].get('transmit', False):
            if len(ctx_obj['transmit']['channels']) == 1:
                ctx_obj['transmit']['channels'] = ctx_obj['transmit']['channels'][0]
    params = {}
    update_params(params, ctx_obj, 'main')

    main_params = params.pop('main', '')
    if main_params:
        main_params = ' '.join(main_params)
    
    cmd_params = ""
    for k, v in params.items():
        cmd_params += ' {} '.format(k) + ' '.join(v)
    print("\nEnter the following command to replicate this test:")
    print(
        "snout {main_params} {auto} {protocol}{cmd_params}".format(
            main_params=main_params,
            auto=iot_click,
            protocol=ctx_obj['app'].protocol,
            cmd_params=cmd_params,
        ).replace('  ', ' ').replace('  ', ' '),  # remove double space if auto is blank
    )



iot_click = IoTClick()
