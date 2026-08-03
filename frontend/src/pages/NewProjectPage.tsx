import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../lib/api'
import { MetaSelect, SelectGrid } from '../components/SelectGrid'
import type { Project } from '../lib/api'

interface WizardState {
  // 基本
  name: string
  industry: string
  target_market: string
  target_platform: string
  language: string
  visual_style: string
  resolution: string
  aspect_ratio: string
  // 产品
  product_name: string
  product_selling_points: string
  product_target_audience: string
  product_description: string
  extra_requirements: string
  // 模块
  module_keys: string[]
  module_quantities: Record<string, number>
  module_mode: 'ai' | 'manual'
}

const STEPS = [
  { key: 'basic', title: '产品信息', desc: '项目名 + 产品图' },
  { key: 'market', title: '行业/平台', desc: '行业、目标平台' },
  { key: 'requirement', title: '详情图要求', desc: '卖点和目标用户（AI 帮写）' },
  { key: 'visual', title: '视觉/语言/尺寸', desc: '视觉风格、输出语言、尺寸比例、分辨率' },
  { key: 'modules', title: '详情图模块', desc: 'AI 规划或自选' },
  { key: 'confirm', title: '确认并创建', desc: '检查并创建' },
] as const

const RESOLUTIONS = [
  { key: '1K', name_zh: '1K · 1024px' },
  { key: '2K', name_zh: '2K · 2048px' },
  { key: '4K', name_zh: '4K · 4096px' },
]

