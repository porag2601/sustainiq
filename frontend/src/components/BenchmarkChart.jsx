import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { formatNumber, metricLabel } from '../metrics'

// Why scores and not raw values: the six metrics have different units
// (kWh, t CO2e, m³, %), so they cannot share one axis honestly. The score
// puts every metric on the same 0-100 scale, where 50 = sector benchmark.

// Recharts draws SVG and needs colours as values, not Tailwind classes.
// BAR: slot 1 of the validated categorical palette (dataviz skill), passes
// contrast on white. Kept distinct from the green/amber/red status badges.
const COLORS = {
  bar: '#2a78d6',
  benchmark: '#52514e', // neutral grey: the benchmark is a reference, not data
  grid: '#e2e8f0', // slate-200: recessive, so the bars stand out
  text: '#334155', // slate-700: text never wears the data colour
}

const BAR_SIZE = 24 // thin bars; the rest of each row stays white space

// Custom hover box: shows the real values behind the score.
function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const metric = payload[0].payload
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3 text-sm shadow">
      <p className="font-semibold">{metric.label}</p>
      <p>Score: {metric.score} / 100</p>
      <p className="text-slate-600">
        {formatNumber(metric.value)} vs. benchmark {formatNumber(metric.benchmark_value)}
      </p>
      <p className="text-xs text-slate-500">{metric.unit}</p>
    </div>
  )
}

function BenchmarkChart({ metrics }) {
  const data = metrics.map((metric) => ({ ...metric, label: metricLabel(metric.key) }))
  // One row per metric; the height grows with the number of rows.
  const height = data.length * 48 + 40

  return (
    // figure + figcaption describe the chart for screen readers. The metric
    // cards below show the same numbers as text, so nothing is chart-only.
    <figure className="rounded-lg bg-white p-6 shadow">
      <figcaption>
        <h2 className="text-xl font-semibold">Score per metric</h2>
        <p className="mt-1 text-sm text-slate-600">
          0-100 per metric. The dashed line at 50 is the indicative sector benchmark: bars past the
          line are better than the sector.
        </p>
      </figcaption>

      <div className="mt-4">
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data} layout="vertical" margin={{ top: 8, right: 40, bottom: 8, left: 8 }}>
            <CartesianGrid horizontal={false} stroke={COLORS.grid} />
            <XAxis
              type="number"
              domain={[0, 100]}
              ticks={[0, 25, 50, 75, 100]}
              tick={{ fill: COLORS.text, fontSize: 12 }}
              stroke={COLORS.grid}
            />
            <YAxis
              type="category"
              dataKey="label"
              width={150}
              tick={{ fill: COLORS.text, fontSize: 12 }}
              stroke={COLORS.grid}
            />
            <Tooltip content={<ChartTooltip />} cursor={{ fill: '#f1f5f9' }} />
            <Bar dataKey="score" fill={COLORS.bar} barSize={BAR_SIZE} radius={[0, 4, 4, 0]}>
              {/* Value at the bar tip, in text colour. */}
              <LabelList dataKey="score" position="right" fill={COLORS.text} fontSize={12} />
            </Bar>
            {/* Drawn after the bars so the line stays visible on top of them. */}
            <ReferenceLine
              x={50}
              stroke={COLORS.benchmark}
              strokeDasharray="4 4"
              strokeWidth={2}
              label={{ value: 'Benchmark', position: 'top', fill: COLORS.text, fontSize: 12 }}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </figure>
  )
}

export default BenchmarkChart
