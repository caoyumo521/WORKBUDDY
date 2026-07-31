// 统一 API 客户端

const BASE = import.meta.env.VITE_API || ''  // 通过 vite proxy 走 /api

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers as Record<string, string> || {}),
    },
  })
  if (!r.ok) {
    let msg = r.statusText || `HTTP ${r.status}`
    try {
      const t = await r.text()
      if (t) {
        try {
          const j = JSON.parse(t)
          msg = j.detail || j.message || t
        } catch {
          msg = t
        }
      }
    } catch {}
    throw new Error(msg)
  }
  const ct = r.headers.get('content-type') || ''
  if (ct.includes('application/json')) return (await r.json()) as T
  return (await r.text()) as unknown as T
}

// ===== 类型定义 =====
export type ID = string

export interface Project {
  id: ID
  name: string
  industry: string
  target_market: string
  target_platform: string
  language: string
  visual_style: string
  resolution: string
  aspect_ratio: string
  product_name: string
  product_selling_points: string
  product_target_audience: string
  product_description: string
  extra_requirements: string
  module_plan: { key: string; name_zh: string; quantity?: number }[]
  workdir: string
  status: string
  created_at: string
  updated_at: string
}

export interface Asset {
  id: number
  project_id: string
  asset_type: string
  module_key: string
  seq: number
  language: string
  file_path: string
  url: string
  thumbnail_url: string
  width: number
  height: number
  file_size: number
  prompt: string
  negative_prompt: string
  model: string
  resolution: string
  status: string
  error_message: string
  created_at: string
}

export interface GenerationTask {
  id: number
  project_id: string
  module_key: string
  language: string
  status: 'pending' | 'running' | 'success' | 'failed'
  progress: number
  message: string
  asset_id: number | null
  prompt: string
  model: string
  resolution: string
  aspect_ratio: string
  created_at: string
  finished_at: string | null
}

// ===== API =====
export const api = {
  // Meta
  industries: () => http<any[]>('/api/meta/industries'),
  platforms: () => http<any[]>('/api/meta/platforms'),
  languages: () => http<any[]>('/api/meta/languages'),
  aspectRatios: () => http<any[]>('/api/meta/aspect-ratios'),
  visualStyles: () => http<any[]>('/api/meta/visual-styles'),
  modules: () => http<any[]>('/api/meta/modules'),
  industryPreset: (key: string) => http<{ modules: string[] }>(`/api/meta/industry-preset/${key}`),

  // Settings
  getSettings: () => http<any>('/api/settings'),
  updateSettings: (data: any) =>
    http<any>('/api/settings', { method: 'PUT', body: JSON.stringify(data) }),
  testConnection: (section: 'image' | 'text') =>
    http<{ ok: boolean; message: string; latency_ms?: number }>(
      `/api/settings/test/${section}`,
      { method: 'POST' }
    ),
  testGeneration: () =>
    http<{ ok: boolean; message: string; latency_ms?: number; has_preview?: boolean }>(
      `/api/settings/test_generation`,
      { method: 'POST' }
    ),

  // Projects
  listProjects: () => http<Project[]>('/api/projects'),
  getProject: (id: string) => http<Project>(`/api/projects/${id}`),
  updateProject: (id: string, data: Partial<Project>) =>
    http<Project>(`/api/projects/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteProject: (id: string) => http<{ ok: boolean }>(`/api/projects/${id}`, { method: 'DELETE' }),
  createFromWizard: (data: any) =>
    http<Project>('/api/projects/from-wizard', { method: 'POST', body: JSON.stringify(data) }),

  // Preview sources (for combined preview)
  previewSources: (id: string) => http<any>(`/api/projects/${id}/preview-sources`),

  // Upload
  upload: async (projectId: string, files: File[], assetType = 'product_image') => {
    const fd = new FormData()
    files.forEach((f) => fd.append('files', f))
    fd.append('asset_type', assetType)
    const r = await fetch(`/api/upload/project/${projectId}`, { method: 'POST', body: fd })
    if (!r.ok) throw new Error(await r.text())
    return r.json()
  },
  deleteAsset: (assetId: number) =>
    http<{ ok: boolean }>(`/api/upload/asset/${assetId}`, { method: 'DELETE' }),

  // AI
  aiHelp: (data: any) =>
    http<{ selling_points: string; target_audience: string; visual_direction: string; suggested_modules: string[] }>(
      '/api/ai/help',
      { method: 'POST', body: JSON.stringify(data) }
    ),

  // Generation
  runGeneration: (projectId: string, data: any) =>
    http<{ queued: number; task_ids: number[] }>(`/api/generation/project/${projectId}/run`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  listTasks: (projectId: string) => http<GenerationTask[]>(`/api/generation/project/${projectId}/tasks`),
  retryTask: (taskId: number) =>
    http<{ ok: boolean }>(`/api/generation/task/${taskId}/retry`, { method: 'POST' }),
  listAssets: (projectId: string) => http<Asset[]>(`/api/generation/project/${projectId}/assets`),

  // Export
  exportUrl: (projectId: string, format: 'html' | 'docx' | 'pdf') =>
    `/api/export/project/${projectId}?format=${format}`,
  // File download with format conversion
  fileUrl: (path: string, format?: 'png' | 'jpeg' | 'webp') => {
    const params = new URLSearchParams({ path })
    if (format) params.set('format', format)
    return `/api/files?${params.toString()}`
  },
}
