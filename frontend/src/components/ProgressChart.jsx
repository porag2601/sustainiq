import { useEffect, useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { listAssessments } from '../api/client'
import { formatDate } from '../metrics'

// Same colour roles as BenchmarkChart.jsx (validated series colour, grey benchmark).
const COLORS = {
  line: '#2a78d6',
  benchmark: '#52514e',
  grid: '#e2e8f0',
  text: '#334155',
  surface: '#ffffff',
}

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3 text-sm shadow">
      <p className="font-semibold">Assessment #{point.id}</p>
      <p className="text-slate-600">{point.date}</p>
      <p>Score: {point.score} / 100</p>
    </div>
  )
}

// Overall score of one company across all its saved assessments.
function ProgressChart({ companyName }) {
  const [history, setHistory] = useState(null) // null = loading
  const [error, setError] = useState(null)

  useEffect(() => {
    let ignore = false // see PastAssessments.jsx
    listAssessments(companyName)
      .then((rows) => !ignore && setHistory(rows))
      .catch((err) => !ignore && setError(err.message))
    return () => {
      ignore = true
    }
  }, [companyName])

  if (error) return null // progress is extra information; the report works without it
  if (history === null) return null

  // The API sends newest first; a chart over time reads left (old) to right (new).
  const points = [...history].reverse().map((row) => ({
    id: row.id,
    date: formatDate(row.created_at),
    score: row.overall_score,
  }))

  return (
    <figure className="rounded-lg bg-white p-6 shadow">
      <figcaption>
        <h2 className="text-xl font-semibold">Progress over time</h2>
        {points.length < 2 ? (
          <p className="mt-2 text-sm text-slate-600">
            This is the first saved assessment for {companyName}. Run another one later (for example next
            year) with the same company name to see the progress here.
          </p>
        ) : (
          <p className="mt-1 text-sm text-slate-600">
            {points.length} assessments. Change since the previous one:{' '}
            <span className="font-medium text-slate-900">
              {formatChange(points.at(-1).score - points.at(-2).score)} points
            </span>
          </p>
        )}
      </figcaption>

      {points.length >= 2 && (
        <div className="mt-4">
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={points} margin={{ top: 16, right: 24, bottom: 8, left: 0 }}>
              <CartesianGrid vertical={false} stroke={COLORS.grid} />
              {/* One point per assessment. Dates are labels, so uneven gaps
                  between assessments are not shown to scale. */}
              <XAxis dataKey="date" tick={{ fill: COLORS.text, fontSize: 12 }} stroke={COLORS.grid} />
              <YAxis
                domain={[0, 100]}
                ticks={[0, 25, 50, 75, 100]}
                tick={{ fill: COLORS.text, fontSize: 12 }}
                stroke={COLORS.grid}
                width={36}
              />
              <Tooltip content={<ChartTooltip />} />
              <ReferenceLine
                y={50}
                stroke={COLORS.benchmark}
                strokeDasharray="4 4"
                label={{ value: 'Benchmark', position: 'insideTopRight', fill: COLORS.text, fontSize: 12 }}
              />
              {/* 2px line, 8px dots with a white ring so they stay visible where they overlap. */}
              <Line
                type="linear"
                dataKey="score"
                stroke={COLORS.line}
                strokeWidth={2}
                dot={{ r: 4, fill: COLORS.line, stroke: COLORS.surface, strokeWidth: 2 }}
                activeDot={{ r: 6, fill: COLORS.line, stroke: COLORS.surface, strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </figure>
  )
}

// 5.24 -> "+5.2", -3 -> "-3.0"
function formatChange(value) {
  return `${value > 0 ? '+' : ''}${value.toFixed(1)}`
}

export default ProgressChart
