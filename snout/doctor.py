import ast
import datetime
import logging
import os
import platform
import subprocess
import sys
from shutil import copy
import yaml

import click

from snout.core.config import Config as cfg
from snout.core.config import setup_logging
from snout.core.pcontroller import PController


class SnoutDoctor(object):
    WARN_PY_VERSION = """
        Your default Python version is not Python 3. Please make sure Python 3
        is installed on your system and ensure Snout is running with the Python 3 interpreter
        (for example, by creating a virtual environment)
        """

    def __init__(self, verbose=False):
        """ Performs some general health checks.
        
        \b
        Keyword Arguments:
            verbose {bool} -- Makes diagnosis more verbose (default: {False})
        """
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

    def checkup(self):
        """ Perform all health checks.
        """
        self.check_py_version()
        self.check_virtualenv()
        self.check_pybombs_prefix()
        self.check_cfgfile()
        self.check_logging()

    def check_py_version(self):
        click.secho("- Python version:       ", nl=False)
        ok_py_version = sys.version_info[0] == 3
        msg_py_version = "" if ok_py_version else self.WARN_PY_VERSION
        py_version = ".".join(
            map(str, sys.version_info[:3])) if not self.verbose else sys.version_info
        click.secho(f"{py_version} {msg_py_version}",
                    fg='green' if ok_py_version else 'red')

    def check_virtualenv(self):
        check_virtualenv = 'VIRTUAL_ENV' in os.environ.keys()
        if check_virtualenv:
            click.secho(f"- Virtual environment:  {os.environ['VIRTUAL_ENV']}")
        else:
            click.secho("- No virtual environment active.")

    def check_pybombs_prefix(self):
        click.secho(f"- PyBOMBS prefix used:  ", nl=False)
        check_pybombs = cfg.get('pybombs.env.PYBOMBS_PREFIX', silent=True)
        if check_pybombs:
            click.secho(f"{check_pybombs}", fg='green')
        else:
            click.secho(
                "No PyBOMBS config file found. Run `snout-doctor reset-config` to set up.", fg='red')
    
    def check_cfgfile(self):
        click.secho(f"- Snout configuration:  ", nl=False)
        try:
            loc = cfg.location(silent=True)
            click.secho(f"{loc}", fg='green')
        except Exception as e:
            click.secho(
            "No PyBOMBS config file found. Run `snout-doctor reset-config` to set up.", fg='red')
    
    def check_logging(self):
        from snout.core.config import LOGCFG_FILE as loggingcfg
        if os.path.exists(loggingcfg):
            click.secho(f"- Logging configuration:{loggingcfg}", nl=False)
        if self.verbose:
            from logging_tree import printout
            printout()



# Click command line args
######################################################
CONTEXT_SETTINGS = dict(
    help_option_names=["-h", "--help"], max_content_width=110)


@click.group(invoke_without_command=False, context_settings=CONTEXT_SETTINGS)
@click.pass_context
@click.option(
    "verbose",
    "-v",
    "--verbose",
    count=True,
    help="Make everything more verbose.",
)
def main(
    ctx,
    verbose=None
):
    """Welcome to Snout Doctor!

        This is a helper tool that checks if everything is properly set up and allows you to manage the system configuration of Snout.
    """
    # Configure logging
    setup_logging()
    logger = logging.getLogger(__name__)

    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose

    # Get the PyBOMBS environment from the config:
    #py_env = cfg.pybombs_env()


@main.command('checkup', short_help='Performs a general checkup on your snout.')
@click.pass_context
@click.option(
    "verbose",
    "-v",
    "--verbose",
    count=True,
    help="Make everything more verbose.",
)
def checkup(ctx, verbose=None):
    """ Checks the vital signs of your snout to make sure it is working properly.
        """

    click.secho("\n# Checkup:", fg='cyan')
    doctor = SnoutDoctor(verbose)
    doctor.checkup()

    # Environment variables
    ctx.forward(env)


@main.command('env', short_help='Print the VIRTUAL_ENV and PATH variables as Snout sees them')
@click.pass_context
@click.option(
    "verbose",
    "-v",
    "--verbose",
    count=True,
    help="Make everything more verbose.",
)
def env(ctx, verbose=None):
    """ Prints all relevant environment variables.
    """
    show_always = ['VIRTUAL_ENV', 'PATH']
    click.secho("\n# Environmental Variables:", fg='cyan')
    for k, v in os.environ.items():
        if not verbose and k not in show_always:
            continue
        ___ = " "*(24-len(k))
        print(f"- {k}:{___}{v}")

@main.command('locate-config', short_help='Locate the config file')
def locate():
    cfg.print_location()

@main.command('edit-config', short_help='Edit all configuration values interactively')
def edit():
    cfg.interactive_edit()


@main.command('get-config', short_help='Get the configuration values')
@click.pass_context
@click.option('--keys', is_flag=True, help='Show all of the available keys')
@click.argument('key', required=False)
def get_config(ctx, key=None, keys=None):
    """ 
        Prints configuration settings.

        This returns all configuration keys and values. If a key argument is given, it only returns the selected entry.
        
        \b
        Arguments:
            key {str} -- select a configuration key (optional)
    """
    if keys:
        for key in cfg.formatted_keys():
            print(key)
    else:
        cfg.show(key=key)


@main.command('set-config', short_help='Set configuration values')
@click.pass_context
@click.argument('key')
@click.argument('value')
def set_config(ctx, key=None, value=None):
    """ 
        Sets configuration values.

        This sets the configuration entry of a given key to the given value.
        
        \b
        Arguments:
            key {str}   -- a valid configuration key
            value {str} -- configuration value
    """
    old_value = cfg.set(key, value=value)
    if old_value == False:
        print('Invalid key: {}'.format(key))
    else:
        print('Updated key {} to {} from {}'.format(key, value, old_value))


@main.command('reset-config', short_help='Reset the config to a default configuration.')
@click.pass_context
def setup(ctx, key=None, value=None):
    try:
        old_config = cfg.location(silent=True)
    except Exception as e:
        old_config = None
    if old_config:
        click.secho(f"Old config file found in {old_config}.", fg='yellow')
        old_config_bkup = old_config + '.bkup'
        copy(old_config, old_config_bkup)
        click.secho(f"-> Created backup of config file {old_config_bkup}.", fg='green')
    pybombs_prefix = os.getenv('PYBOMBS_PREFIX')
    if pybombs_prefix:
        click.secho(f"Found PyBOMBS prefix {pybombs_prefix}.", fg='yellow')
        if click.confirm('Do you want to use this?'):
            cfg.reset(userprefix=pybombs_prefix, force=True)
            new_config = cfg.location()
            click.secho(f"-> Created fresh config file {new_config}.", fg='green')
    else:
        click.secho(f"Could not find PyBOMBS prefix. Please run your PyBOMBS `setup_env.sh` script first.", fg='red')
        exit(1)


if __name__ == "__main__":
    try:
        try:
            main(obj={})
        except click.Abort:  # click equivalent of a keyboard interrupt
            print("\nQuitting...")
            sys.exit(-1)
    except AttributeError:  # if keyboard interrupt after starting, click will use a string with make_context, which will raise an AttributeError
        sys.exit(0)
