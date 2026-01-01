import { useEffect, useMemo, useState } from 'react'
import { fetchJson, isApiError, uploadMultipart } from '../lib/api'
import type { ApiList, Artifact, Folder } from '../lib/types'
import { formatDate } from '../lib/utils'

const STORAGE_KEY = 'ec:selectedFolderId'

type LibraryPaneProps = {
  onTraceCapture?: (traceId: string | null) => void
}

// Left pane: folders, uploads, and artifacts list with detail drawer.
export function LibraryPane({ onTraceCapture }: LibraryPaneProps) {
  const [folders, setFolders] = useState<Folder[]>([])
  const [foldersLoading, setFoldersLoading] = useState(true)
  const [foldersError, setFoldersError] = useState<string | null>(null)
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null)

  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [artifactsLoading, setArtifactsLoading] = useState(false)
  const [artifactsError, setArtifactsError] = useState<string | null>(null)

  const [drawerArtifact, setDrawerArtifact] = useState<Artifact | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [createName, setCreateName] = useState('')

  const shouldPoll = useMemo(
    () => artifacts.some((artifact) => ['queued', 'running'].includes(String(artifact.ingestion_status))),
    [artifacts],
  )

  const loadFolders = async () => {
    setFoldersLoading(true)
    setFoldersError(null)
    try {
      const { data } = await fetchJson<ApiList<Folder>>('/folders')
      const items = data.items ?? []
      setFolders(items)
      setFoldersLoading(false)

      if (items.length === 0) {
        setSelectedFolderId(null)
        return
      }

      const saved = localStorage.getItem(STORAGE_KEY)
      const stillValid = saved && items.some((folder) => folder.id === saved)
      const nextId = stillValid ? saved : items[0].id
      setSelectedFolderId(nextId)
    } catch (error) {
      setFoldersLoading(false)
      setFoldersError(isApiError(error) ? error.message : 'Failed to load folders')
      onTraceCapture?.(isApiError(error) ? error.traceId ?? null : null)
    }
  }

  const loadArtifacts = async (folderId: string) => {
    setArtifactsLoading(true)
    setArtifactsError(null)
    try {
      const { data } = await fetchJson<ApiList<Artifact>>(`/folders/${folderId}/artifacts`)
      setArtifacts(data.items ?? [])
      setArtifactsLoading(false)
    } catch (error) {
      setArtifactsLoading(false)
      setArtifactsError(isApiError(error) ? error.message : 'Failed to load artifacts')
      onTraceCapture?.(isApiError(error) ? error.traceId ?? null : null)
    }
  }

  useEffect(() => {
    loadFolders()
  }, [])

  useEffect(() => {
    if (!selectedFolderId) return
    localStorage.setItem(STORAGE_KEY, selectedFolderId)
    loadArtifacts(selectedFolderId)
  }, [selectedFolderId])

  useEffect(() => {
    if (!selectedFolderId || !shouldPoll) return
    const interval = setInterval(() => {
      loadArtifacts(selectedFolderId)
    }, 2000)
    return () => clearInterval(interval)
  }, [selectedFolderId, shouldPoll])

  const handleCreateFolder = async () => {
    const name = createName.trim()
    if (!name) return
    setCreateName('')
    try {
      const { data } = await fetchJson<Folder>('/folders', {
        method: 'POST',
        body: { name },
      })
      setFolders((prev) => [...prev, data])
      setSelectedFolderId(data.id)
    } catch (error) {
      setFoldersError(isApiError(error) ? error.message : 'Failed to create folder')
      onTraceCapture?.(isApiError(error) ? error.traceId ?? null : null)
    }
  }

  const handleUpload = async (file: File) => {
    if (!selectedFolderId) return
    setUploading(true)
    setUploadError(null)
    try {
      const form = new FormData()
      form.append('folder_id', selectedFolderId)
      form.append('file', file)
      await uploadMultipart<Artifact>('/artifacts/upload', form)
      await loadArtifacts(selectedFolderId)
    } catch (error) {
      const message = isApiError(error) ? error.message : 'Upload failed'
      const trace = isApiError(error) ? error.traceId ?? null : null
      setUploadError(trace ? `${message} (trace ${trace})` : message)
      onTraceCapture?.(trace)
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (artifactId: string) => {
    if (!selectedFolderId) return
    try {
      await fetchJson<{ ok: boolean }>(`/artifacts/${artifactId}`, { method: 'DELETE' })
      await loadArtifacts(selectedFolderId)
      if (drawerArtifact?.id === artifactId) {
        setDrawerArtifact(null)
      }
    } catch (error) {
      setArtifactsError(isApiError(error) ? error.message : 'Delete failed')
      onTraceCapture?.(isApiError(error) ? error.traceId ?? null : null)
    }
  }

  return (
    <div className="pane-content">
      <header className="pane-header">
        <div>
          <h2>Library</h2>
          <p>Organize artifacts into folders, upload, and monitor ingestion.</p>
        </div>
        <button type="button" className="button button--ghost" onClick={loadFolders}>
          Refresh
        </button>
      </header>

      <div className="pane-scroll">
        <section className="card section">
          <div className="section-title">Folders</div>
          {foldersLoading ? (
            <SkeletonRows count={3} />
          ) : foldersError ? (
            <div className="empty-state error">{foldersError}</div>
          ) : folders.length === 0 ? (
            <div className="empty-state">Create your first folder to begin.</div>
          ) : (
            <FolderList
              folders={folders}
              selectedId={selectedFolderId}
              onSelect={setSelectedFolderId}
            />
          )}

          <div className="inline-form">
            <input
              type="text"
              value={createName}
              placeholder="New folder name"
              onChange={(event) => setCreateName(event.target.value)}
            />
            <button type="button" className="button" onClick={handleCreateFolder}>
              Create
            </button>
          </div>
        </section>

        <section className="card section">
          <div className="section-title">Upload</div>
          {!selectedFolderId ? (
            <div className="empty-state">Select a folder to upload artifacts.</div>
          ) : (
            <UploadArtifactForm uploading={uploading} onUpload={handleUpload} />
          )}
          {uploadError && <div className="empty-state error">{uploadError}</div>}
        </section>

        <section className="card section section--grow">
          <div className="section-title">Artifacts</div>
          {artifactsLoading ? (
            <SkeletonRows count={4} />
          ) : artifactsError ? (
            <div className="empty-state error">{artifactsError}</div>
          ) : !selectedFolderId ? (
            <div className="empty-state">Pick a folder to see its artifacts.</div>
          ) : artifacts.length === 0 ? (
            <div className="empty-state">Upload your first doc to start ingestion.</div>
          ) : (
            <ArtifactsTable
              artifacts={artifacts}
              onSelect={setDrawerArtifact}
              onDelete={handleDelete}
            />
          )}
        </section>
      </div>

      {drawerArtifact && (
        <ArtifactDetailDrawer
          artifact={drawerArtifact}
          onClose={() => setDrawerArtifact(null)}
        />
      )}
    </div>
  )
}

function FolderList({
  folders,
  selectedId,
  onSelect,
}: {
  folders: Folder[]
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  return (
    <div className="folder-list">
      {folders.map((folder) => (
        <button
          key={folder.id}
          type="button"
          className={`folder-item ${selectedId === folder.id ? 'folder-item--active' : ''}`}
          onClick={() => onSelect(folder.id)}
        >
          <span>{folder.name}</span>
          <span className="muted">{formatDate(folder.created_at)}</span>
        </button>
      ))}
    </div>
  )
}

function UploadArtifactForm({
  uploading,
  onUpload,
}: {
  uploading: boolean
  onUpload: (file: File) => void
}) {
  return (
    <label className="upload">
      <input
        type="file"
        disabled={uploading}
        onChange={(event) => {
          const file = event.target.files?.[0]
          if (file) onUpload(file)
          event.currentTarget.value = ''
        }}
      />
      <div>
        <div className="upload__title">Upload a document</div>
        <div className="upload__subtitle">PDF, DOCX, MD, or TXT · 20MB max</div>
      </div>
      <span className="pill">{uploading ? 'Uploading…' : 'Choose file'}</span>
    </label>
  )
}

function ArtifactsTable({
  artifacts,
  onSelect,
  onDelete,
}: {
  artifacts: Artifact[]
  onSelect: (artifact: Artifact) => void
  onDelete: (artifactId: string) => void
}) {
  return (
    <div className="artifacts">
      {artifacts.map((artifact) => (
        <div key={artifact.id} className="artifact-row">
          <button
            type="button"
            className="artifact-main"
            onClick={() => onSelect(artifact)}
          >
            <div>
              <div className="artifact-name">{artifact.filename}</div>
              <div className="muted">{artifact.ingestion_stage ?? 'pending stage'}</div>
            </div>
            <div className="artifact-meta">
              <span className={`status status--${artifact.ingestion_status ?? 'queued'}`}>
                {artifact.ingestion_status ?? 'queued'}
              </span>
              <span className="muted">{formatDate(artifact.updated_at ?? artifact.created_at)}</span>
            </div>
          </button>
          <button
            type="button"
            className="icon-button"
            onClick={() => onDelete(artifact.id)}
            aria-label="Delete artifact"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  )
}

function ArtifactDetailDrawer({
  artifact,
  onClose,
}: {
  artifact: Artifact
  onClose: () => void
}) {
  const status = artifact.ingestion_status ?? 'queued'
  const preview = artifact.extracted_text_preview

  return (
    <div className="drawer" role="dialog" aria-modal="true">
      <div className="drawer__content">
        <header className="drawer__header">
          <div>
            <div className="drawer__title">{artifact.filename}</div>
            <div className="muted">
              Status: {status} · Stage: {artifact.ingestion_stage ?? 'pending'}
            </div>
          </div>
          <button type="button" className="icon-button" onClick={onClose}>
            Close
          </button>
        </header>

        <div className="drawer__section">
          <div className="section-title">Extracted preview</div>
          {status === 'failed' && artifact.error_message ? (
            <div className="empty-state error">{artifact.error_message}</div>
          ) : preview ? (
            <pre className="preview">{preview}</pre>
          ) : (
            <div className="empty-state">Pending extraction. Check back soon.</div>
          )}
        </div>

        <div className="drawer__section">
          <div className="section-title">Metadata</div>
          <div className="meta-grid">
            <div>
              <div className="muted">Artifact ID</div>
              <div>{artifact.id}</div>
            </div>
            <div>
              <div className="muted">Folder ID</div>
              <div>{artifact.folder_id}</div>
            </div>
            <div>
              <div className="muted">Content type</div>
              <div>{artifact.content_type ?? '—'}</div>
            </div>
            <div>
              <div className="muted">Updated</div>
              <div>{formatDate(artifact.updated_at ?? artifact.created_at)}</div>
            </div>
          </div>
        </div>
      </div>
      <div className="drawer__backdrop" onClick={onClose} />
    </div>
  )
}

function SkeletonRows({ count = 3 }: { count?: number }) {
  return (
    <div className="skeleton-stack">
      {Array.from({ length: count }).map((_, index) => (
        <div key={`skeleton-${index}`} className="skeleton" />
      ))}
    </div>
  )
}
