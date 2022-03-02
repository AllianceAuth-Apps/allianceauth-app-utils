from unittest.mock import patch

from redis import Redis

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from allianceauth.notifications.models import Notification
from app_utils._app_settings import APP_UTILS_NOTIFY_THROTTLED_TIMEOUT
from app_utils.allianceauth import (
    create_fake_user,
    get_redis_client,
    notify_admins,
    notify_admins_throttled,
)
from app_utils.helpers import throttle

MODULE_PATH = "app_utils.allianceauth"


class TestNotifyAdmins(TestCase):
    def test_should_notify_users_with_logging_permissions_and_superusers_only(self):
        # given
        superuser = User.objects.create_superuser(username="super")
        user_admin = create_fake_user(
            1001, "Bruce Wayne", permissions=["auth.logging_notifications"]
        )
        user_regular = create_fake_user(1002, "Peter Parker")
        # when
        notify_admins("message", "title", "danger")
        # then
        self.assertEqual(Notification.objects.filter(user=superuser).count(), 1)
        self.assertEqual(Notification.objects.filter(user=user_admin).count(), 1)
        self.assertEqual(Notification.objects.filter(user=user_regular).count(), 0)
        notif = Notification.objects.filter(user=superuser).first()
        self.assertEqual(notif.message, "message")
        self.assertEqual(notif.title, "title")
        self.assertEqual(notif.level, "danger")


class TestNotifyAdminsThrottled(TestCase):
    def test_should_send_notification_when_new(self):
        # given
        user_admin = create_fake_user(
            1001, "Bruce Wayne", permissions=["auth.logging_notifications"]
        )
        cache.clear()
        # when
        notify_admins_throttled("message-id", "message", "title")
        # then
        self.assertEqual(Notification.objects.filter(user=user_admin).count(), 1)

    def test_should_discard_subsequent_notifications_while_throttled(self):
        # given
        user_admin = create_fake_user(
            1001, "Bruce Wayne", permissions=["auth.logging_notifications"]
        )
        cache.clear()
        # when
        notify_admins_throttled("message-id", "message", "title")
        notify_admins_throttled("message-id", "message", "title")
        # then
        self.assertEqual(Notification.objects.filter(user=user_admin).count(), 1)

    @patch("app_utils.allianceauth.throttle", wraps=throttle)
    def test_should_use_default_timeout_when_not_specified(self, spy_throttle):
        # given
        create_fake_user(
            1001, "Bruce Wayne", permissions=["auth.logging_notifications"]
        )
        cache.clear()
        # when
        notify_admins_throttled("message-id", "message", "title")
        # then
        _, kwargs = spy_throttle.call_args
        self.assertEqual(kwargs["timeout"], APP_UTILS_NOTIFY_THROTTLED_TIMEOUT)

    @patch(MODULE_PATH + ".APP_UTILS_NOTIFY_THROTTLED_TIMEOUT", 123)
    @patch("app_utils.allianceauth.throttle", wraps=throttle)
    def test_should_use_timeout_setting_when_defined(self, spy_throttle):
        # given
        create_fake_user(
            1001, "Bruce Wayne", permissions=["auth.logging_notifications"]
        )
        cache.clear()
        # when
        notify_admins_throttled("message-id", "message", "title")
        # then
        _, kwargs = spy_throttle.call_args
        self.assertEqual(kwargs["timeout"], 123)


class TestGetRedisClient(TestCase):
    def test_should_return_redis_client(self):
        # when
        client = get_redis_client()
        # then
        self.assertIsInstance(client, Redis)
