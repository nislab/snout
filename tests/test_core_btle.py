import snout.core.protocols.btle.assigned_numbers as btle_constants

def test_btle_constants():
    assert btle_constants.company_ids
    assert isinstance(btle_constants.company_ids, dict)
    assert len(btle_constants.company_ids.keys()) > 0
    assert btle_constants.ad_types
    assert isinstance(btle_constants.ad_types, dict)
    assert len(btle_constants.ad_types.keys()) > 0