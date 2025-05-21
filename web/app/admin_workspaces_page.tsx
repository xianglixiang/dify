'use client'

import React, { useState, useCallback, useContext } from 'react'
import { useRouter } from 'next/navigation'
import { useTranslation } from 'react-i18next'
import Button from '@/app/components/base/button'
import { Input } from '@/app/components/base/input'
import Modal from '@/app/components/base/modal'
import { AppContext } from '@/context/app-context'
import { useWorkspacesContext } from '@/context/workspace-context'
import { createWorkspace, deleteWorkspace } from '@/service/common'
import Toast from '@/app/components/base/toast'
import type { IWorkspace } from '@/models/common'
import { AlertTriangle } from 'lucide-react'

const AdminWorkspacesPage = () => {
  const { t } = useTranslation()
  const router = useRouter()
  const { userProfile, currentWorkspace } = useContext(AppContext)
  const { workspaces, isLoading: isLoadingWorkspaces, triggerWorkspacesUpdate } = useWorkspacesContext()

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [newWorkspaceName, setNewWorkspaceName] = useState('')
  const [isSubmittingCreate, setIsSubmittingCreate] = useState(false)

  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [workspaceToDelete, setWorkspaceToDelete] = useState<IWorkspace | null>(null)
  const [isSubmittingDelete, setIsSubmittingDelete] = useState(false)

  // Admin check
  if (userProfile && !userProfile.is_admin_or_owner) {
    // Redirect to home or show access denied
    router.replace('/') // Or a dedicated access-denied page
    return (
      <div className="flex h-full items-center justify-center">
        <p>Access Denied. You must be an admin to view this page.</p>
      </div>
    )
  }
  // Handle case where userProfile is not yet loaded
  if (userProfile === undefined) {
    return (
      <div className="flex h-full items-center justify-center">
        <p>{t('admin.workspaces.loadingUserInfo')}</p>
      </div>
    )
  }
  // Admin check
  if (userProfile && !userProfile.is_admin_or_owner) {
    // Redirect to home or show access denied
    router.replace('/') // Or a dedicated access-denied page
    return (
      <div className="flex h-full items-center justify-center">
        <p>{t('admin.workspaces.accessDenied')}</p>
      </div>
    )
  }

  const handleOpenCreateModal = () => {
    setNewWorkspaceName('')
    setIsCreateModalOpen(true)
  }

  const handleCloseCreateModal = () => {
    if (!isSubmittingCreate)
      setIsCreateModalOpen(false)
  }

  const handleCreateSubmit = async () => {
    if (!newWorkspaceName.trim()) {
      Toast.notify({ type: 'error', message: t('admin.workspaces.nameNotEmptyToast') })
      return
    }
    setIsSubmittingCreate(true)
    try {
      const result = await createWorkspace(newWorkspaceName.trim())
      if (result && result.data && result.data.id) {
        Toast.notify({ type: 'success', message: t('admin.workspaces.createSuccessToast', { name: newWorkspaceName.trim() }) })
        triggerWorkspacesUpdate()
        handleCloseCreateModal()
      } else {
        Toast.notify({ type: 'error', message: (result && result.message) || t('admin.workspaces.createErrorToastFallback') })
      }
    } catch (error: any) {
      Toast.notify({ type: 'error', message: error.message || t('admin.workspaces.createErrorToastGeneral') })
    } finally {
      setIsSubmittingCreate(false)
    }
  }

  const handleOpenDeleteModal = (workspace: IWorkspace) => {
    setWorkspaceToDelete(workspace)
    setIsDeleteModalOpen(true)
  }

  const handleCloseDeleteModal = () => {
    if (!isSubmittingDelete) {
      setWorkspaceToDelete(null)
      setIsDeleteModalOpen(false)
    }
  }

  const handleDeleteSubmit = async () => {
    if (!workspaceToDelete)
      return

    setIsSubmittingDelete(true)
    try {
      const result = await deleteWorkspace(workspaceToDelete.id)
      if (result && result.result === 'success') {
        Toast.notify({ type: 'success', message: t('admin.workspaces.deleteSuccessToast', { name: workspaceToDelete.name }) })
        triggerWorkspacesUpdate()
        handleCloseDeleteModal()
      } else {
        Toast.notify({ type: 'error', message: (result && result.message) || t('admin.workspaces.deleteErrorToastFallback') })
      }
    } catch (error: any) {
      Toast.notify({ type: 'error', message: error.message || t('admin.workspaces.deleteErrorToastGeneral') })
    } finally {
      setIsSubmittingDelete(false)
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold text-gray-900">{t('admin.workspaces.manageTitle')}</h1>
      <div className="mt-6">
        <Button variant="primary" onClick={handleOpenCreateModal}>
          {t('admin.workspaces.createWorkspace')}
        </Button>
      </div>

      {isCreateModalOpen && (
        <Modal
          isOpen={isCreateModalOpen}
          onClose={handleCloseCreateModal}
          title={t('admin.workspaces.createModalTitle')}
          wrapperClassName='!z-[101]'
        >
          <div className="mt-4">
            <label htmlFor="newWorkspaceName" className="block text-sm font-medium text-gray-700">
              {t('admin.workspaces.workspaceNameLabel')}
            </label>
            <Input
              type="text"
              id="newWorkspaceName"
              value={newWorkspaceName}
              onChange={e => setNewWorkspaceName(e.target.value)}
              className="mt-1 block w-full"
              placeholder={t('admin.workspaces.workspaceNamePlaceholder')}
            />
          </div>
          <div className="mt-6 flex justify-end space-x-2">
            <Button variant="normal" onClick={handleCloseCreateModal} disabled={isSubmittingCreate}>
              {t('admin.workspaces.cancelButton')}
            </Button>
            <Button variant="primary" onClick={handleCreateSubmit} loading={isSubmittingCreate} disabled={isSubmittingCreate}>
              {t('admin.workspaces.submitButton')}
            </Button>
          </div>
        </Modal>
      )}

      <div className="mt-8">
        {isLoadingWorkspaces && <p>{t('admin.workspaces.loadingWorkspaces')}</p>}
        {!isLoadingWorkspaces && (!workspaces || workspaces.length === 0) && (
          <p className="text-gray-500">{t('admin.workspaces.noWorkspaces')}</p>
        )}
        {!isLoadingWorkspaces && workspaces && workspaces.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('admin.workspaces.tableHeaderName')}</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('admin.workspaces.tableHeaderID')}</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('admin.workspaces.tableHeaderStatus')}</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('admin.workspaces.tableHeaderActions')}</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {workspaces.map(ws => (
                  <tr key={ws.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{ws.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{ws.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{ws.status}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Button
                        variant='danger'
                        onClick={() => handleOpenDeleteModal(ws)}
                        disabled={ws.id === currentWorkspace.id || isSubmittingDelete}
                        className="text-red-600 hover:text-red-900 disabled:text-gray-400"
                      >
                        {t('admin.workspaces.deleteButton')}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {isDeleteModalOpen && workspaceToDelete && (
        <Modal
          isOpen={isDeleteModalOpen}
          onClose={handleCloseDeleteModal}
          title={t('admin.workspaces.deleteModalTitle')}
          wrapperClassName='!z-[101]'
        >
          <div className="mt-4">
            <div className='flex items-center'>
              <AlertTriangle className="h-6 w-6 text-red-600 mr-2" />
              <p className="text-sm text-gray-700">
                {t('admin.workspaces.deleteConfirmText', { workspaceName: workspaceToDelete.name })}
              </p>
            </div>
          </div>
          <div className="mt-6 flex justify-end space-x-2">
            <Button variant="normal" onClick={handleCloseDeleteModal} disabled={isSubmittingDelete}>
              {t('admin.workspaces.cancelButton')}
            </Button>
            <Button variant="danger" onClick={handleDeleteSubmit} loading={isSubmittingDelete} disabled={isSubmittingDelete}>
              {t('admin.workspaces.confirmDeleteButton')}
            </Button>
          </div>
        </Modal>
      )}
    </div>
  )
}

export default AdminWorkspacesPage
