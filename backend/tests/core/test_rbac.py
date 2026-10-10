import pytest
from app.core.rbac import has_permission, PERMISSIONS


def test_owner_has_all():
    owner_perms = PERMISSIONS["owner"]
    assert "users.manage" in owner_perms
    assert "settings.view" in owner_perms


def test_operator_cannot_manage_users():
    assert not has_permission("operator", "users.manage")


def test_operator_can_scan():
    assert has_permission("operator", "scan.use")


def test_buyer_limited():
    assert has_permission("buyer", "buyer.own")
    assert not has_permission("buyer", "inventory.view")


def test_unknown_role_denied():
    assert not has_permission("ghost", "settings.view")


def test_all_roles_defined():
    expected = {"owner", "manager", "storekeeper", "operator", "qc_inspector", "dispatch", "accounts", "buyer"}
    assert set(PERMISSIONS.keys()) == expected