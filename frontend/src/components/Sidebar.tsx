import { NavLink, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { api, type Project } from '../lib/api'

export default function Sidebar() {
  const [projects, setProjects] = useState<Project[]>([])
  const nav = useNavigate()

  useEffect(() => {
    api.listProjects().then(setProjects).catch(() => {})
  }, [])

  return (
    <aside className="w-56 border-r border-slate-100 bg-white flex flex-col">
      <div className="px-4 py-4 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-brand-600 grid place-items-center text-white text-sm font-bold">
            A
          </div>
          <div className="text-sm font-semibold">AI 详情页工作台</div>
        </div>
      </div>

      <div className="p-3">
        <button
          onClick={() => nav('/projects/new')}
          className="w-full h-10 rounded-lg border-2 border-dashed border-brand-400 text-brand-600 text-sm font-medium hover:bg-brand-50"
        >
          + 创建新项目
        </button>
      </div>

      <div className="px-3 py-1 text-xs text-slate-400 font-medium">历史项目</div>
      <nav className="flex-1 overflow-y-auto px-2">
        {projects.length === 0 && (
          <div className="text-xs text-slate-400 px-2 py-3">暂无项目</div>
        )}
        {projects.map((p) => (
          <NavLink
            key={p.id}
            to={`/projects/${p.id}`}
            className={({ isActive }) =>
              `block px-3 py-2 rounded-md text-sm mb-0.5 truncate ${
                isActive ? 'bg-brand-50 text-brand-700 font-medium' : 'text-slate-700 hover:bg-slate-50'
              }`
            }
            title={p.name}
          >
            {p.name}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-slate-100">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-2 px-3 py-2 rounded-md text-sm ${
              isActive ? 'bg-brand-50 text-brand-700 font-medium' : 'text-slate-600 hover:bg-slate-50'
            }`
          }
        >
          <span>⚙</span>
          <span>系统设置</span>
        </NavLink>
      </div>
      <div className="px-3 pb-3 text-xs text-slate-400">
        v0.1.0 · 本地版
      </div>
    </aside>
  )
}
