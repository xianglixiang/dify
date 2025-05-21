import unittest
from unittest.mock import MagicMock, patch

from werkzeug.exceptions import InternalServerError

from extensions.ext_database import db
from models.account import Account, Tenant, TenantStatus
from services.account_service import TenantService
from services.errors.account import (
    InvalidActionError,
    NoPermissionError,
    TenantNotFoundError,
)


class TestTenantService(unittest.TestCase):

    @patch('services.account_service.db')
    def test_create_workspace_by_admin_success(self, mock_db):
        mock_creator_account = MagicMock(spec=Account)
        mock_creator_account.is_admin_or_owner = True
        mock_creator_account.current_tenant = MagicMock(spec=Tenant)

        mock_new_tenant = MagicMock(spec=Tenant)
        mock_new_tenant.id = "new_tenant_id"
        mock_new_tenant.name = "New Workspace"

        with patch.object(TenantService, 'create_tenant', return_value=mock_new_tenant) as mock_create_tenant:
            created_tenant = TenantService.create_workspace_by_admin(
                name="New Workspace",
                creator_account=mock_creator_account
            )

            mock_create_tenant.assert_called_once_with(name="New Workspace", is_from_dashboard=True)
            self.assertEqual(created_tenant, mock_new_tenant)
            self.assertEqual(created_tenant.name, "New Workspace")

    def test_create_workspace_by_admin_no_permission_not_admin(self):
        mock_creator_account = MagicMock(spec=Account)
        mock_creator_account.is_admin_or_owner = False
        mock_creator_account.current_tenant = MagicMock(spec=Tenant)

        with self.assertRaises(NoPermissionError):
            TenantService.create_workspace_by_admin(
                name="New Workspace",
                creator_account=mock_creator_account
            )

    def test_create_workspace_by_admin_no_permission_no_current_tenant(self):
        mock_creator_account = MagicMock(spec=Account)
        mock_creator_account.is_admin_or_owner = True
        mock_creator_account.current_tenant = None

        with self.assertRaises(NoPermissionError) as e: # Capture the exception
            TenantService.create_workspace_by_admin(
                name="New Workspace",
                creator_account=mock_creator_account
            )
        # Check the exception message
        self.assertIn("Admin user must have an active workspace", str(e.exception))


    @patch('services.account_service.db')
    def test_delete_workspace_by_admin_success(self, mock_db):
        mock_operator_account = MagicMock(spec=Account)
        mock_operator_account.is_admin_or_owner = True
        mock_operator_account.current_tenant = MagicMock(spec=Tenant)
        mock_operator_account.current_tenant.id = "operator_tenant_id"
        mock_operator_account.current_tenant_id = "operator_tenant_id" # Ensure this attribute is set

        mock_target_tenant = MagicMock(spec=Tenant)
        mock_target_tenant.id = "target_tenant_id"
        mock_target_tenant.status = TenantStatus.NORMAL.value # Initial status

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_target_tenant
        mock_db.session.query.return_value = mock_query

        TenantService.delete_workspace_by_admin(
            workspace_id="target_tenant_id",
            operator_account=mock_operator_account
        )

        self.assertEqual(mock_target_tenant.status, TenantStatus.ARCHIVE.value)
        mock_db.session.commit.assert_called_once()

    def test_delete_workspace_by_admin_no_permission_not_admin(self):
        mock_operator_account = MagicMock(spec=Account)
        mock_operator_account.is_admin_or_owner = False
        mock_operator_account.current_tenant = MagicMock(spec=Tenant)

        with self.assertRaises(NoPermissionError):
            TenantService.delete_workspace_by_admin(
                workspace_id="target_tenant_id",
                operator_account=mock_operator_account
            )

    def test_delete_workspace_by_admin_no_permission_no_current_tenant(self):
        mock_operator_account = MagicMock(spec=Account)
        mock_operator_account.is_admin_or_owner = True
        mock_operator_account.current_tenant = None

        with self.assertRaises(NoPermissionError) as e: # Capture the exception
            TenantService.delete_workspace_by_admin(
                workspace_id="target_tenant_id",
                operator_account=mock_operator_account
            )
        self.assertIn("Admin user must have an active workspace", str(e.exception))


    @patch('services.account_service.db')
    def test_delete_workspace_by_admin_delete_self_error(self, mock_db):
        mock_operator_account = MagicMock(spec=Account)
        mock_operator_account.is_admin_or_owner = True
        mock_operator_account.current_tenant = MagicMock(spec=Tenant)
        mock_operator_account.current_tenant.id = "self_tenant_id"
        mock_operator_account.current_tenant_id = "self_tenant_id" # Ensure this attribute is set

        mock_target_tenant = MagicMock(spec=Tenant)
        mock_target_tenant.id = "self_tenant_id" # Same as operator's current tenant

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_target_tenant
        mock_db.session.query.return_value = mock_query

        with self.assertRaises(InvalidActionError):
            TenantService.delete_workspace_by_admin(
                workspace_id="self_tenant_id",
                operator_account=mock_operator_account
            )

    @patch('services.account_service.db')
    def test_delete_workspace_by_admin_tenant_not_found(self, mock_db):
        mock_operator_account = MagicMock(spec=Account)
        mock_operator_account.is_admin_or_owner = True
        mock_operator_account.current_tenant = MagicMock(spec=Tenant)
        mock_operator_account.current_tenant_id = "operator_tenant_id"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None # Simulate tenant not found
        mock_db.session.query.return_value = mock_query

        with self.assertRaises(TenantNotFoundError):
            TenantService.delete_workspace_by_admin(
                workspace_id="non_existent_tenant_id",
                operator_account=mock_operator_account
            )

if __name__ == '__main__':
    unittest.main()
