import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import AdminWorkspacesPage from './admin_workspaces_page' // Adjust path if necessary
import { AppContext } from '@/context/app-context'
import { WorkspacesContext } from '@/context/workspace-context' // Assuming this is the correct path
import { createWorkspace, deleteWorkspace } from '@/service/common'
import Toast from '@/app/components/base/toast'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    replace: jest.fn(),
  }),
}))

// Mock react-i18next
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: any) => {
      if (params) {
        let AKey = key
        for (const k in params)
          AKey = AKey.replace(`{{${k}}}`, params[k])

        return AKey
      }
      return key
    },
  }),
}))

// Mock service functions
jest.mock('@/service/common', () => ({
  createWorkspace: jest.fn(),
  deleteWorkspace: jest.fn(),
}))

// Mock Toast
jest.mock('@/app/components/base/toast', () => ({
  notify: jest.fn(),
}))

const mockUserProfileAdmin = {
  id: 'admin-user-id',
  name: 'Admin User',
  email: 'admin@example.com',
  is_admin_or_owner: true,
}

const mockUserProfileNormal = {
  id: 'normal-user-id',
  name: 'Normal User',
  email: 'user@example.com',
  is_admin_or_owner: false,
}

const mockWorkspaces = [
  { id: 'ws1', name: 'Workspace 1', status: 'normal', created_at: Date.now() / 1000, role: 'admin' },
  { id: 'ws2', name: 'Workspace 2', status: 'normal', created_at: Date.now() / 1000, role: 'normal' },
]

const mockCurrentWorkspace = {
  id: 'ws1',
  name: 'Workspace 1',
  plan: 'basic',
  status: 'normal',
  created_at: Date.now() / 1000,
  role: 'admin',
  in_trial: false,
  trial_end_reason: null,
  custom_config: {},
}

const renderPage = (
  userProfile: any = mockUserProfileAdmin,
  workspaces: any[] = [],
  isLoadingWorkspaces: boolean = false,
  currentWs: any = mockCurrentWorkspace,
) => {
  return render(
    <AppContext.Provider value={{ userProfile, currentWorkspace: currentWs } as any}>
      <WorkspacesContext.Provider
        value={{
          workspaces,
          isLoading: isLoadingWorkspaces,
          triggerWorkspacesUpdate: jest.fn(),
        } as any}
      >
        <AdminWorkspacesPage />
      </WorkspacesContext.Provider>
    </AppContext.Provider>,
  )
}

