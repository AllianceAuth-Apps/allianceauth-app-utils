from django.core.cache import cache
from django.test import TestCase, override_settings

from app_utils.caching import ObjectCacheMixin

CURRENT_PATH = "utils_test_app.tests.test_caching"
fake_objects = dict()


class FakeManager(ObjectCacheMixin):
    def create(self, name):
        pk = len(fake_objects) + 1
        fake_objects[pk] = self.model(pk, name)
        return fake_objects[pk]

    def get(self, pk):
        return fake_objects[pk]

    def select_related(self, query):
        return self

    @property
    def model(self):
        return FakeModel


class _FakeMeta:
    def __init__(self, app_label, model_name) -> None:
        self.app_label = app_label
        self.model_name = model_name


class FakeModel:
    def __init__(self, pk, name) -> None:
        self.pk = pk
        self.name = name

    _meta = _FakeMeta("dummy", "fakemodel")
    objects = FakeManager()


@override_settings(APP_UTILS_OBJECT_CACHE_DISABLED=False)
class TestObjectCacheMixin(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def test_should_fetch_from_db_when_cache_is_empty(self):
        # given
        obj = FakeModel.objects.create(name="My object")

        # when
        new_obj = FakeModel.objects.get_cached(pk=obj.pk)

        # then
        self.assertEqual(new_obj.name, "My object")

    def test_should_fetch_from_cache(self):
        # given
        obj = FakeModel.objects.create(name="My object")
        FakeModel.objects.get_cached(pk=obj.pk)
        obj.name = "Changed object"

        # when
        new_obj = FakeModel.objects.get_cached(pk=obj.pk)

        # then
        self.assertEqual(new_obj.name, "My object")

    def test_should_fetch_from_db_when_cache_cleared(self):
        # given
        obj = FakeModel.objects.create(name="My object")
        FakeModel.objects.get_cached(pk=obj.pk)
        obj.name = "Changed object"

        # when
        FakeModel.objects.clear_cache(pk=obj.pk)
        new_obj = FakeModel.objects.get_cached(pk=obj.pk)

        # then
        self.assertEqual(new_obj.name, "Changed object")

    def test_should_fetch_from_db_when_query_is_different(self):
        # given
        obj = FakeModel.objects.create(name="My object")
        FakeModel.objects.get_cached(pk=obj.pk, select_related="dummy")
        obj.name = "Changed object"

        # when
        new_obj = FakeModel.objects.get_cached(pk=obj.pk)

        # then
        self.assertEqual(new_obj.name, "Changed object")

    def test_should_fetch_from_cache_with_select_related(self):
        # given
        obj = FakeModel.objects.create(name="My object")
        FakeModel.objects.get_cached(pk=obj.pk, select_related="dummy")
        obj.name = "Changed object"

        # when
        new_obj = FakeModel.objects.get_cached(pk=obj.pk, select_related="dummy")

        # then
        self.assertEqual(new_obj.name, "My object")

    def test_should_fetch_from_db_when_cache_cleared_with_select_related(self):
        # given
        obj = FakeModel.objects.create(name="My object")
        FakeModel.objects.get_cached(pk=obj.pk, select_related="dummy")
        obj.name = "Changed object"

        # when
        FakeModel.objects.clear_cache(pk=obj.pk)
        new_obj = FakeModel.objects.get_cached(pk=obj.pk, select_related="dummy")

        # then
        self.assertEqual(new_obj.name, "Changed object")


@override_settings(APP_UTILS_OBJECT_CACHE_DISABLED=True)
class TestObjectCacheMixin2(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def test_should_fetch_from_db_when_cache_is_disabled(self):
        # given
        obj = FakeModel.objects.create(name="My object")
        FakeModel.objects.get_cached(pk=obj.pk)
        obj.name = "Changed object"

        # when
        new_obj = FakeModel.objects.get_cached(pk=obj.pk)

        # then
        self.assertEqual(new_obj.name, "Changed object")
