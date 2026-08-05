import { useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, type Asset, type GenerationTask, type Project } from '../lib/api'

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [project, setProject] = useState<Project | null>(null)
  const [assets, setAssets] = useState<Asset[]>([])
  const [tasks, setTasks] = useState<GenerationTask[]>([])
  const [generating, setGenerating] = useState(false)
  const [previewAsset, setPreviewAsset] = useState<Asset | null>(null)
  const [showCombined, setShowCombined] = useState(false)
  const pollRef = useRef<number | null>(null)

  // 产品需求·可编辑（生成后也能完善）
  const [req, setReq] = useState({ selling: '', desc: '', extra: '' })
  const [reqBusy, setReqBusy] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const reqFileRef = useRef<HTMLInputElement>(null)
  useEffect(() => {
    if (project) {
      setReq({
        selling: project.product_selling_points || '',
        desc: project.product_description || '',
        extra: project.extra_requirements || '',
      })
    }
  }, [project?.id])

  async function load() {
    if (!id) return
    const [p, a, t] = await Promise.all([
      api.getProject(id),
      api.listAssets(id),
      api.listTasks(id),
    ])
    setProject(p)
    setAssets(a)
    setTasks(t)
  }

  useEffect(() => {
    load()
  }, [id])

  // 轮询任务
  useEffect(() => {
    function tick() {
      if (!id) return
      api.listTasks(id).then(setTasks).catch(() => {})
      api.listAssets(id).then(setAssets).catch(() => {})
    }
    pollRef.current = window.setInterval(tick, 2000) as any
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current)
    }
  }, [id])

  const hasRunning = tasks.some((t) => t.status === 'running' || t.status === 'pending')
  useEffect(() => {
    setGenerating(hasRunning)
  }, [hasRunning])

  async function handleGenerate(moduleKeys?: string[]) {
    if (!id) return
    setGenerating(true)
    await api.runGeneration(id, { module_keys: moduleKeys })
  }

  async function handleRetry(taskId: number) {
    await api.retryTask(taskId)
  }

  async function handleDeleteAsset(asset: Asset) {
    if (!confirm('删除这张图？')) return
    await api.deleteAsset(asset.id)
    load()
  }

  async function handleUploadStyleRef(file: File) {
    if (!id) return
    await api.upload(id, [file], 'style_reference')
    await load()
  }

  async function saveRequirements(regenerate: boolean) {
    if (!id) return
    setReqBusy(true)
    try {
      await api.updateProject(id, {
        product_selling_points: req.selling,
        product_description: req.desc,
        extra_requirements: req.extra,
      })
      await load()
      if (regenerate) await handleGenerate()
    } catch (e: any) {
      alert('保存失败：' + e.message)
    } finally {
      setReqBusy(false)
    }
  }

  async function handleAnalyzeReq(file: File) {
    if (!id || !project) return
    setAnalyzing(true)
    try {
      const r: any = await api.analyzeImage(
        {
          productName: project.product_name,
          industry: project.industry,
          language: project.language,
          visualStyle: project.visual_style,
        },
        file,
      )
      if (r._error) {
        alert('视觉分析暂不可用：' + r._error + '\n你可以手动编辑卖点。')
        return
      }
      setReq((prev) => ({
        selling: r.selling_points || prev.selling,
        desc: r.description || prev.desc,
        extra:
          (prev.extra ? prev.extra + '\n' : '') +
          (r.suggested_extra ? `[AI 图析] ${r.suggested_extra}` : ''),
      }))
    } catch (e: any) {
      alert('图片分析失败：' + e.message)
    } finally {
      setAnalyzing(false)
    }
  }

  if (!project) return <div className="p-8 text-slate-400">加载中…</div>

  const generated = assets.filter((a) => a.asset_type === 'generated' || a.asset_type === 'composed')
  const finalAssets = preferComposed(generated)
  const productImgs = assets.filter((a) => a.asset_type === 'product_image')
  const styleRefs = assets.filter((a) => a.asset_type === 'style_reference')
  const moduleGroups = groupByModule(finalAssets, project.module_plan)
  const combinedPreviewUrl = id ? `/api/files/preview/${id}` : ''

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="text-xs text-slate-400 mb-1">
            <Link to="/" className="hover:underline">项目列表</Link> / <span>{project.name}</span>
          </div>
          <h1 className="text-2xl font-semibold text-slate-800">{project.name}</h1>
          <div className="text-sm text-slate-500 mt-1 flex gap-3 flex-wrap">
            <span>{project.industry || '通用行业'}</span>
            <span>·</span>
            <span>{project.target_market}</span>
            <span>·</span>
            <span>{project.target_platform}</span>
            <span>·</span>
            <span>{project.language}</span>
            <span>·</span>
            <span>{project.resolution} / {project.aspect_ratio}</span>
          </div>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            className="btn-secondary"
            disabled={generating || finalAssets.length === 0}
            onClick={() => setShowCombined(true)}
            title="将所有已生成图片拼合为完整详情页预览"
          >
            🖼 组合预览
          </button>
          <button
            className="btn-secondary"
            disabled={generating}
            onClick={() => handleGenerate()}
          >
            {generating ? '生成中…' : '▶ 一键生成所有模块'}
          </button>
          <a
            className="btn-primary"
            href={api.exportUrl(project.id, 'html')}
            target="_blank"
            rel="noreferrer"
          >
            ⬇ 导出 HTML
          </a>
          <a
            className="btn-secondary"
            href={api.exportUrl(project.id, 'docx')}
          >
            Word
          </a>
          <a
            className="btn-secondary"
            href={api.exportUrl(project.id, 'pdf')}
          >
            PDF
          </a>
        </div>
      </div>

      {/* 产品图 */}
      {productImgs.length > 0 && (
        <section className="card p-4 mb-6">
          <div className="text-sm font-medium text-slate-700 mb-3">产品原图（{productImgs.length}）</div>
          <div className="flex gap-3 flex-wrap">
            {productImgs.map((a) => (
              <div key={a.id} className="w-24 h-24 rounded-md overflow-hidden border border-slate-200 bg-slate-50 group relative">
                <img src={a.url} className="w-full h-full object-cover" />
                <button
                  className="absolute top-1 right-1 w-5 h-5 rounded-full bg-white/90 text-rose-500 text-xs hidden group-hover:grid place-items-center"
                  onClick={() => handleDeleteAsset(a)}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 风格参考图（统一调性，最强一致性锚点） */}
      <section className="card p-4 mb-6 border-brand-100">
        <div className="text-sm font-medium text-slate-700 mb-1">风格参考图（统一调性）</div>
        <div className="text-xs text-slate-400 mb-3">
          上传一张最能代表你想要的「色调 / 光影 / 质感」的图。重新生成时，所有模块都会对齐这同一套调性，整页上下一致。
        </div>
        <div className="flex gap-3 items-center flex-wrap">
          {styleRefs.map((a) => (
            <div key={a.id} className="w-24 h-24 rounded-md overflow-hidden border border-slate-200 bg-slate-50 group relative">
              <img src={a.url} className="w-full h-full object-cover" />
              <button
                className="absolute top-1 right-1 w-5 h-5 rounded-full bg-white/90 text-rose-500 text-xs hidden group-hover:grid place-items-center"
                onClick={() => handleDeleteAsset(a)}
                title="删除风格参考图"
              >
                ×
              </button>
            </div>
          ))}
          <label className="w-24 h-24 rounded-md border-2 border-dashed border-slate-300 grid place-items-center text-slate-400 text-xs cursor-pointer hover:border-brand-400 hover:text-brand-500 transition">
            + 上传参考
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) handleUploadStyleRef(f)
                e.target.value = ''
              }}
            />
          </label>
        </div>
      </section>

      {/* 产品需求 · 可编辑（生成后也能完善，上传图自动提炼卖点） */}
      <section className="card p-4 mb-6 border-slate-200">
        <div className="flex items-center justify-between mb-1">
          <div className="text-sm font-medium text-slate-700">产品需求 · 可编辑</div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="text-sm text-brand-600 hover:underline flex items-center gap-1"
              onClick={() => reqFileRef.current?.click()}
              disabled={analyzing}
            >
              {analyzing ? '分析中…' : '📷 上传图自动提炼卖点'}
            </button>
            <input
              ref={reqFileRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) handleAnalyzeReq(f)
                e.target.value = ''
              }}
            />
          </div>
        </div>
        <div className="text-xs text-slate-400 mb-3">
          上传一张产品图，AI 自动提炼卖点/特点并填入下方；你可随手修改。保存后重新生成，整页调性由「风格锁定 + 风格参考图」保持一致。
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">核心卖点</label>
            <textarea
              className="textarea h-20"
              value={req.selling}
              onChange={(e) => setReq((p) => ({ ...p, selling: e.target.value }))}
              placeholder="AI 提炼或手动填写：集吸尘/拖地/自清洁一体；高转速滚刷"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">产品描述</label>
            <textarea
              className="textarea h-20"
              value={req.desc}
              onChange={(e) => setReq((p) => ({ ...p, desc: e.target.value }))}
              placeholder="AI 提炼或手动填写产品描述"
            />
          </div>
        </div>
        <div className="mt-3">
          <label className="block text-xs text-slate-500 mb-1">其他要求 / 拍摄重点</label>
          <textarea
            className="textarea h-16"
            value={req.extra}
            onChange={(e) => setReq((p) => ({ ...p, extra: e.target.value }))}
            placeholder="如：现代简洁风格；颜色偏好；差异化表达"
          />
        </div>
        <div className="flex gap-2 mt-3">
          <button
            className="btn-primary"
            disabled={reqBusy}
            onClick={() => saveRequirements(false)}
          >
            {reqBusy ? '保存中…' : '💾 保存修改'}
          </button>
          <button
            className="btn-secondary"
            disabled={reqBusy || reqBusy}
            onClick={() => saveRequirements(true)}
          >
            保存并重新生成
          </button>
        </div>
      </section>

      {/* 模块工作台 */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <div className="text-sm font-medium text-slate-700">详情页模块</div>
          <div className="text-xs text-slate-400">
            {finalAssets.length} 张已生成 / {tasks.length} 个任务
          </div>
        </div>

        <div className="space-y-3">
          {project.module_plan.map((m, idx) => {
            const imgs = moduleGroups[m.key] || []
            const moduleTasks = tasks.filter((t) => t.module_key === m.key).slice(0, 3)
            return (
              <ModuleRow
                key={m.key}
                index={idx + 1}
                name={m.name_zh}
                moduleKey={m.key}
                expectedQty={m.quantity || 1}
                images={imgs}
                tasks={moduleTasks}
                onGenerate={() => handleGenerate([m.key])}
                onRetry={handleRetry}
                onPreview={setPreviewAsset}
                onDelete={handleDeleteAsset}
              />
            )
          })}
        </div>
      </section>

      {previewAsset && (
        <ImagePreviewModal asset={previewAsset} onClose={() => setPreviewAsset(null)} />
      )}

      {showCombined && (
        <CombinedPreviewModal
          url={combinedPreviewUrl}
          projectName={project.name}
          onClose={() => setShowCombined(false)}
        />
      )}
    </div>
  )
}