describe('AdminWorkspacesPage', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks()
  })

  // 1. Admin Access and Rendering
  describe('Admin Access and Rendering', () => {
    it('should render main elements for admin with no workspaces', () => {
      renderPage(mockUserProfileAdmin, [], false)
      expect(screen.getByText('admin.workspaces.manageTitle')).toBeInTheDocument()
      // The create button key might be different, e.g. admin.workspaces.createWorkspace
      expect(screen.getByText('admin.workspaces.createWorkspace')).toBeInTheDocument()
      // The no workspaces key might be different, e.g. admin.workspaces.noWorkspaces
      expect(screen.getByText('admin.workspaces.noWorkspaces')).toBeInTheDocument()
    })
  })

  // 2. Non-Admin Access
  describe('Non-Admin Access', () => {
    it('should show access denied for non-admin user', () => {
      const mockRouterReplace = jest.fn()
      jest.spyOn(require('next/navigation'), 'useRouter').mockImplementationOnce(() => ({ replace: mockRouterReplace }))
      renderPage(mockUserProfileNormal, [], false)
      expect(screen.getByText('admin.workspaces.accessDenied')).toBeInTheDocument()
      expect(mockRouterReplace).toHaveBeenCalledWith('/')
    })

    it('should show loading user info if userProfile is undefined', () => {
      renderPage(undefined, [], false)
      expect(screen.getByText('admin.workspaces.loadingUserInfo')).toBeInTheDocument()
    })
  })

  // 3. Workspace Creation Modal
  describe('Workspace Creation Modal', () => {
    it('should open creation modal, allow input, and submit successfully', async () => {
      const triggerUpdateMock = jest.fn()
      (createWorkspace as jest.Mock).mockResolvedValueOnce({ data: { id: 'new-ws-id' }, message: 'Success' })

      render(
        <AppContext.Provider value={{ userProfile: mockUserProfileAdmin, currentWorkspace: mockCurrentWorkspace } as any}>
          <WorkspacesContext.Provider
            value={{
              workspaces: [],
              isLoading: false,
              triggerWorkspacesUpdate: triggerUpdateMock,
            } as any}
          >
            <AdminWorkspacesPage />
          </WorkspacesContext.Provider>
        </AppContext.Provider>,
      )

      fireEvent.click(screen.getByText('admin.workspaces.createWorkspace'))
      expect(screen.getByText('admin.workspaces.createModalTitle')).toBeInTheDocument()
      expect(screen.getByLabelText('admin.workspaces.workspaceNameLabel')).toBeInTheDocument()

      const inputField = screen.getByPlaceholderText('admin.workspaces.workspaceNamePlaceholder')
      fireEvent.change(inputField, { target: { value: 'New Test Workspace' } })
      expect(inputField).toHaveValue('New Test Workspace')

      fireEvent.click(screen.getByText('admin.workspaces.submitButton'))

      await waitFor(() => {
        expect(createWorkspace).toHaveBeenCalledWith('New Test Workspace')
        expect(Toast.notify).toHaveBeenCalledWith({ type: 'success', message: 'admin.workspaces.createSuccessToast' })
        expect(triggerUpdateMock).toHaveBeenCalled()
      })
    })

    it('should show error toast on creation API failure', async () => {
      (createWorkspace as jest.Mock).mockRejectedValueOnce(new Error('API Error'))
       renderPage()

      fireEvent.click(screen.getByText('admin.workspaces.createWorkspace'))
      const inputField = screen.getByPlaceholderText('admin.workspaces.workspaceNamePlaceholder')
      fireEvent.change(inputField, { target: { value: 'Fail Workspace' } })
      fireEvent.click(screen.getByText('admin.workspaces.submitButton'))

      await waitFor(() => {
        expect(createWorkspace).toHaveBeenCalledWith('Fail Workspace')
        expect(Toast.notify).toHaveBeenCalledWith({ type: 'error', message: 'admin.workspaces.createErrorToastGeneral' })
      })
    })

    it('should show error toast if workspace name is empty', () => {
      renderPage()
      fireEvent.click(screen.getByText('admin.workspaces.createWorkspace'))
      fireEvent.click(screen.getByText('admin.workspaces.submitButton'))
      expect(Toast.notify).toHaveBeenCalledWith({ type: 'error', message: 'admin.workspaces.nameNotEmptyToast' })
      expect(createWorkspace).not.toHaveBeenCalled()
    })
  })

  // 4. Workspace Listing and Deletion
  describe('Workspace Listing and Deletion', () => {
    it('should list workspaces and disable delete for current workspace', () => {
      renderPage(mockUserProfileAdmin, mockWorkspaces, false, mockCurrentWorkspace)
      expect(screen.getByText(mockWorkspaces[0].name)).toBeInTheDocument()
      expect(screen.getByText(mockWorkspaces[1].name)).toBeInTheDocument()

      const deleteButtons = screen.getAllByText('admin.workspaces.deleteButton')
      // Assuming ws1 is currentWorkspace
      expect(deleteButtons[0]).toBeDisabled()
      expect(deleteButtons[1]).not.toBeDisabled()
    })

    it('should open delete confirmation modal and delete successfully', async () => {
      const triggerUpdateMock = jest.fn();
      (deleteWorkspace as jest.Mock).mockResolvedValueOnce({ result: 'success' })
      
      render(
        <AppContext.Provider value={{ userProfile: mockUserProfileAdmin, currentWorkspace: mockCurrentWorkspace } as any}>
          <WorkspacesContext.Provider
            value={{
              workspaces: mockWorkspaces, // ws1 (current), ws2
              isLoading: false,
              triggerWorkspacesUpdate: triggerUpdateMock,
            } as any}
          >
            <AdminWorkspacesPage />
          </WorkspacesContext.Provider>
        </AppContext.Provider>,
      )

      const deleteButtons = screen.getAllByText('admin.workspaces.deleteButton')
      fireEvent.click(deleteButtons[1]) // Click delete for ws2

      expect(screen.getByText('admin.workspaces.deleteModalTitle')).toBeInTheDocument()
      expect(screen.getByText('admin.workspaces.deleteConfirmText')).toBeInTheDocument()

      fireEvent.click(screen.getByText('admin.workspaces.confirmDeleteButton'))

      await waitFor(() => {
        expect(deleteWorkspace).toHaveBeenCalledWith(mockWorkspaces[1].id)
        expect(Toast.notify).toHaveBeenCalledWith({ type: 'success', message: 'admin.workspaces.deleteSuccessToast' })
        expect(triggerUpdateMock).toHaveBeenCalled()
      })
    })

    it('should show error toast on deletion API failure', async () => {
      (deleteWorkspace as jest.Mock).mockRejectedValueOnce(new Error('API Deletion Error'))
      renderPage(mockUserProfileAdmin, mockWorkspaces, false, mockCurrentWorkspace)

      const deleteButtons = screen.getAllByText('admin.workspaces.deleteButton')
      fireEvent.click(deleteButtons[1]) // Click delete for ws2

      fireEvent.click(screen.getByText('admin.workspaces.confirmDeleteButton'))

      await waitFor(() => {
        expect(deleteWorkspace).toHaveBeenCalledWith(mockWorkspaces[1].id)
        expect(Toast.notify).toHaveBeenCalledWith({ type: 'error', message: 'admin.workspaces.deleteErrorToastGeneral' })
      })
    })
  })
})
