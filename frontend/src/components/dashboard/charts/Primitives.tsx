'use client'

import { ReactNode } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  RadialBarChart, RadialBar, PolarAngleAxis as RadialAngleAxis,
} from 'recharts'
import { CATEGORICAL, STATUS } from '@/src/lib/chartColors'

const TOOLTIP_STYLE = {
  background: '#1E293B',
  border: '1px solid #334155',
  borderRadius: 8,
  fontSize: 12,
  color: '#E2E8F0',
}

function SinDatos({ height = 208 }: { height?: number }) {
  return (
    <div style={{ height }} className="flex items-center justify-center text-xs text-slate-500 font-body text-center px-4">
      Sin datos en este período todavía.
    </div>
  )
}

/** Tarjeta flotante con elevación/tilt al hover — estándar transversal. */
export function TiltCard({ children, className = '' }: { children: ReactNode; className?: string }) {
  const reduceMotion = useReducedMotion()
  return (
    <motion.div
      className={`rounded-xl border border-slate-700/80 bg-gradient-to-br from-slate-800 to-slate-900 shadow-lg ${className}`}
      whileHover={reduceMotion ? undefined : { y: -3, scale: 1.015, boxShadow: '0 20px 40px -12px rgba(0,0,0,0.45)' }}
      transition={{ type: 'spring', stiffness: 300, damping: 22 }}
    >
      {children}
    </motion.div>
  )
}

export function StatCard({
  label, value, sublabel, accent = CATEGORICAL[0],
}: { label: string; value: string | number; sublabel?: string; accent?: string }) {
  return (
    <TiltCard className="p-5">
      <p className="text-xs text-slate-400 font-body uppercase tracking-wider mb-1.5">{label}</p>
      <p className="text-2xl lg:text-3xl font-mono font-extrabold tracking-tight" style={{ color: accent }}>
        {value}
      </p>
      {sublabel && <p className="text-[11px] text-slate-500 font-body mt-1">{sublabel}</p>}
    </TiltCard>
  )
}

export function IconStatCard({
  label, value, icon,
}: { label: string; value: string | number; icon: ReactNode }) {
  return (
    <TiltCard className="p-4 flex items-center gap-3">
      <div className="w-10 h-10 rounded-lg bg-teal/10 text-teal flex items-center justify-center shrink-0">{icon}</div>
      <div className="min-w-0">
        <p className="text-lg font-mono font-bold text-slate-100 leading-tight">{value}</p>
        <p className="text-[11px] text-slate-400 font-body truncate">{label}</p>
      </div>
    </TiltCard>
  )
}

