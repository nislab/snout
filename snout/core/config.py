import json
import logging
import logging.config
import os
import subprocess
import time
from pathlib import Path

import appdirs
import click

import yaml
from scapy.config import conf

from .pcontroller import PController

USER_DATA_DIR = appdirs.user_data_dir('Snout', 'NISLAB')
OUTPUTS_DIR = os.path.join(USER_DATA_DIR, 'outputs')
CONFIG_FILE = os.path.join(USER_DATA_DIR, 'config.yml') # previously CONFIG_PATH
LOGCFG_FILE = os.path.join(USER_DATA_DIR, 'logging.json')
# Logging default settings from https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
LOGCFG_DEFAULTSETTINGS = """
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },

        "info_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": "info.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },

        "error_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "simple",
            "filename": "errors.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        }
    },

    "loggers": {
        "my_module": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": false
        }
    },

    "root": {
        "level": "DEBUG",
        "handlers": ["console", "info_file_handler", "error_file_handler"]
    }
}
"""

def setup_logging(
    default_path=LOGCFG_FILE,
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if not os.path.exists(path):
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        with open(path, 'w') as f:
            f.write(LOGCFG_DEFAULTSETTINGS)
    with open(path, 'rt') as f:
        config = json.load(f)
    logging.config.dictConfig(config)

class Config(object):
    USER_DATA_DIR = USER_DATA_DIR
    OUTPUTS_DIR = OUTPUTS_DIR
    CONFIG_FILE = CONFIG_FILE
    LOGCFG_FILE = LOGCFG_FILE

    _CFG_ = None
    logger = logging.getLogger(__name__)

    @classmethod
    def _cfginit_(cls, silent=False):
        if not cls.is_initialized():
            return cls.load(silent=silent)
        return True # already initialized

    @classmethod
    def is_initialized(cls):
        return True if cls._CFG_ else False
    
    @classmethod
    def load(cls, silent=False):
        try:
            cls._CFG_ = yaml.safe_load(open(CONFIG_FILE, "r"))
        except FileNotFoundError as e:
            if not silent:
                print(f" SILENT = {silent}")
                cls.logger.error(f"Error loading config file: {e.filename} not found ({e.__class__.__name__}: {e.strerror})", exc_info=True)
                cls.logger.info(f"Run the Snout setup or snout-doctor to create a valid config file.")
        except yaml.YAMLError as e:
            if not silent:
                cls.logger.error(f"Error in configuration file: {e}", exc_info=True)
        return True if cls._CFG_ else False # return whether _CFG_ was loaded successfully
    
    @classmethod
    def store(cls, cfg=None, cfgfile=None, init=False):
        # Can dump a provided config `cfg` or dump the global config in `cls.CFGSTORE`.
        if not cls.is_initialized() and not cfg:
            raise ValueError("Config is not initialized and no config provided. Unclear what should be stored.")
        if not cfg:
            cls._cfginit_()
            cfg = cls._CFG_
        elif not init:
            cls._cfginit_()
            cfg = cls._CFG_.update(cfg)
        if not cfgfile:
            cfgfile = CONFIG_FILE
        # Make sure config dir exists on the system
        if not os.path.exists(USER_DATA_DIR):
            os.makedirs(USER_DATA_DIR, exist_ok=True)
        # Store the config
        with open(cfgfile, 'w') as f:
            return yaml.dump(cfg, f)

    @classmethod
    def reset(cls, userprefix="//USERPREFIX//", force=False):
        cls._cfginit_(silent=True)
        if not cls.is_initialized() or force:
            init_cfg = {
                'pybombs': {
                    'env': {
                        'PATH': f'{userprefix}/bin',
                        'PYTHONPATH':       f'{userprefix}/python:' \
                                            f'{userprefix}/lib/python3.6/site-packages:' \
                                            f'{userprefix}/lib64/python3.6/site-packages:' \
                                            f'{userprefix}/lib/python3.6/dist-packages:' \
                                            f'{userprefix}/lib64/python3.6/dist-packages:' \
                                            f'{userprefix}/lib/python3.7/site-packages:' \
                                            f'{userprefix}/lib64/python3.7/site-packages:' \
                                            f'{userprefix}/lib/python3.7/dist-packages:' \
                                            f'{userprefix}/lib64/python3.7/dist-packages:' \
                                            f'{userprefix}/lib/python2.6/site-packages:' \
                                            f'{userprefix}/lib64/python2.6/site-packages:' \
                                            f'{userprefix}/lib/python2.6/dist-packages:' \
                                            f'{userprefix}/lib64/python2.6/dist-packages:' \
                                            f'{userprefix}/lib/python2.7/site-packages:' \
                                            f'{userprefix}/lib64/python2.7/site-packages:' \
                                            f'{userprefix}/lib/python2.7/dist-packages:' \
                                            f'{userprefix}/lib64/python2.7/dist-packages',
                        'LD_LIBRARY_PATH':  f'{userprefix}/lib:' \
                                            f'{userprefix}/lib64/',
                        'LIBRARY_PATH':     f'{userprefix}/lib:' \
                                            f'{userprefix}/lib64/',
                        'PKG_CONFIG_PATH':  f'{userprefix}/lib/pkgconfig:' \
                                            f'{userprefix}/lib64/pkgconfig',
                        'PYBOMBS_PREFIX':   f'{userprefix}/'
                    },
                },
                'docker': os.environ.get('SNOUT_DOCKER', False),
            }
            cls.store(cfg=init_cfg, init=True)
        else:
            raise Exception("Configuration was already set up. (API: run Config.reset(force=True))")

    @classmethod
    def location(cls, silent=False):
        if cls._cfginit_(silent=silent):
            return CONFIG_FILE
        raise Exception("Configuration could not be loaded.")

    @classmethod
    def print_location(cls):
        print(cls.location())

#### try:
####     _cfgstore = yaml.safe_load(open(CONFIG_PATH, "r"))
#### except FileNotFoundError:
####     _cfgstore = None  # not setup yet


#### def setup(placeholder="//USERPREFIX//"):
####     from scapy.themes import DefaultTheme
####     conf.color_theme = DefaultTheme()
####     global _cfgstore
#### 
####     # If it is not setup yet, prompt the user for paths
####     if placeholder in _cfgstore['pybombs']['env']['PATH']:
####         if _cfgstore['docker']:
####             run_install = False
####             prefix = '/pybombs'
####             # Replace the sample config with the actual paths
####             _cfg_store = replace_all(_cfgstore, prefix, placeholder)
####             return _dump()
####         run_install = False  # click.confirm("Install libraries? (If no, then only the config will be modified) \
####         #    \nOnly skip this if you have all the required libraries")
####         if run_install:
####             subprocess.Popen(['chmod', '+x', 'install.sh'])
####             install_pybombs = not click.confirm(
####                 "Do you already have pybombs installed?")
####             if install_pybombs:
####                 confirmed = False
####                 while not confirmed:
####                     prefix = click.prompt(
####                         "Where would you like to install pybombs?").rstrip('/')
####                     if '~' in prefix:
####                         print("Error: Please do not use ~, type the full directory:")
####                         print("i.e. ~/prefix = /home/username/prefix")
####                     confirmed = os.path.isdir(prefix) and click.confirm(
####                         "Confirm: Install pybombs at " + prefix + "?")
####                 # pcontroller for the install sh with pybombs install
####                 install_process = PController(
####                     './install.sh', [prefix, 'y'], pipe=False)
####         while not run_install or not install_pybombs:
####             prefix = click.prompt(
####                 "Please enter the path for your pybombs prefix"
####             ).rstrip('/')
####             if prefix[0] == '~':
####                 # ~ throws things off. replace with raw home dir
####                 prefix = os.path.join(Path.home(), prefix[1:].lstrip('/'))
####             # Check if there is a setup_env file at that path
####             if os.path.isfile(os.path.join(prefix, "setup_env.sh")):
####                 # pcontroller for the install sh without pybombs install
####                 install_process = PController(
####                     './install.sh', prefix, pipe=False)
####                 break
####             else:
####                 print("Error: Please enter a valid pybombs prefix path")
####         # if run_install:
####             # !TODO: Remove this, install.sh is not valid any more
####             # install_process.run()
####             # Wait until the install is finished before continuing
####             # while (install_process.is_running()):
####             #     time.sleep(1)
####         # Replace the sample config with the actual paths
####         _cfg_store = replace_all(_cfgstore, prefix, placeholder)
####         return _dump()

####def _dump(update_dict=None):
####    """Dumps _cfgstore to the config file.
####
####    Keyword Arguments:
####        update_dict {dict} -- If given, _cfgstore will be updated with this 
####                                dict and then dumped (default: {None})
####
####    Raises:
####        Exception: If an update_dict is given but _cfgstore is None 
####    """
####    global _cfgstore
####    if update_dict:
####        if exists():
####            _cfgstore.update(update_dict)
####        else:
####            # user will probably never see this exception, but it is helpful for debugging
####            raise Exception(
####                "You must setup() before dumping specific values to the config.")
####        _cfgstore.update(update_dict)
####    if not exists():
####        raise Exception(
####            "Attempted to dump empty value to the config.")
####    if not os.path.exists(USER_DATA_DIR):
####        os.makedirs(USER_DATA_DIR, exist_ok=True)
####    return yaml.dump(_cfgstore, open(CONFIG_PATH, 'w'))

    @classmethod
    def replace_all(cls, tree, prefix, placeholder):
        """Replaces all occurences of placeholder with prefix 

        Returns:
            dict -- the config dict with the updated user prefix
        """
        for item in tree:
            if isinstance(tree[item], dict):
                item = cls.replace_all(tree[item], prefix, placeholder)
            elif isinstance(tree[item], str):
                tree[item] = tree[item].replace(placeholder, prefix)
        return tree

    @classmethod
    def get(cls, cfg_path, cfg_node=None, silent=False):
        if cls._cfginit_(silent=silent):
            if isinstance(cfg_path, list):
                if cfg_node is None:
                    if not cfg_path:
                        return None
                    return cls.get(cfg_path, cls._CFG_)
                if not cfg_path:
                    return cfg_node
                if isinstance(cfg_node, dict):
                    node = cfg_path.pop(0)
                    return cls.get(cfg_path, cfg_node[node]) if node in cfg_node else False
            elif isinstance(cfg_path, str):
                return cls.get(cfg_path.split("."), cls._CFG_)
            elif not cfg_path:
                return False
        return None

    @classmethod
    def set(cls, cfg_path, cfg_node=None, value=None):
        if cls._cfginit_():
            if isinstance(cfg_path, str):
                return cls.set(cfg_path.split("."), cls._CFG_, value)
            else:
                if cfg_node is None:
                    return cls.set(cfg_path, cls._CFG_, value)
                elif len(cfg_path) == 1:
                    try:
                        if isinstance(cfg_node[cfg_path[0]], list) or isinstance(cfg_node[cfg_path[0]], dict):
                            old_value = cfg_node[cfg_path[0]].copy()
                        else:
                            old_value = cfg_node[cfg_path[0]]
                        cfg_node[cfg_path[0]] = value
                        cls.store()
                        return old_value
                    except KeyError:
                        return False
                elif isinstance(cfg_node, dict):
                    node = cfg_path.pop(0)
                    return cls.set(cfg_path, cfg_node[node], value) if node in cfg_node else False
                else:
                    return False

    @classmethod
    def pybombs_env(cls):
        """ Merges the current environment with additional PyBOMBS variables from the config.
        """
        if cls._cfginit_():
            pybombs_env = {**os.environ}    # copy the current environment into a dict
            cfg_env = cls.get("pybombs.env")    # grab the pybombs environment from config
            for k, v in cfg_env.items():
                if k in pybombs_env:        # check if var already exists
                    if pybombs_env[k] == v:  # if this var already has the same value, nothing to do
                        continue
                    if 'PREFIX' in k:       # for prefix var, replace
                        pybombs_env[k] = v
                    if 'PATH' in k:         # for path var, combine paths
                        pybombs_env[k] = ':'.join([v, pybombs_env[k]])
                else:                       # if var doesn't exist, add it to env
                    pybombs_env[k] = v
            return pybombs_env

    @classmethod
    def prompt_edits(cls, d, prompt_prefix=''):
        """Prompts the user for edits of each key in a dict
        """
        IGNORE_KEYS = ['docker']
        for k, v in d.items():
            if k in IGNORE_KEYS:
                continue
            if isinstance(v, dict):
                add_prefix = ' '.join([name for name in k.split('_')])
                if prompt_prefix:
                    new_prefix = '{} -> {}'.format(prompt_prefix, add_prefix)
                else:
                    new_prefix = add_prefix
                cls.prompt_edits(v, new_prefix)
            else:
                if d[k] is None:
                    # click won't accept None, but it will accept an empty string if it is the default
                    d[k] = ''
                add_prefix = ' '.join([name for name in k.split('_')])
                if prompt_prefix:
                    new_prefix = '{} -> {}'.format(
                        prompt_prefix, add_prefix)
                else:
                    new_prefix = add_prefix
                result = click.prompt(
                    new_prefix,
                    default=d[k],
                    show_default=bool(d[k])
                )
                # don't want empty strings to be saved
                d[k] = result if result else None

    @classmethod
    def interactive_edit(cls):
        cls._cfginit_()
        cls.prompt_edits(cls._CFG_)
        cls.store()

    @classmethod
    def formatted_keys(cls):
        cls._cfginit_()
        
        IGNORE_KEYS = ['docker']

        def form_keys_dict(d):
            new_dict = {}
            for k, v in d.items():
                if k in IGNORE_KEYS:
                    continue
                if isinstance(v, dict):
                    for sub_k, sub_v in form_keys_dict(v).items():
                        new_dict.update(
                            {'{}.{}'.format(k, sub_k): sub_v}
                        )
                else:
                    new_dict.update(
                        {'{}'.format(k): v}
                    )
            return new_dict
        return list(form_keys_dict(cls._CFG_).keys())

    @classmethod
    def show(cls, key=None):
        """Shows the config using json.dumps. This is easier to interpret in the terminal
        than yaml.dump, especially for longer strings. If no key is given, show the whole
        config

        Keyword Arguments:
            key {str} -- Key to view (default: {None})

        Raises:
            Exception: the config is not setup yet
        """
        cls._cfginit_()
        if key:
            find_result = cls.get(key)
            if find_result != False:
                if isinstance(find_result, dict):
                    print('{}:\n\n{}'.format(key, json.dumps(find_result, indent=4)))
                else:
                    if isinstance(find_result, str) and len(find_result) > 120:
                        print('{}:\n\n{}'.format(key, find_result))
                    else:
                        print('{}: {}'.format(key, find_result))
            else:
                print("Invalid key: {}".format(key))
        else:
            print(json.dumps(cls._CFG_, indent=4))
