'use client'

import { ReactNode } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  RadialBarChart, RadialBar, PolarAngleAxis as RadialAngleAxis,
} from 'recharts'
import { CATEGORICAL, STATUS } from '@/src/lib/chartColors'

/** Variante clara de Primitives.tsx — exclusiva para dashboards CLIENTE_*
 * (RURAL, CONDUCTOR, DISTRITO). "Tema claro ya decidido — NO oscurecer"
 * (sesión dashboards): las tarjetas de estos roles usan bg-white igual que
 * RepuestoCard, no el par bg-slate-800/data-theme-override de los roles
 * internos, porque recharts pinta SVG con props inline — el CSS de
 * globals.css que invierte clases Tailwind no le llega. */

const TOOLTIP_STYLE = {
  background: '#FFFFFF',
  border: '1px solid #E2E8F0',
  borderRadius: 8,
  fontSize: 12,
  color: '#1E293B',
}
const GRID_STROKE = '#E2E8F0'
const AXIS_TICK = { fontSize: 10, fill: '#64748B' }

function SinDatosLight({ height = 208 }: { height?: number }) {
  return (
    <div style={{ height }} className="flex items-center justify-center text-xs text-slate-400 font-body text-center px-4">
      Sin datos en este período todavía.
    </div>
  )
}

export function TiltCardLight({ children, className = '' }: { children: ReactNode; className?: string }) {
  const reduceMotion = useReducedMotion()
  return (
    <motion.div
      className={`rounded-xl border border-slate-200 bg-white shadow-sm ${className}`}
      whileHover={reduceMotion ? undefined : { y: -3, scale: 1.015, boxShadow: '0 16px 32px -12px rgba(15,23,42,0.18)' }}
      transition={{ type: 'spring', stiffness: 300, damping: 22 }}
    >
      {children}
    </motion.div>
  )
}

export function StatCardLight({
  label, value, sublabel, accent = CATEGORICAL[0],
}: { label: string; value: string | number; sublabel?: string; accent?: string }) {
  return (
    <TiltCardLight className="p-5">
      <p className="text-xs text-slate-500 font-body uppercase tracking-wider mb-1.5">{label}</p>
      <p className="text-2xl lg:text-3xl font-mono font-extrabold tracking-tight" style={{ color: accent }}>{value}</p>
      {sublabel && <p className="text-[11px] text-slate-400 font-body mt-1">{sublabel}</p>}
    </TiltCardLight>
  )
}

export function GaugeRadialLight({ porcentaje, label, color = STATUS.good }: { porcentaje: number | null; label: string; color?: string }) {
  const valor = porcentaje ?? 0
  const data = [{ name: label, value: valor, fill: color }]
  return (
    <TiltCardLight className="p-5 flex flex-col items-center">
      <div className="w-full h-36 relative">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart innerRadius="70%" outerRadius="100%" data={data} startAngle={90} endAngle={-270}>
            <RadialAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
            <RadialBar background={{ fill: '#F1F5F9' }} dataKey="value" cornerRadius={8} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-mono font-extrabold text-slate-800">{porcentaje === null ? '—' : `${valor}%`}</span>
        </div>
      </div>
      <p className="text-xs text-slate-500 font-body text-center mt-1">{label}</p>
    </TiltCardLight>
  )
}

export function DonutChartLight({ data, colors = CATEGORICAL }: { data: { clave: string; valor: number }[]; colors?: readonly string[] }) {
  const total = data.reduce((s, d) => s + d.valor, 0)
  if (total === 0) return <TiltCardLight className="p-5"><SinDatosLight height={208} /></TiltCardLight>
  return (
    <TiltCardLight className="p-5">
      <div className="h-52">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="valor" nameKey="clave" innerRadius="55%" outerRadius="85%" paddingAngle={2}>
              {data.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
            </Pie>
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              formatter={(v, n) => {
                const num = typeof v === 'number' ? v : Number(v ?? 0)
                return [`${num} (${total ? Math.round(num / total * 100) : 0}%)`, String(n)]
              }}
            />
            <Legend wrapperStyle={{ fontSize: 11, color: '#475569' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </TiltCardLight>
  )
}

export function RadarWidgetLight({ data, keys, colors = CATEGORICAL }: { data: Record<string, any>[]; keys: string[]; colors?: readonly string[] }) {
  if (data.length === 0) return <TiltCardLight className="p-5"><SinDatosLight height={256} /></TiltCardLight>
  return (
    <TiltCardLight className="p-5">
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data}>
            <PolarGrid stroke={GRID_STROKE} />
            <PolarAngleAxis dataKey="categoria" tick={{ fontSize: 10, fill: '#475569' }} />
            <PolarRadiusAxis tick={{ fontSize: 9, fill: '#64748B' }} />
            {keys.map((k, i) => (
              <Radar key={k} name={k} dataKey={k} stroke={colors[i % colors.length]} fill={colors[i % colors.length]} fillOpacity={0.25} />
            ))}
            <Legend wrapperStyle={{ fontSize: 11, color: '#475569' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </TiltCardLight>
  )
}

export function BarHorizontalLight({
  data, dataKey = 'valor', nameKey = 'clave', color = CATEGORICAL[0],
}: { data: Record<string, any>[]; dataKey?: string; nameKey?: string; color?: string }) {
  if (data.length === 0) return <TiltCardLight className="p-5"><SinDatosLight /></TiltCardLight>
  return (
    <TiltCardLight className="p-5">
      <div style={{ height: Math.max(120, data.length * 42) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} horizontal={false} />
            <XAxis type="number" tick={AXIS_TICK} />
            <YAxis type="category" dataKey={nameKey} tick={{ fontSize: 11, fill: '#475569' }} width={110} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Bar dataKey={dataKey} fill={color} radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </TiltCardLight>
  )
}

export function BarLineComboLight({
  data, barKey, lineKey, color = CATEGORICAL[0], lineColor = CATEGORICAL[1], xKey = 'periodo',
}: { data: Record<string, any>[]; barKey: string; lineKey: string; color?: string; lineColor?: string; xKey?: string }) {
  if (data.length === 0) return <TiltCardLight className="p-5"><SinDatosLight height={256} /></TiltCardLight>
  return (
    <TiltCardLight className="p-5">
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ left: 0, right: 16, top: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
            <XAxis dataKey={xKey} tick={AXIS_TICK} />
            <YAxis tick={AXIS_TICK} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: 11, color: '#475569' }} />
            <Bar dataKey={barKey} fill={color} radius={[4, 4, 0, 0]} />
            <Line type="monotone" dataKey={lineKey} stroke={lineColor} strokeWidth={2} dot={{ r: 3 }} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </TiltCardLight>
  )
}

export function MultiLineWidgetLight({
  data, keys, colors = CATEGORICAL, xKey = 'fecha', height = 240,
}: { data: Record<string, any>[]; keys: string[]; colors?: readonly string[]; xKey?: string; height?: number }) {
  if (data.length === 0) return <TiltCardLight className="p-5"><SinDatosLight height={height} /></TiltCardLight>
  return (
    <TiltCardLight className="p-5">
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ left: 0, right: 16, top: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
            <XAxis dataKey={xKey} tick={AXIS_TICK} />
            <YAxis tick={AXIS_TICK} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: 11, color: '#475569' }} />
            {keys.map((k, i) => (
              <Line key={k} type="monotone" dataKey={k} stroke={colors[i % colors.length]} strokeWidth={2} dot={{ r: 3 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </TiltCardLight>
  )
}
