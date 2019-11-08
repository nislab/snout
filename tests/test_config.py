from snout.core.config import Config as cfg

def test_config1():
    assert not cfg.is_initialized()

def test_config2():
    assert not cfg.is_initialized()
    cfg._cfginit_()
    assert isinstance(cfg._CFG_, dict)


def test_config_wrongkeys():
    assert False == cfg.get(False)
    assert False == cfg.get(None)
    assert False == cfg.get("nonexistant")


def test_config_getkeys():
    assert isinstance(cfg.get("pybombs"), dict)
    assert isinstance(cfg.get("pybombs.env"), dict)


def test_config_pybombs():
    py_env = cfg.pybombs_env()
    assert isinstance(py_env, dict)
    assert 'PATH' in py_env
    assert 'PYTHONPATH' in py_env
    assert 'LD_LIBRARY_PATH' in py_env
    assert 'LIBRARY_PATH' in py_env
    assert 'PKG_CONFIG_PATH' in py_env
    assert 'PYBOMBS_PREFIX' in py_env
