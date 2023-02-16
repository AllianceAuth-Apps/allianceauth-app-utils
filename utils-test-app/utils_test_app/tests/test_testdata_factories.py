from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo
from app_utils.testdata_factories import (
    EveAllianceInfoFactory,
    EveCorporationInfoFactory,
)
from app_utils.testing import NoSocketsTestCase


class TestEveAllianceInfoFactory(NoSocketsTestCase):
    def test_should_create_obj(self):
        # when
        obj = EveAllianceInfoFactory()
        # then
        self.assertIsInstance(obj, EveAllianceInfo)


class TestEveCorporationInfoFactory(NoSocketsTestCase):
    def test_should_create_obj(self):
        # when
        obj = EveCorporationInfoFactory()
        # then
        self.assertIsInstance(obj, EveCorporationInfo)