function ModuleRow({
  index,
  name,
  moduleKey,
  expectedQty,
  images,
  tasks,
  onGenerate,
  onRetry,
  onPreview,
  onDelete,
}: {
  index: number
  name: string
  moduleKey: string
  expectedQty: number
  images: Asset[]
  tasks: GenerationTask[]
  onGenerate: () => void
  onRetry: (id: number) => void
  onPreview: (a: Asset) => void
  onDelete: (a: Asset) => void
}) {
  const latest = tasks[0]
  const isRunning = tasks.some((t) => t.status === 'running' || t.status === 'pending')
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="font-medium text-slate-800">
            {String(index).padStart(2, '0')}. {name}
          </div>
          <div className="text-xs text-slate-400 mt-0.5">
            {images.length}/{expectedQty} 张 ·
            {latest ? ` 最新任务 #${latest.id} · ${taskLabel(latest.status)}` : ' 尚未生成'}
          </div>
        </div>
        <div className="flex gap-2 items-center">
          {isRunning && (
            <span className="text-xs text-brand-600 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse"></span>
              生成中
            </span>
          )}
          <button
            className="btn-secondary text-xs"
            onClick={onGenerate}
            disabled={isRunning}
          >
            {images.length > 0 ? '重新生成' : '生成'}
          </button>
        </div>
      </div>

      {/* 进度条 */}
      {isRunning && latest && (
        <div className="mb-3">
          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-500 transition-all"
              style={{ width: `${latest.progress || 0}%` }}
            />
          </div>
          {latest.message && <div className="text-xs text-slate-500 mt-1">{latest.message}</div>}
        </div>
      )}

      {latest && latest.status === 'failed' && (
        <div className="mb-3 p-2 bg-rose-50 text-rose-600 text-xs rounded flex items-center justify-between">
          <span>生成失败：{latest.message}</span>
          <button className="text-brand-600 hover:underline" onClick={() => onRetry(latest.id)}>
            重试
          </button>
        </div>
      )}

      {/* 图片网格 */}
      {images.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {images.map((img) => (
            <div
              key={img.id}
              className="group relative aspect-[3/4] rounded-md overflow-hidden border border-slate-200 bg-slate-50 cursor-zoom-in"
              onClick={() => onPreview(img)}
            >
              <img src={img.url} className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition flex items-end opacity-0 group-hover:opacity-100">
                <div className="p-2 w-full flex justify-between">
                  <span className="text-[10px] text-white truncate flex-1">{img.model || 'mock'}</span>
                  <button
                    className="text-[10px] text-white hover:text-rose-300"
                    onClick={(e) => {
                      e.stopPropagation()
                      onDelete(img)
                    }}
                  >
                    删除
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="aspect-[3/4] max-w-xs rounded-md border-2 border-dashed border-slate-200 grid place-items-center text-slate-400 text-sm">
          暂无图片
        </div>
      )}
    </div>
  )
}

function ImagePreviewModal({ asset, onClose }: { asset: Asset; onClose: () => void }) {
  const [dlFormat, setDlFormat] = useState<'png' | 'jpeg'>('png')

  const downloadUrl = api.fileUrl(asset.file_path, dlFormat)
  const downloadExt = dlFormat === 'jpeg' ? 'jpg' : 'png'

  return (
    <div
      className="fixed inset-0 z-50 bg-black/70 grid place-items-center p-8"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="font-medium">图片预览</div>
          <button className="btn-ghost" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <img src={asset.url} className="w-full rounded-md" />
          </div>
          <div className="space-y-3 text-sm">
            <div>
              <div className="text-slate-400 text-xs">尺寸</div>
              <div>{asset.width} × {asset.height}</div>
            </div>
            <div>
              <div className="text-slate-400 text-xs">模型</div>
              <div>{asset.model || '—'}</div>
            </div>
            <div>
              <div className="text-slate-400 text-xs">分辨率</div>
              <div>{asset.resolution}</div>
            </div>
            <div>
              <div className="text-slate-400 text-xs">Prompt</div>
              <div className="text-xs text-slate-700 bg-slate-50 p-2 rounded max-h-48 overflow-auto whitespace-pre-wrap">
                {asset.prompt || '—'}
              </div>
            </div>
            <div>
              <div className="text-slate-400 text-xs mb-1.5">下载格式</div>
              <div className="flex gap-2">
                <select
                  className="select flex-1"
                  value={dlFormat}
                  onChange={(e) => setDlFormat(e.target.value as 'png' | 'jpeg')}
                >
                  <option value="png">PNG（无损透明）</option>
                  <option value="jpeg">JPG（体积更小）</option>
                </select>
                <a
                  className="btn-primary whitespace-nowrap"
                  href={downloadUrl}
                  download={`${asset.module_key}_${asset.seq}.${downloadExt}`}
                >
                  ⬇ 下载
                </a>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                PNG 保留透明通道；JPG 体积更小、背景填充白色。
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function preferComposed(assets: Asset[]): Asset[] {
  const map: Record<string, Asset> = {}
  for (const a of assets) {
    const key = `${a.module_key}_${a.seq}`
    // 同一模块同序号优先保留成品图（composed），否则保留生成图
    if (a.asset_type === 'composed' || !map[key]) {
      map[key] = a
    }
  }
  return Object.values(map).sort((a, b) => a.id - b.id)
}

function groupByModule(assets: Asset[], plan: { key: string; name_zh: string; quantity?: number }[]) {
  const order = plan.map((m) => m.key)
  const map: Record<string, Asset[]> = {}
  for (const a of assets) {
    (map[a.module_key] = map[a.module_key] || []).push(a)
  }
  // 按 plan 顺序输出
  const sorted: Record<string, Asset[]> = {}
  for (const k of order) {
    if (map[k]) sorted[k] = map[k]
  }
  // 兜底
  for (const k of Object.keys(map)) {
    if (!sorted[k]) sorted[k] = map[k]
  }
  return sorted
}

function taskLabel(s: string) {
  return { pending: '等待中', running: '生成中', success: '已完成', failed: '失败' }[s] || s
}

function CombinedPreviewModal({
  url,
  projectName,
  onClose,
}: {
  url: string
  projectName: string
  onClose: () => void
}) {
  const [dlFormat, setDlFormat] = useState<'png' | 'jpeg'>('jpeg')
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(false)

  // 展示用 JPEG（秒级），下载按用户选择格式
  const downloadUrl = `${url}?format=${dlFormat}`
  const downloadExt = dlFormat === 'jpeg' ? 'jpg' : 'png'

  return (
    <div
      className="fixed inset-0 z-50 bg-black/80 grid place-items-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl w-full max-w-3xl max-h-[92vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 border-b border-slate-100 flex items-center justify-between flex-shrink-0">
          <div>
            <div className="font-medium text-slate-800">组合预览 — {projectName}</div>
            <div className="text-xs text-slate-400 mt-0.5">所有已生成模块图片垂直拼合</div>
          </div>
          <button className="btn-ghost" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-auto bg-slate-50 p-4">
          {!loaded && !error && (
            <div className="text-center py-20 text-slate-400 text-sm">
              <div className="inline-block w-8 h-8 border-2 border-slate-300 border-t-brand-500 rounded-full animate-spin mb-3"></div>
              <div>拼合中…</div>
            </div>
          )}
          {error && (
            <div className="text-center py-20 text-rose-500 text-sm">
              拼合失败，请确保至少有一张已生成的图片。
            </div>
          )}
          {url && !error && (
            <img
              src={url}
              className="w-full rounded-md shadow-sm"
              style={{ display: loaded ? 'block' : 'none' }}
              onLoad={() => setLoaded(true)}
              onError={() => setError(true)}
            />
          )}
        </div>

        <div className="p-4 border-t border-slate-100 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">下载格式：</span>
            <select
              className="select w-40"
              value={dlFormat}
              onChange={(e) => setDlFormat(e.target.value as 'png' | 'jpeg')}
            >
              <option value="jpeg">JPG（更小更快）</option>
              <option value="png">PNG（无损）</option>
            </select>
          </div>
          <a className="btn-primary" href={downloadUrl} download={`${projectName}-preview.${downloadExt}`}>
            ⬇ 下载组合图
          </a>
        </div>
      </div>
    </div>
  )
}
