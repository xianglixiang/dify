import json
import uuid
from unittest.mock import MagicMock, patch

from models.account import Tenant
from tests.integration_tests.framework import FlaskIntegrationTestCase


class TestAdminWorkspaceApi(FlaskIntegrationTestCase):

    def setUp(self):
        super().setUp()
        # Assuming you have a way to set up an admin user and get their API key
        # For simplicity, we'll mock the admin_required decorator or related checks
        # or assume the test client is already authenticated as admin.
        # If using an API key, it might be set in headers:
        # self.headers = {'Authorization': f'Bearer {self.get_admin_api_key()}'}
        # self.admin_user = self.get_admin_user() # A helper to get/create an admin

        # Patch admin_required to bypass actual auth for these tests
        self.admin_required_patch = patch('controllers.console.admin.admin_required', lambda func: func)
        self.admin_required_mock = self.admin_required_patch.start()

        # Patch login_required
        self.login_required_patch = patch('libs.login.login_required', lambda func: func)
        self.login_required_mock = self.login_required_patch.start()
        
        # Patch current_user
        self.current_user_patch = patch('flask_login.utils._get_user')
        self.current_user_mock = self.current_user_patch.start()
        self.current_user_mock.is_authenticated = True
        # self.current_user_mock.return_value = self.admin_user # if you have an admin user object

    def tearDown(self):
        self.admin_required_patch.stop()
        self.login_required_patch.stop()
        self.current_user_patch.stop()
        super().tearDown()

    @patch('services.account_service.TenantService.create_workspace_by_admin')
    def test_admin_create_workspace_success(self, mock_create_workspace):
        mock_tenant = MagicMock(spec=Tenant)
        mock_tenant.id = str(uuid.uuid4())
        mock_tenant.name = "Test Workspace"
        mock_tenant.status = "normal"
        mock_tenant.created_at = "fake_timestamp" # Replace with actual datetime if necessary for marshalling
        
        # Configure the mock to return a dictionary that can be marshalled by workspace_fields
        # This typically means the mock should behave like a Tenant model instance
        # For direct attribute access by marshal:
        mock_tenant.to_dict.return_value = {
            'id': mock_tenant.id,
            'name': mock_tenant.name,
            'status': mock_tenant.status,
            'created_at': mock_tenant.created_at,
        }
        mock_create_workspace.return_value = mock_tenant

        response = self.client.post(
            '/admin/workspaces',
            json={'name': 'Test Workspace'}
            # headers=self.headers if hasattr(self, 'headers') else None
        )

        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertIn('data', response_data)
        # Ensure all expected fields are present
        self.assertEqual(response_data['data']['name'], "Test Workspace")
        self.assertEqual(response_data['data']['id'], mock_tenant.id)
        # Add other assertions for status, created_at if workspace_fields includes them

        mock_create_workspace.assert_called_once()


    def test_admin_create_workspace_missing_name(self):
        response = self.client.post(
            '/admin/workspaces',
            json={}
            # headers=self.headers if hasattr(self, 'headers') else None
        )
        self.assertEqual(response.status_code, 400) # Assuming reqparse handles this

    @patch('services.account_service.TenantService.delete_workspace_by_admin')
    def test_admin_delete_workspace_success(self, mock_delete_workspace):
        mock_delete_workspace.return_value = None # Service returns None on success
        workspace_id = str(uuid.uuid4())

        response = self.client.delete(
            f'/admin/workspaces/{workspace_id}'
            # headers=self.headers if hasattr(self, 'headers') else None
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['result'], 'success')
        mock_delete_workspace.assert_called_once_with(workspace_id=workspace_id, operator_account=self.current_user_mock)


    @patch('services.account_service.TenantService.delete_workspace_by_admin')
    def test_admin_delete_workspace_not_found(self, mock_delete_workspace):
        from services.errors.account import TenantNotFoundError
        workspace_id = str(uuid.uuid4())
        mock_delete_workspace.side_effect = TenantNotFoundError("Workspace not found")

        response = self.client.delete(
            f'/admin/workspaces/{workspace_id}'
            # headers=self.headers if hasattr(self, 'headers') else None
        )

        self.assertEqual(response.status_code, 404) # Assuming a global error handler maps this
        mock_delete_workspace.assert_called_once_with(workspace_id=workspace_id, operator_account=self.current_user_mock)


    @patch('services.account_service.TenantService.delete_workspace_by_admin')
    def test_admin_delete_own_workspace_error(self, mock_delete_workspace):
        from services.errors.account import InvalidActionError
        workspace_id = str(uuid.uuid4())
        mock_delete_workspace.side_effect = InvalidActionError("Cannot delete own workspace")

        response = self.client.delete(
            f'/admin/workspaces/{workspace_id}'
            # headers=self.headers if hasattr(self, 'headers') else None
        )
        # The status code might depend on how InvalidActionError is handled globally
        # Could be 400, 403, or another error code. Let's assume 400 for now.
        self.assertEqual(response.status_code, 400) 
        mock_delete_workspace.assert_called_once_with(workspace_id=workspace_id, operator_account=self.current_user_mock)

    # To test non-admin access, you would typically stop the admin_required_patch
    # or configure current_user_mock to not be an admin.
    # For simplicity, if admin_required is robustly tested elsewhere,
    # these specific non-admin tests might be omitted if they are redundant
    # with tests for the decorator itself.

    # Example for testing non-admin (requires more setup or different patching strategy)
    # def test_admin_create_workspace_non_admin(self):
    #     self.admin_required_mock.stop() # Stop the bypass patch
    #     # Ensure current_user is not admin or setup admin_required to check a flag
    #     # that you can control in the test.
    #     # This might involve patching 'current_user.is_admin_or_owner' if that's used by admin_required
    #
    #     response = self.client.post('/admin/workspaces', json={'name': 'Test NonAdmin'})
    #     self.assertEqual(response.status_code, 401) # Or 403, depending on flask_login behavior
    #
    #     self.admin_required_mock.start() # Restart for other tests


if __name__ == '__main__':
    unittest.main()
