import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database.db as db_module
from database.db import init_db, get_db
from services.notification_service import NotificationService
from utils.security import hash_password

TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_medikiosk_notif.db")


def setup_module():
    db_module.DB_PATH = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_db()
    seed()


def teardown_module():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def seed():
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, 'patient', ?, ?)",
            ("notify@test.com", hash_password("ValidPass123!"), "Notify", "User"),
        )
        conn.commit()
        global user_id
        user_id = cursor.lastrowid
    finally:
        conn.close()


def test_create_notification():
    result = NotificationService.create_notification(1, "Test title", "Test message", "info")
    assert result is not None


def test_retrieve_notifications():
    NotificationService.create_notification(1, "Notification A", "Message A", "info")
    NotificationService.create_notification(1, "Notification B", "Message B", "appointment")
    notifications = NotificationService.get_user_notifications(1)
    assert len(notifications) >= 2
    titles = [n["title"] for n in notifications]
    assert "Notification A" in titles
    assert "Notification B" in titles


def test_unread_count_and_mark():
    NotificationService.create_notification(1, "Unread test", "Unread message")
    count = NotificationService.get_unread_count(1)
    assert count >= 1
    notifications = NotificationService.get_user_notifications(1, unread_only=True)
    assert notifications
    NotificationService.mark_all_read(1)
    count_after = NotificationService.get_unread_count(1)
    assert count_after == 0
    notifications = NotificationService.get_user_notifications(1, unread_only=True)
    assert len(notifications) == 0


def test_mark_read():
    NotificationService.create_notification(1, "Single", "Single message")
    notifications = NotificationService.get_user_notifications(1)
    target = notifications[0]
    NotificationService.mark_read(target["id"])
    notifications2 = NotificationService.get_user_notifications(1)
    target2 = [n for n in notifications2 if n["id"] == target["id"]][0]
    assert target2["is_read"] == 1