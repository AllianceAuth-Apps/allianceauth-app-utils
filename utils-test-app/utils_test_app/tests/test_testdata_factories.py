from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo
from app_utils.testdata_factories import (
    EveAllianceInfoFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
    UserFactory,
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


class TestEveInfoFactory(NoSocketsTestCase):
    def test_can_create_without_alliance(self):
        character = EveCharacterFactory(
            corporation=EveCorporationInfoFactory(create_alliance=False)
        )
        self.assertIsNone(character.alliance_id)


class TestUserFactory(NoSocketsTestCase):
    def test_can_create(self):
        # when
        perm_Name = "groupmanagement.request_groups"
        user = UserFactory(permissions__=[perm_Name])
        # then
        user.has_perm(perm_Name)