export default function NewProjectPage() {
  const nav = useNavigate()
  const [params] = useSearchParams()
  const [step, setStep] = useState(Number(params.get('step') || 0))
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadPhase, setUploadPhase] = useState<'idle' | 'creating' | 'uploading' | 'analyzing'>('idle')
  const [productImages, setProductImages] = useState<{ name: string; size: number; url: string }[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [presetModules, setPresetModules] = useState<string[]>([])
  const [modules, setModules] = useState<{ key: string; name_zh: string; desc_zh: string }[]>([])

  const [s, setS] = useState<WizardState>({
    name: '',
    industry: '',
    target_market: '中国',
    target_platform: 'tmall',
    language: 'zh-CN',
    visual_style: 'minimal',
    resolution: '2K',
    aspect_ratio: '3:4',
    product_name: '',
    product_selling_points: '',
    product_target_audience: '',
    product_description: '',
    extra_requirements: '',
    module_keys: [],
    module_quantities: {},
    module_mode: 'ai',
  })

  useEffect(() => {
    api.modules().then(setModules)
  }, [])

  useEffect(() => {
    if (s.industry) {
      api.industryPreset(s.industry).then((r) => setPresetModules(r.modules || []))
    }
  }, [s.industry])

  function patch(p: Partial<WizardState>) {
    setS((prev) => ({ ...prev, ...p }))
  }

  async function handleUpload(files: FileList | null) {
    if (!files || !files.length) return
    setUploading(true)
    setUploadProgress(0)
    try {
      // 1) 快速创建/复用草稿项目（不做 AI 规划，避免上传前等待 LLM）
      let tempId = localStorage.getItem('wizard_temp_project')
      if (!tempId) {
        setUploadPhase('creating')
        const tempProject = await api.createDraft({
          name: s.name || '草稿-临时项目',
          industry: s.industry,
          target_market: s.target_market,
          target_platform: s.target_platform,
          language: s.language,
          visual_style: s.visual_style,
          resolution: s.resolution,
          aspect_ratio: s.aspect_ratio,
          product_name: s.product_name,
          product_selling_points: s.product_selling_points,
          product_target_audience: s.product_target_audience,
          product_description: s.product_description,
          extra_requirements: s.extra_requirements,
        })
        tempId = tempProject.id
        localStorage.setItem('wizard_temp_project', tempId)
      }

      // 2) 上传图片（带进度）
      setUploadPhase('uploading')
      setUploadProgress(0)
      const uploaded = await api.upload(tempId, Array.from(files), 'product_image', (pct) => {
        setUploadProgress(pct)
      })
      const enriched = uploaded.map((u: any) => ({
        name: u.file_path.split(/[\\/]/).pop(),
        size: u.file_size,
        url: u.url,
      }))
      setProductImages((prev) => [...prev, ...enriched])

      // 3) 用首张图自动提炼卖点/描述（可选，失败不阻塞）
      const firstFile = files[0]
      if (firstFile) {
        setUploadPhase('analyzing')
        try {
          const analyzed = await api.analyzeImage(
            {
              productName: s.product_name || s.name,
              industry: s.industry,
              language: s.language,
              visualStyle: s.visual_style,
            },
            firstFile,
          )
          patch({
            product_name: s.product_name || analyzed.description?.split('，')[0]?.slice(0, 20) || s.product_name,
            product_selling_points: s.product_selling_points || analyzed.selling_points || '',
            product_description: s.product_description || analyzed.description || '',
            extra_requirements:
              (s.extra_requirements ? s.extra_requirements + '\n' : '') +
              (analyzed.suggested_extra ? `[AI 建议] ${analyzed.suggested_extra}` : ''),
          })
        } catch (analyzeErr: any) {
          // 非致命：图片已保存，卖点可后续手动填写
          console.warn('AI 提炼卖点失败:', analyzeErr)
        }
      }
    } catch (e: any) {
      alert('上传失败：' + e.message)
    } finally {
      setUploading(false)
      setUploadPhase('idle')
      setUploadProgress(0)
    }
  }

  async function handleAIHelp() {
    if (!s.product_name && !s.product_selling_points) {
      alert('请至少填写产品名或卖点')
      return
    }
    try {
      const r = await api.aiHelp({
        product_name: s.product_name,
        product_selling_points: s.product_selling_points,
        product_target_audience: s.product_target_audience,
        product_description: s.product_description,
        industry: s.industry,
        target_market: s.target_market,
        target_platform: s.target_platform,
        visual_style: s.visual_style,
        language: s.language,
      })
      patch({
        product_selling_points: r.selling_points || s.product_selling_points,
        product_target_audience: r.target_audience || s.product_target_audience,
        extra_requirements:
          (s.extra_requirements ? s.extra_requirements + '\n' : '') + `[AI 视觉方向] ${r.visual_direction || ''}`,
        module_keys: r.suggested_modules || s.module_keys,
      })
    } catch (e: any) {
      alert('AI 帮写失败：' + e.message)
    }
  }

  function toggleModule(key: string) {
    const has = s.module_keys.includes(key)
    patch({
      module_keys: has ? s.module_keys.filter((k) => k !== key) : [...s.module_keys, key],
      module_quantities: has
        ? Object.fromEntries(Object.entries(s.module_quantities).filter(([k]) => k !== key))
        : { ...s.module_quantities, [key]: s.module_quantities[key] || 1 },
    })
  }

  function setQty(key: string, q: number) {
    patch({ module_quantities: { ...s.module_quantities, [key]: Math.max(1, q) } })
  }

  async function handleSubmit() {
    if (!s.name.trim()) {
      alert('请填写项目名')
      setStep(0)
      return
    }
    setSubmitting(true)
    try {
      // 找临时项目 id（在 step 0 上传过图的）
      const tempId = localStorage.getItem('wizard_temp_project')
      let project: Project
      if (tempId) {
        // 在已有草稿项目上 update module_keys 等
        project = await api.getProject(tempId)
        await api.updateProject(tempId, {
          name: s.name,
          industry: s.industry,
          target_market: s.target_market,
          target_platform: s.target_platform,
          language: s.language,
          visual_style: s.visual_style,
          resolution: s.resolution,
          aspect_ratio: s.aspect_ratio,
          product_name: s.product_name,
          product_selling_points: s.product_selling_points,
          product_target_audience: s.product_target_audience,
          product_description: s.product_description,
          extra_requirements: s.extra_requirements,
          module_plan: s.module_keys.map((k) => ({
            key: k,
            name_zh: modules.find((m) => m.key === k)?.name_zh || k,
            quantity: s.module_quantities[k] || 1,
          })),
        })
        project = await api.getProject(tempId)
        localStorage.removeItem('wizard_temp_project')
      } else {
        project = await api.createFromWizard({
          ...s,
          module_keys: s.module_keys,
          module_quantities: s.module_quantities,
        })
      }
      nav(`/projects/${project.id}`)
    } catch (e: any) {
      alert('创建失败：' + e.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex h-full">
      {/* 左侧步骤 */}
      <div className="w-56 border-r border-slate-100 bg-white p-4">
        <div className="text-xs text-slate-400 font-medium mb-2">创建项目</div>
        <ol className="space-y-1">
          {STEPS.map((st, i) => (
            <li key={st.key}>
              <button
                className={`w-full text-left px-3 py-2 rounded-md text-sm transition ${
                  i === step
                    ? 'bg-brand-50 text-brand-700 font-medium'
                    : i < step
                    ? 'text-slate-700 hover:bg-slate-50'
                    : 'text-slate-400'
                }`}
                onClick={() => setStep(i)}
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`w-5 h-5 rounded-full text-[10px] grid place-items-center ${
                      i < step
                        ? 'bg-brand-500 text-white'
                        : i === step
                        ? 'bg-brand-600 text-white'
                        : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {i < step ? '✓' : i + 1}
                  </span>
                  <span className="truncate">{st.title}</span>
                </div>
              </button>
            </li>
          ))}
        </ol>
      </div>

      {/* 主区 */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-8">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-slate-800">{STEPS[step].title}</h2>
            <p className="text-sm text-slate-500 mt-1">{STEPS[step].desc}</p>
          </div>

          {step === 0 && (
            <StepProduct
              state={s}
              patch={patch}
              productImages={productImages}
              onUpload={handleUpload}
              uploading={uploading}
              uploadPhase={uploadPhase}
              uploadProgress={uploadProgress}
            />
          )}
          {step === 1 && <StepMarket state={s} patch={patch} />}
          {step === 2 && <StepRequirement state={s} patch={patch} onAIHelp={handleAIHelp} />}
          {step === 3 && <StepVisual state={s} patch={patch} />}
          {step === 4 && (
            <StepModules
              state={s}
              modules={modules}
              presetKeys={presetModules}
              onToggle={toggleModule}
              onSetQty={setQty}
              patch={patch}
            />
          )}
          {step === 5 && <StepConfirm state={s} modules={modules} />}

          <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-100">
            <button
              className="btn-secondary"
              disabled={step === 0}
              onClick={() => setStep((x) => Math.max(0, x - 1))}
            >
              上一步
            </button>
            {step < STEPS.length - 1 ? (
              <button className="btn-primary" onClick={() => setStep((x) => x + 1)}>
                下一步
              </button>
            ) : (
              <button className="btn-primary" onClick={handleSubmit} disabled={submitting}>
                {submitting ? '创建中…' : '创建项目并开始'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ===== 各步骤组件 =====
function StepProduct({
  state,
  patch,
  productImages,
  onUpload,
  uploading,
  uploadPhase,
  uploadProgress,
}: {
  state: WizardState
  patch: (p: Partial<WizardState>) => void
  productImages: { name: string; size: number; url: string }[]
  onUpload: (files: FileList | null) => void
  uploading: boolean
  uploadPhase: 'idle' | 'creating' | 'uploading' | 'analyzing'
  uploadProgress: number
}) {
  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">项目名称</label>
        <input
          className="input"
          value={state.name}
          onChange={(e) => patch({ name: e.target.value })}
          placeholder="例如：无线智能洗地机 X1 详情页"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          产品图 <span className="text-slate-400 font-normal">（最多 6 张，可选）</span>
        </label>
        <div className="border-2 border-dashed border-slate-200 rounded-xl p-6 bg-white">
          <div className="text-center">
            <div className="text-3xl mb-2">☁️</div>
            <div className="text-sm text-slate-600 mb-1">上传同一款产品图片</div>
            <div className="text-xs text-slate-400 mb-3">支持 JPG / JPEG / PNG / WEBP（最大 10MB / 张）</div>
            {uploading ? (
              <div className="w-64">
                <div className="text-xs text-slate-500 mb-1">
                  {uploadPhase === 'creating' && '创建草稿项目…'}
                  {uploadPhase === 'uploading' && `上传中 ${uploadProgress}%…`}
                  {uploadPhase === 'analyzing' && 'AI 提炼卖点中…'}
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-brand-500 transition-all duration-200"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            ) : (
              <label className="btn-primary cursor-pointer inline-flex">
                + 本地上传
                <input
                  type="file"
                  multiple
                  accept=".jpg,.jpeg,.png,.webp"
                  className="hidden"
                  onChange={(e) => onUpload(e.target.files)}
                />
              </label>
            )}
          </div>
        </div>
        {productImages.length > 0 && (
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 mt-4">
            {productImages.map((img, i) => (
              <div key={i} className="aspect-square rounded-md overflow-hidden bg-slate-100 border border-slate-200">
                <img src={img.url} className="w-full h-full object-cover" />
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">产品名称（可选）</label>
        <input
          className="input"
          value={state.product_name}
          onChange={(e) => patch({ product_name: e.target.value })}
          placeholder="例如：无线智能洗地机 X1"
        />
      </div>
    </div>
  )
}

function StepMarket({ state, patch }: { state: WizardState; patch: (p: Partial<WizardState>) => void }) {
  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">行业 / 品类</label>
        <MetaSelect meta="industries" value={state.industry} onChange={(v) => patch({ industry: v })} columns={5} />
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">目标市场</label>
        <div className="flex flex-wrap gap-2">
          {['中国', '美国', '英国', '欧洲', '日本', '韩国', '东南亚'].map((m) => (
            <button
              key={m}
              onClick={() => patch({ target_market: m })}
              className={`px-4 h-9 rounded-md text-sm ${
                state.target_market === m
                  ? 'bg-brand-50 text-brand-700 border border-brand-500 font-medium'
                  : 'bg-white border border-slate-200 text-slate-700 hover:border-slate-300'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">目标平台</label>
        <MetaSelect meta="platforms" value={state.target_platform} onChange={(v) => patch({ target_platform: v })} columns={6} flag={false} />
      </div>
    </div>
  )
}

function StepRequirement({
  state,
  patch,
  onAIHelp,
}: {
  state: WizardState
  patch: (p: Partial<WizardState>) => void
  onAIHelp: () => void
}) {
  const [busy, setBusy] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  async function handleAnalyze(file: File) {
    setBusy(true)
    try {
      const r: any = await api.analyzeImage(
        {
          productName: state.product_name,
          industry: state.industry,
          language: state.language,
          visualStyle: state.visual_style,
        },
        file,
      )
      if (r._error) {
        alert('视觉分析暂不可用：' + r._error + '\n你可以手动填写卖点。')
        return
      }
      patch({
        product_selling_points: r.selling_points || state.product_selling_points,
        product_description: r.description || state.product_description,
        extra_requirements:
          (state.extra_requirements ? state.extra_requirements + '\n' : '') +
          (r.suggested_extra ? `[AI 图析] ${r.suggested_extra}` : ''),
      })
    } catch (e: any) {
      alert('图片分析失败：' + e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-slate-700">详情图要求</label>
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="text-sm text-brand-600 hover:underline flex items-center gap-1"
            onClick={() => fileRef.current?.click()}
            disabled={busy}
          >
            {busy ? '分析中…' : '📷 上传图自动提炼'}
          </button>
          <button
            type="button"
            className="text-sm text-brand-600 hover:underline flex items-center gap-1"
            onClick={onAIHelp}
          >
            ✨ AI 帮写
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) handleAnalyze(f)
              e.target.value = ''
            }}
          />
        </div>
      </div>
      <div>
        <label className="block text-xs text-slate-500 mb-1">核心卖点</label>
        <textarea
          className="textarea h-20"
          value={state.product_selling_points}
          onChange={(e) => patch({ product_selling_points: e.target.value })}
          placeholder="例如：集吸尘/拖地/自清洁一体；高转速滚刷；大吸力电机"
        />
      </div>
      <div>
        <label className="block text-xs text-slate-500 mb-1">目标用户</label>
        <input
          className="input"
          value={state.product_target_audience}
          onChange={(e) => patch({ product_target_audience: e.target.value })}
          placeholder="例如：都市白领、有娃/有宠物的家庭"
        />
      </div>
      <div>
        <label className="block text-xs text-slate-500 mb-1">产品描述（可选）</label>
        <textarea
          className="textarea h-16"
          value={state.product_description}
          onChange={(e) => patch({ product_description: e.target.value })}
          placeholder="例如：高转速滚刷 + 大吸力电机；智能感应脏污；一次加水清洁全屋"
        />
      </div>
      <div>
        <label className="block text-xs text-slate-500 mb-1">其他要求（可选）</label>
        <textarea
          className="textarea h-16"
          value={state.extra_requirements}
          onChange={(e) => patch({ extra_requirements: e.target.value })}
          placeholder="例如：现代简洁风格；颜色偏好；拍摄场景"
        />
      </div>
    </div>
  )
}

function StepVisual({ state, patch }: { state: WizardState; patch: (p: Partial<WizardState>) => void }) {
  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">视觉风格</label>
        <MetaSelect meta="visualStyles" value={state.visual_style} onChange={(v) => patch({ visual_style: v })} columns={5} flag={false} />
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">输出语言</label>
        <MetaSelect meta="languages" value={state.language} onChange={(v) => patch({ language: v })} columns={5} />
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">尺寸比例</label>
        <MetaSelect meta="aspectRatios" value={state.aspect_ratio} onChange={(v) => patch({ aspect_ratio: v })} columns={5} flag={false} />
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">图片分辨率</label>
        <SelectGrid
          value={state.resolution}
          options={RESOLUTIONS}
          onChange={(v) => patch({ resolution: v })}
          columns={3}
        />
      </div>
    </div>
  )
}

function StepModules({
  state,
  modules,
  presetKeys,
  onToggle,
  onSetQty,
  patch,
}: {
  state: WizardState
  modules: { key: string; name_zh: string; desc_zh: string }[]
  presetKeys: string[]
  onToggle: (k: string) => void
  onSetQty: (k: string, q: number) => void
  patch: (p: Partial<WizardState>) => void
}) {
  function applyPreset() {
    patch({ module_keys: [...presetKeys] })
  }
  return (
    <div className="space-y-4">
      <div className="flex bg-slate-100 rounded-md p-1 w-fit">
        <button
          className={`px-4 h-8 rounded text-sm ${state.module_mode === 'ai' ? 'bg-white shadow-sm font-medium' : 'text-slate-500'}`}
          onClick={() => {
            patch({ module_mode: 'ai' })
            if (presetKeys.length) applyPreset()
          }}
        >
          AI 规划
        </button>
        <button
          className={`px-4 h-8 rounded text-sm ${state.module_mode === 'manual' ? 'bg-white shadow-sm font-medium' : 'text-slate-500'}`}
          onClick={() => patch({ module_mode: 'manual' })}
        >
          自选组合
        </button>
      </div>

      <div className="text-xs text-slate-500">
        选择详情图包含的模块 <span className="text-slate-400">（可多选，每个模块可设置数量）</span>
        {presetKeys.length > 0 && state.module_mode === 'manual' && (
          <button className="ml-3 text-brand-600 hover:underline" onClick={applyPreset}>
            一键应用行业推荐
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {modules.map((m) => {
          const checked = state.module_keys.includes(m.key)
          return (
            <div
              key={m.key}
              onClick={() => onToggle(m.key)}
              className={`relative p-4 rounded-lg border-2 cursor-pointer transition ${
                checked ? 'border-brand-500 bg-brand-50/30' : 'border-slate-200 hover:border-slate-300 bg-white'
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-medium text-slate-800 text-sm">{m.name_zh}</div>
                  <div className="text-xs text-slate-500 mt-1 leading-relaxed">{m.desc_zh}</div>
                </div>
                <span
                  className={`w-5 h-5 rounded-full border-2 grid place-items-center ${
                    checked ? 'bg-brand-500 border-brand-500 text-white' : 'border-slate-300'
                  }`}
                >
                  {checked && <span className="text-[10px]">✓</span>}
                </span>
              </div>
              {checked && (
                <div
                  className="mt-3 flex items-center gap-2"
                  onClick={(e) => e.stopPropagation()}
                >
                  <span className="text-xs text-slate-500">数量</span>
                  <button
                    className="w-7 h-7 rounded border border-slate-200 hover:bg-slate-50"
                    onClick={() => onSetQty(m.key, (state.module_quantities[m.key] || 1) - 1)}
                  >
                    −
                  </button>
                  <span className="w-8 text-center text-sm font-medium">
                    {state.module_quantities[m.key] || 1}
                  </span>
                  <button
                    className="w-7 h-7 rounded border border-slate-200 hover:bg-slate-50"
                    onClick={() => onSetQty(m.key, (state.module_quantities[m.key] || 1) + 1)}
                  >
                    +
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="text-xs text-slate-400">
        已选 {state.module_keys.length} 个模块 ·
        共 {Object.values(state.module_quantities).reduce((a, b) => a + (b || 1), 0) || state.module_keys.length} 张图
      </div>
    </div>
  )
}

function StepConfirm({
  state,
  modules,
}: {
  state: WizardState
  modules: { key: string; name_zh: string }[]
}) {
  const moduleMap = Object.fromEntries(modules.map((m) => [m.key, m.name_zh]))
  return (
    <div className="space-y-4 text-sm">
      <SummaryRow label="项目名称" value={state.name || '—'} />
      <SummaryRow label="行业" value={state.industry || '—'} />
      <SummaryRow label="目标市场 / 平台" value={`${state.target_market} / ${state.target_platform}`} />
      <SummaryRow label="语言" value={state.language} />
      <SummaryRow label="视觉风格" value={state.visual_style} />
      <SummaryRow label="分辨率 / 比例" value={`${state.resolution} / ${state.aspect_ratio}`} />
      <SummaryRow label="产品" value={state.product_name || '—'} />
      <SummaryRow label="核心卖点" value={state.product_selling_points || '—'} />
      <div className="pt-4 border-t border-slate-100">
        <div className="text-slate-500 mb-2">详情页模块：</div>
        <div className="flex flex-wrap gap-2">
          {state.module_keys.length === 0 && <span className="text-slate-400">（未选模块）</span>}
          {state.module_keys.map((k) => (
            <span
              key={k}
              className="badge bg-brand-50 text-brand-700 border border-brand-200 px-2.5"
            >
              {moduleMap[k] || k} ×{state.module_quantities[k] || 1}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex">
      <div className="w-32 text-slate-500">{label}</div>
      <div className="flex-1 text-slate-800">{value}</div>
    </div>
  )
}
