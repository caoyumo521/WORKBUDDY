import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type Project } from '../lib/api'

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const nav = useNavigate()

  async function refresh() {
    setLoading(true)
    try {
      setProjects(await api.listProjects())
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => {
    refresh()
  }, [])

  async function handleDelete(id: string) {
    if (!confirm('确认删除该项目？所有图片与文档将一并删除。')) return
    await api.deleteProject(id)
    refresh()
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-end justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">项目列表</h1>
          <p className="text-sm text-slate-500 mt-1">所有详情页项目，支持继续编辑、重新生成、导出。</p>
        </div>
        <button className="btn-primary" onClick={() => nav('/projects/new')}>
          + 创建新项目
        </button>
      </div>

      {loading ? (
        <div className="text-slate-400 text-sm py-8 text-center">加载中…</div>
      ) : projects.length === 0 ? (
        <EmptyState onCreate={() => nav('/projects/new')} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} onOpen={() => nav(`/projects/${p.id}`)} onDelete={() => handleDelete(p.id)} />
          ))}
        </div>
      )}
    </div>
  )
}

function ProjectCard({ project, onOpen, onDelete }: { project: Project; onOpen: () => void; onDelete: () => void }) {
  return (
    <div className="card p-4 hover:shadow-md transition cursor-pointer" onClick={onOpen}>
      <div className="flex items-start justify-between">
        <div className="font-medium text-slate-800 truncate pr-2">{project.name}</div>
        <span className={`badge ${statusColor(project.status)}`}>{statusLabel(project.status)}</span>
      </div>
      <div className="text-xs text-slate-500 mt-1 truncate">
        {project.product_name || '(未命名产品)'} · {project.industry || '通用行业'} · {project.language}
      </div>
      <div className="text-xs text-slate-400 mt-2">
        更新于 {new Date(project.updated_at).toLocaleString('zh-CN')}
      </div>
      <div className="flex gap-2 mt-3" onClick={(e) => e.stopPropagation()}>
        <button className="btn-ghost text-xs" onClick={onOpen}>
          打开
        </button>
        <button className="btn-ghost text-xs text-rose-500 hover:bg-rose-50" onClick={onDelete}>
          删除
        </button>
      </div>
    </div>
  )
}

function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="card p-12 text-center">
      <div className="text-5xl mb-3">🎨</div>
      <div className="text-slate-700 font-medium">还没有项目</div>
      <div className="text-slate-400 text-sm mt-1 mb-4">从创建一个 AI 详情页项目开始</div>
      <button className="btn-primary" onClick={onCreate}>
        + 创建新项目
      </button>
    </div>
  )
}

function statusLabel(s: string) {
  return { draft: '草稿', planning: '规划中', generating: '生成中', done: '已完成' }[s] || s
}
function statusColor(s: string) {
  return {
    draft: 'bg-slate-100 text-slate-500',
    planning: 'bg-amber-100 text-amber-700',
    generating: 'bg-blue-100 text-blue-700',
    done: 'bg-emerald-100 text-emerald-700',
  }[s] || 'bg-slate-100 text-slate-500'
}