export function MiniSparkline({ data, color = CATEGORICAL[0] }: { data: { fecha: string; valor: number }[]; color?: string }) {
  return (
    <div className="h-10 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <Line type="monotone" dataKey="valor" stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function GaugeRadial({ porcentaje, label, color = STATUS.good }: { porcentaje: number | null; label: string; color?: string }) {
  const valor = porcentaje ?? 0
  const data = [{ name: label, value: valor, fill: color }]
  return (
    <TiltCard className="p-5 flex flex-col items-center">
      <div className="w-full h-36 relative">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart innerRadius="70%" outerRadius="100%" data={data} startAngle={90} endAngle={-270}>
            <RadialAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
            <RadialBar background dataKey="value" cornerRadius={8} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-mono font-extrabold text-slate-100">
            {porcentaje === null ? '—' : `${valor}%`}
          </span>
        </div>
      </div>
      <p className="text-xs text-slate-400 font-body text-center mt-1">{label}</p>
    </TiltCard>
  )
}

export function DonutChart({
  data, colors = CATEGORICAL,
}: { data: { clave: string; valor: number }[]; colors?: readonly string[] }) {
  const total = data.reduce((s, d) => s + d.valor, 0)
  if (total === 0) return <TiltCard className="p-5"><SinDatos height={208} /></TiltCard>
  return (
    <TiltCard className="p-5">
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
            <Legend wrapperStyle={{ fontSize: 11, color: '#94A3B8' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </TiltCard>
  )
}

export function BarRankingHorizontal({
  data, dataKey = 'total', nameKey = 'nombre', color = CATEGORICAL[0],
}: { data: Record<string, any>[]; dataKey?: string; nameKey?: string; color?: string }) {
  if (data.length === 0) return <TiltCard className="p-5"><SinDatos /></TiltCard>
  return (
    <TiltCard className="p-5">
      <div style={{ height: Math.max(120, data.length * 42) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 10, fill: '#64748B' }} />
            <YAxis type="category" dataKey={nameKey} tick={{ fontSize: 11, fill: '#94A3B8' }} width={110} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Bar dataKey={dataKey} fill={color} radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </TiltCard>
  )
}

export function BarVertical({
  data, dataKey = 'valor', nameKey = 'clave', color = CATEGORICAL[0], height = 240,
}: { data: Record<string, any>[]; dataKey?: string; nameKey?: string; color?: string; height?: number }) {
  const total = data.reduce((s, d) => s + (Number(d[dataKey]) || 0), 0)
  if (data.length === 0 || total === 0) return <TiltCard className="p-5"><SinDatos height={height} /></TiltCard>
  return (
    <TiltCard className="p-5">
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ left: 0, right: 8, top: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
            <XAxis dataKey={nameKey} tick={{ fontSize: 10, fill: '#64748B' }} />
            <YAxis tick={{ fontSize: 10, fill: '#64748B' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Bar dataKey={dataKey} fill={color} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </TiltCard>
  )
}

export function RadarWidget({
  data, keys, colors = CATEGORICAL,
}: { data: Record<string, any>[]; keys: string[]; colors?: readonly string[] }) {
  if (data.length === 0) return <TiltCard className="p-5"><SinDatos height={256} /></TiltCard>
  return (
    <TiltCard className="p-5">
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data}>
            <PolarGrid stroke="#1E293B" />
            <PolarAngleAxis dataKey="categoria" tick={{ fontSize: 10, fill: '#94A3B8' }} />
            <PolarRadiusAxis tick={{ fontSize: 9, fill: '#64748B' }} />
            {keys.map((k, i) => (
              <Radar key={k} name={k} dataKey={k} stroke={colors[i % colors.length]} fill={colors[i % colors.length]} fillOpacity={0.25} />
            ))}
            <Legend wrapperStyle={{ fontSize: 11, color: '#94A3B8' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </TiltCard>
  )
}

export function ScatterWidget({
  data, xKey, yKey, color = CATEGORICAL[1],
}: { data: Record<string, any>[]; xKey: string; yKey: string; color?: string }) {
  if (data.length === 0) return <TiltCard className="p-5"><SinDatos height={256} /></TiltCard>
  return (
    <TiltCard className="p-5">
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ left: 0, right: 16, top: 8, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
            <XAxis type="number" dataKey={xKey} name="Horas" tick={{ fontSize: 10, fill: '#64748B' }} />
            <YAxis type="number" dataKey={yKey} name="Monto" tick={{ fontSize: 10, fill: '#64748B' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ strokeDasharray: '3 3' }} />
            <Scatter data={data} fill={color} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </TiltCard>
  )
}

export function StackedBarWidget({
  data, keys, colors = CATEGORICAL, height = 260,
}: { data: Record<string, any>[]; keys: string[]; colors?: readonly string[]; height?: number }) {
  if (data.length === 0) return <TiltCard className="p-5"><SinDatos height={height} /></TiltCard>
  return (
    <TiltCard className="p-5">
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ left: 0, right: 8, top: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
            <XAxis dataKey="mes" tick={{ fontSize: 10, fill: '#64748B' }} />
            <YAxis tick={{ fontSize: 10, fill: '#64748B' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: 11, color: '#94A3B8' }} />
            {keys.map((k, i) => (
              <Bar key={k} dataKey={k} stackId="a" fill={colors[i % colors.length]} radius={i === keys.length - 1 ? [4, 4, 0, 0] : undefined} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </TiltCard>
  )
}

export function MultiLineWidget({
  data, keys, colors = CATEGORICAL, xKey = 'mes', height = 260,
}: { data: Record<string, any>[]; keys: string[]; colors?: readonly string[]; xKey?: string; height?: number }) {
  if (data.length === 0) return <TiltCard className="p-5"><SinDatos height={height} /></TiltCard>
  return (
    <TiltCard className="p-5">
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ left: 0, right: 16, top: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
            <XAxis dataKey={xKey} tick={{ fontSize: 10, fill: '#64748B' }} />
            <YAxis tick={{ fontSize: 10, fill: '#64748B' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: 11, color: '#94A3B8' }} />
            {keys.map((k, i) => (
              <Line key={k} type="monotone" dataKey={k} stroke={colors[i % colors.length]} strokeWidth={2} dot={{ r: 3 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </TiltCard>
  )
}
