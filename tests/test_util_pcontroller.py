import time
import os
from snout.core import pcontroller
from snout.core.config import Config as cfg

def test_pcontroller_empty():
    p = pcontroller.PController()
    assert p.full_cmd == ['']


def test_pcontroller_empty_args():
    p = pcontroller.PController('ls')
    assert isinstance(p.args, list)
    assert p.args == []


def test_pcontroller_arg_str():
    p = pcontroller.PController('ls', '-a')
    assert p.args == ['-a']


def test_pcontroller_add_arg():
    p = pcontroller.PController('ls', '-a')
    assert p.args == ['-a']
    p.add_args('-l')
    assert p.args == ['-a', '-l']


def test_pcontroller_cmd_str():
    p = pcontroller.PController('ls', ['-a', '-l'])
    assert p.args == ['-a', '-l']
    assert p.full_cmd == ['ls', '-a', '-l']


def test_pcontroller_run():
    myprocess = pcontroller.PController("tests/util/pcontroller_forloop.sh")
    myprocess.run()  # this should run the process
    assert myprocess.is_running() is True
    assert isinstance(myprocess.pid, int) and myprocess.pid > 0
    # give the subprocess time to produce IO and the queues to collect it
    time.sleep(.1)
    result = myprocess.readline()  # read output from the
    assert result == 'Number: 1'
    time.sleep(.1)
    assert myprocess.p.returncode is None
    assert myprocess.is_running() is True
    time.sleep(4)
    assert myprocess.is_running() is False
    assert myprocess.p.returncode == 0
    assert myprocess.status == pcontroller.PState.TERMINATED


def test_pcontroller_run_stop():
    myprocess = pcontroller.PController("tests/util/pcontroller_forloop.sh")
    myprocess.run()  # this should run the process
    assert myprocess.is_running() is True
    assert isinstance(myprocess.pid, int) and myprocess.pid > 0
    # give the subprocess time to produce IO and the queues to collect it
    time.sleep(.1)
    result = myprocess.readline()  # read output from the
    assert result == 'Number: 1'
    time.sleep(.1)
    assert myprocess.p.returncode is None
    assert myprocess.is_running() is True
    myprocess.stop()
    time.sleep(5)
    assert myprocess.is_running() is False
    assert myprocess.p.returncode == -15
    assert myprocess.status == pcontroller.PState.STOPPED

def test_pcontroller_env_fun():
    env = os.environ
    env['PYBOMBS_PREFIX'] = '/hello'
    env['PATH'] = ':'.join(['/hello', env['PATH']])
    myprocess = pcontroller.PController(
        "tests/util/pcontroller_py_env.sh", env=env)
    myprocess.run()  # this should run the process
    # give the subprocess time to produce IO and the queues to collect it
    time.sleep(.1)
    hello = myprocess.readline()  # read output from the
    hello_path = myprocess.readline()  # read output from the
    assert hello == '/hello'
    assert '/hello' in hello_path


def test_pcontroller_pybombs_env():
    py_env = cfg.pybombs_env()
    myprocess = pcontroller.PController(
        "tests/util/pcontroller_py_env.sh", env=py_env)
    myprocess.run()  # this should run the process
    # give the subprocess time to produce IO and the queues to collect it
    time.sleep(.1)
    res_PYBOMBS_PREFIX = myprocess.readline()  # read output from the
    res_PATH = myprocess.readline()  # read output from the
    assert res_PYBOMBS_PREFIX == str(cfg.get('pybombs.env.PYBOMBS_PREFIX'))
    assert str(cfg.get('pybombs.env.PYBOMBS_PREFIX')) in res_PATH
