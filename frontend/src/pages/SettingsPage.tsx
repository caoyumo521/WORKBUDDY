import { useEffect, useState } from 'react'
import { api } from '../lib/api'

interface ImageCfg {
  provider: string
  base_url: string
  model: string
  api_key: string // 用户输入的（不会回显，只显示 mask）
  api_key_masked: string
  has_api_key: boolean
  quality: string
  output_format: string
  background: string
  providers: string[]
  output_formats: string[]
  qualities: string[]
  backgrounds: string[]
}

interface TextCfg {
  provider: string
  base_url: string
  model: string
  api_key: string
  api_key_masked: string
  has_api_key: boolean
  providers: string[]
}

interface Settings {
  image: ImageCfg
  text: TextCfg
}

const KEEP = '__KEEP__'
const CLEAR = '__CLEAR__'

export default function SettingsPage() {
  const [data, setData] = useState<Settings | null>(null)
  const [saving, setSaving] = useState(false)
  const [testingImg, setTestingImg] = useState(false)
  const [testingTxt, setTestingTxt] = useState(false)
  const [deepTesting, setDeepTesting] = useState(false)
  const [imgResult, setImgResult] = useState<{ ok: boolean; message: string } | null>(null)
  const [txtResult, setTxtResult] = useState<{ ok: boolean; message: string } | null>(null)
  const [deepResult, setDeepResult] = useState<{ ok: boolean; message: string } | null>(null)
  const [saved, setSaved] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => {
    api.getSettings().then((d) => {
      // 初始化用户输入的 api_key 为 KEEP（保留原值）
      setData({
        image: { ...d.image, api_key: KEEP },
        text: { ...d.text, api_key: KEEP },
      })
    }).catch((e) => {
      setLoadError('加载配置失败：' + (e.message || e))
    })
  }, [])

  async function save() {
    if (!data) return
    setSaving(true)
    setSaved(false)
    setSaveError(null)
    try {
      const payload = {
        image: {
          provider: data.image.provider,
          base_url: data.image.base_url,
          model: data.image.model,
          api_key: data.image.api_key, // 可能为 KEEP / CLEAR / 新值
          quality: data.image.quality,
          output_format: data.image.output_format,
          background: data.image.background,
        },
        text: {
          provider: data.text.provider,
          base_url: data.text.base_url,
          model: data.text.model,
          api_key: data.text.api_key,
        },
      }
      const updated = await api.updateSettings(payload)
      setData({
        image: { ...updated.image, api_key: KEEP },
        text: { ...updated.text, api_key: KEEP },
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (e: any) {
      const msg = e.message || String(e)
      setSaveError(msg)
    } finally {
      setSaving(false)
    }
  }

  async function test(section: 'image' | 'text') {
    if (section === 'image') {
      setTestingImg(true)
      setImgResult(null)
      try {
        const r = await api.testConnection('image')
        setImgResult({ ok: r.ok, message: r.message + (r.latency_ms ? ` (${r.latency_ms}ms)` : '') })
      } catch (e: any) {
        setImgResult({ ok: false, message: e.message })
      } finally {
        setTestingImg(false)
      }
    } else {
      setTestingTxt(true)
      setTxtResult(null)
      try {
        const r = await api.testConnection('text')
        setTxtResult({ ok: r.ok, message: r.message + (r.latency_ms ? ` (${r.latency_ms}ms)` : '') })
      } catch (e: any) {
        setTxtResult({ ok: false, message: e.message })
      } finally {
        setTestingTxt(false)
      }
    }
  }

  async function deepTest() {
    setDeepTesting(true)
    setDeepResult(null)
    try {
      const r = await api.testGeneration()
      setDeepResult({ ok: r.ok, message: r.message + (r.latency_ms ? ` (${r.latency_ms}ms)` : '') })
    } catch (e: any) {
      setDeepResult({ ok: false, message: e.message })
    } finally {
      setDeepTesting(false)
    }
  }

  if (!data) return (
    <div className="p-8">
      {loadError ? (
        <div className="max-w-md mx-auto mt-20">
          <div className="card p-6 text-center">
            <div className="text-rose-600 text-sm mb-4">{loadError}</div>
            <button className="btn-primary" onClick={() => window.location.reload()}>
              重新加载
            </button>
          </div>
        </div>
      ) : (
        <div className="text-slate-400">加载中…</div>
      )}
    </div>
  )

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-slate-800">系统设置</h1>
        <p className="text-sm text-slate-500 mt-1">
          配置生图 API 和文案 / 思考 API。所有配置写入 <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs">backend/.env</code>，无需重启即可生效。
        </p>
      </div>

      {/* ===== 生图 API ===== */}
      <section className="card p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-medium text-slate-800">生图 API</h2>
            <p className="text-xs text-slate-500 mt-1">
              用于按模块生成详情页图片。建议使用 <strong>GPT Image API (gpt-image-2)</strong>，原生支持参考图编辑。
            </p>
          </div>
          <div className="flex gap-2">
            <button
              className="btn-secondary text-xs"
              disabled={testingImg}
              onClick={() => test('image')}
            >
              {testingImg ? '测试中…' : '🔌 测试连通'}
            </button>
            <button
              className="btn-secondary text-xs"
              disabled={deepTesting}
              onClick={deepTest}
              title="实际生成一张小图，验证完整生图链路（消耗少量 credits）"
            >
              {deepTesting ? '深度测试中…' : '🎯 深度测试'}
            </button>
          </div>
        </div>
        {imgResult && (
          <div
            className={`mb-2 p-3 rounded text-xs ${imgResult.ok ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}
          >
            {imgResult.ok ? '✓ ' : '✗ '}{imgResult.message}
          </div>
        )}
        {deepResult && (
          <div
            className={`mb-4 p-3 rounded text-xs ${deepResult.ok ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700 border border-amber-200'}`}
          >
            {deepResult.ok ? '✓ ' : '⚠ '}{deepResult.message}
            {!deepResult.ok && (
              <span className="block mt-1 text-amber-500">
                连通性测试通过但实际生图失败，通常是 API 分销商渠道暂时不可用。请稍后重试或联系分销商。
              </span>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Field label="Provider">
            <select
              className="select"
              value={data.image.provider}
              onChange={(e) => setData({ ...data, image: { ...data.image, provider: e.target.value } })}
            >
              {data.image.providers.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Model">
            <input
              className="input"
              value={data.image.model}
              onChange={(e) => setData({ ...data, image: { ...data.image, model: e.target.value } })}
              placeholder="gpt-image-2 / gpt-image-1 / dall-e-3 / flux-pro"
            />
          </Field>
          <Field label="Base URL" full>
            <input
              className="input"
              value={data.image.base_url}
              onChange={(e) => setData({ ...data, image: { ...data.image, base_url: e.target.value } })}
              placeholder="https://api.openai.com/v1"
            />
          </Field>
          <Field
            label={
              <span>
                API Key{' '}
                {data.image.has_api_key && (
                  <span className="text-slate-400 text-xs ml-1">当前：{data.image.api_key_masked}</span>
                )}
              </span>
            }
            full
          >
            <div className="flex gap-2">
              <input
                className="input flex-1"
                type="password"
                value={data.image.api_key === KEEP ? '' : data.image.api_key}
                placeholder={data.image.has_api_key ? '留空保持原值，或输入新值' : 'sk-...'}
                onChange={(e) =>
                  setData({
                    ...data,
                    image: { ...data.image, api_key: e.target.value || KEEP },
                  })
                }
              />
              {data.image.has_api_key && (
                <button
                  className="btn-ghost text-xs whitespace-nowrap"
                  onClick={() => setData({ ...data, image: { ...data.image, api_key: CLEAR } })}
                  type="button"
                >
                  清除
                </button>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1">留空表示保留当前 Key；点「清除」清空。</p>
          </Field>
          {data.image.provider === 'openai' && (
            <>
              <Field label="输出格式">
                <select
                  className="select"
                  value={data.image.output_format}
                  onChange={(e) =>
                    setData({ ...data, image: { ...data.image, output_format: e.target.value } })
                  }
                >
                  {data.image.output_formats.map((f) => (
                    <option key={f} value={f}>
                      {f}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="质量">
                <select
                  className="select"
                  value={data.image.quality}
                  onChange={(e) =>
                    setData({ ...data, image: { ...data.image, quality: e.target.value } })
                  }
                >
                  {data.image.qualities.map((q) => (
                    <option key={q} value={q}>
                      {q}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="背景">
                <select
                  className="select"
                  value={data.image.background}
                  onChange={(e) =>
                    setData({ ...data, image: { ...data.image, background: e.target.value } })
                  }
                >
                  {data.image.backgrounds.map((b) => (
                    <option key={b} value={b}>
                      {b}
                    </option>
                  ))}
                </select>
              </Field>
            </>
          )}
        </div>
      </section>

      {/* ===== 文案 / 思考 API ===== */}
      <section className="card p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-medium text-slate-800">文案 / 思考 API</h2>
            <p className="text-xs text-slate-500 mt-1">
              用于详情页结构规划、文案生成、Prompt 优化。三种模式：
              <br />
              • <strong>openai</strong>：调用 GPT/Claude/Gemini 等 OpenAI 兼容 API
              <br />
              • <strong>workbuddy</strong>：使用 <code>knowledge/</code> 中预生成的策略文件，无需 API Key
              <br />
              • <strong>none</strong>：纯模板模式（适合开发测试）
            </p>
          </div>
          <button
            className="btn-secondary text-xs"
            disabled={testingTxt || data.text.provider === 'none' || data.text.provider === 'workbuddy'}
            onClick={() => test('text')}
          >
            {testingTxt ? '测试中…' : '🔌 测试连通'}
          </button>
        </div>
        {txtResult && (
          <div
            className={`mb-4 p-3 rounded text-xs ${txtResult.ok ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}
          >
            {txtResult.ok ? '✓ ' : '✗ '}{txtResult.message}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Field label="Provider">
            <select
              className="select"
              value={data.text.provider}
              onChange={(e) => setData({ ...data, text: { ...data.text, provider: e.target.value } })}
            >
              {data.text.providers.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Model">
            <input
              className="input"
              value={data.text.model}
              disabled={data.text.provider !== 'openai'}
              onChange={(e) => setData({ ...data, text: { ...data.text, model: e.target.value } })}
              placeholder={data.text.provider === 'openai' ? 'gpt-4o-mini / gpt-4o / claude-3.5-sonnet' : '无需 Model'}
            />
          </Field>
          <Field label="Base URL" full>
            <input
              className="input"
              value={data.text.base_url}
              disabled={data.text.provider !== 'openai'}
              onChange={(e) => setData({ ...data, text: { ...data.text, base_url: e.target.value } })}
              placeholder="https://api.openai.com/v1"
            />
          </Field>
          <Field
            label={
              <span>
                API Key{' '}
                {data.text.has_api_key && (
                  <span className="text-slate-400 text-xs ml-1">当前：{data.text.api_key_masked}</span>
                )}
              </span>
            }
            full
          >
            <div className="flex gap-2">
              <input
                className="input flex-1"
                type="password"
                disabled={data.text.provider !== 'openai'}
                value={data.text.api_key === KEEP ? '' : data.text.api_key}
                placeholder={data.text.has_api_key ? '留空保持原值，或输入新值' : 'sk-...'}
                onChange={(e) =>
                  setData({
                    ...data,
                    text: { ...data.text, api_key: e.target.value || KEEP },
                  })
                }
              />
              {data.text.has_api_key && data.text.provider === 'openai' && (
                <button
                  className="btn-ghost text-xs whitespace-nowrap"
                  onClick={() => setData({ ...data, text: { ...data.text, api_key: CLEAR } })}
                  type="button"
                >
                  清除
                </button>
              )}
            </div>
          </Field>
        </div>
      </section>

      {/* ===== 保存按钮 ===== */}
      <div className="flex items-center justify-between">
        <div className="text-xs">
          {saved && <span className="text-emerald-600">✓ 已保存并生效</span>}
          {saveError && <span className="text-rose-600">✗ 保存失败：{saveError}</span>}
        </div>
        <button className="btn-primary" onClick={save} disabled={saving}>
          {saving ? '保存中…' : '💾 保存全部设置'}
        </button>
      </div>
    </div>
  )
}

function Field({
  label,
  children,
  full,
}: {
  label: React.ReactNode
  children: React.ReactNode
  full?: boolean
}) {
  return (
    <div className={full ? 'lg:col-span-2' : ''}>
      <label className="block text-xs font-medium text-slate-600 mb-1.5">{label}</label>
      {children}
    </div>
  )
}