import { useEffect, useState } from 'react'

interface SelectProps<T> {
  value: T | ''
  options: { key: string; name_zh: string; flag?: string; icon?: string }[]
  onChange: (v: string) => void
  columns?: number
  renderOption?: (opt: any) => React.ReactNode
}

export function SelectGrid<T extends string>({ value, options, onChange, columns = 4, renderOption }: SelectProps<T>) {
  return (
    <div
      className="grid gap-2"
      style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
    >
      {options.map((opt) => {
        const selected = value === opt.key
        return (
          <button
            key={opt.key}
            type="button"
            onClick={() => onChange(opt.key)}
            className={`relative px-3 py-2.5 rounded-md border text-sm text-left transition ${
              selected
                ? 'border-brand-500 bg-brand-50/60 text-brand-700 font-medium'
                : 'border-slate-200 hover:border-slate-300 bg-white'
            }`}
          >
            <div className="flex items-center gap-2">
              {renderOption ? renderOption(opt) : <DefaultOption opt={opt} />}
            </div>
            {selected && (
              <span className="absolute top-1.5 right-1.5 w-4 h-4 rounded-full bg-brand-500 text-white text-[10px] grid place-items-center">
                ✓
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}

function DefaultOption({ opt }: { opt: { name_zh: string; flag?: string; icon?: string } }) {
  return (
    <>
      {opt.flag && <span className="text-base">{opt.flag}</span>}
      {opt.icon && (
        <span className="w-5 h-5 rounded text-[10px] grid place-items-center bg-slate-100 text-slate-600 font-bold">
          {opt.icon.slice(0, 2)}
        </span>
      )}
      <span className="truncate">{opt.name_zh}</span>
    </>
  )
}

interface MetaSelectProps {
  meta: keyof MetaMap
  value: string
  onChange: (v: string) => void
  columns?: number
  flag?: boolean
}

type MetaMap = {
  industries: { key: string; name_zh: string }[]
  platforms: { key: string; name_zh: string; icon: string }[]
  languages: { key: string; name_zh: string; flag: string }[]
  aspectRatios: { key: string; name_zh: string }[]
  visualStyles: { key: string; name_zh: string }[]
  modules: { key: string; name_zh: string; desc_zh: string }[]
}

import { api } from '../lib/api'

export function MetaSelect({ meta, value, onChange, columns = 4, flag = true }: MetaSelectProps) {
  const [opts, setOpts] = useState<any[]>([])
  useEffect(() => {
    const fn = {
      industries: api.industries,
      platforms: api.platforms,
      languages: api.languages,
      aspectRatios: api.aspectRatios,
      visualStyles: api.visualStyles,
      modules: api.modules,
    }[meta]
    fn().then(setOpts)
  }, [meta])

  return (
    <SelectGrid
      value={value}
      options={opts}
      onChange={onChange}
      columns={columns}
      renderOption={(opt) => (
        <>
          {opt.flag && flag && <span className="text-base">{opt.flag}</span>}
          {opt.icon && (
            <span className="w-5 h-5 rounded text-[10px] grid place-items-center bg-slate-100 text-slate-600 font-bold">
              {opt.icon.slice(0, 2)}
            </span>
          )}
          <span className="truncate">{opt.name_zh}</span>
        </>
      )}
    />
  )
}
