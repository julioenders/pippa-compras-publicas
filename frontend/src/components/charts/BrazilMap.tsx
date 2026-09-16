import { useState, useCallback } from 'react'

interface UFData {
  uf: string
  percentual_mpe: number
  total_contratacoes: number
  valor_total: number
}

interface Props {
  data: UFData[]
}

interface TooltipState {
  visible: boolean
  x: number
  y: number
  uf: string
  percentual_mpe: number
  total_contratacoes: number
  valor_total: number
}

const UF_NAMES: Record<string, string> = {
  AC: 'Acre',
  AL: 'Alagoas',
  AM: 'Amazonas',
  AP: 'Amapá',
  BA: 'Bahia',
  CE: 'Ceará',
  DF: 'Distrito Federal',
  ES: 'Espírito Santo',
  GO: 'Goiás',
  MA: 'Maranhão',
  MG: 'Minas Gerais',
  MS: 'Mato Grosso do Sul',
  MT: 'Mato Grosso',
  PA: 'Pará',
  PB: 'Paraíba',
  PE: 'Pernambuco',
  PI: 'Piauí',
  PR: 'Paraná',
  RJ: 'Rio de Janeiro',
  RN: 'Rio Grande do Norte',
  RO: 'Rondônia',
  RR: 'Roraima',
  RS: 'Rio Grande do Sul',
  SC: 'Santa Catarina',
  SE: 'Sergipe',
  SP: 'São Paulo',
  TO: 'Tocantins',
}

const STATE_PATHS: Record<string, string> = {
  AM: 'M 30,100 L 180,100 L 180,200 L 145,220 L 100,220 L 30,200 Z',
  RR: 'M 100,20 L 145,20 L 145,95 L 100,95 Z',
  AP: 'M 230,30 L 270,30 L 270,100 L 230,100 Z',
  PA: 'M 185,80 L 310,80 L 310,180 L 260,200 L 185,200 Z',
  MA: 'M 315,100 L 370,100 L 370,175 L 315,175 Z',
  PI: 'M 375,115 L 410,115 L 410,200 L 375,200 Z',
  CE: 'M 415,100 L 460,100 L 460,155 L 415,155 Z',
  RN: 'M 450,105 L 490,105 L 490,135 L 450,135 Z',
  PB: 'M 450,140 L 490,140 L 490,165 L 450,165 Z',
  PE: 'M 415,160 L 490,160 L 490,190 L 415,190 Z',
  AL: 'M 460,195 L 490,195 L 490,220 L 460,220 Z',
  SE: 'M 445,195 L 455,195 L 455,220 L 445,220 Z',
  BA: 'M 350,180 L 440,180 L 460,225 L 440,310 L 370,310 L 350,260 Z',
  TO: 'M 260,205 L 310,205 L 310,310 L 260,310 Z',
  MT: 'M 150,225 L 255,225 L 255,340 L 150,340 Z',
  GO: 'M 260,315 L 350,315 L 365,375 L 310,400 L 260,380 Z',
  DF: 'M 330,335 L 355,335 L 355,355 L 330,355 Z',
  MG: 'M 320,310 L 430,310 L 430,400 L 350,410 L 320,380 Z',
  ES: 'M 435,340 L 470,340 L 470,390 L 435,390 Z',
  RJ: 'M 395,405 L 445,395 L 450,420 L 395,430 Z',
  SP: 'M 290,400 L 390,400 L 390,450 L 320,460 L 290,440 Z',
  MS: 'M 180,345 L 255,345 L 255,440 L 210,460 L 180,430 Z',
  PR: 'M 260,445 L 340,440 L 340,480 L 260,490 Z',
  SC: 'M 280,485 L 345,485 L 345,515 L 280,515 Z',
  RS: 'M 260,520 L 340,520 L 320,580 L 270,580 Z',
  RO: 'M 80,225 L 145,225 L 145,310 L 80,310 Z',
  AC: 'M 10,225 L 75,225 L 75,280 L 10,280 Z',
}

const STATE_LABEL_POS: Record<string, { x: number; y: number }> = {
  AM: { x: 105, y: 165 },
  RR: { x: 122, y: 62 },
  AP: { x: 250, y: 70 },
  PA: { x: 247, y: 145 },
  MA: { x: 342, y: 142 },
  PI: { x: 392, y: 162 },
  CE: { x: 437, y: 130 },
  RN: { x: 470, y: 123 },
  PB: { x: 470, y: 155 },
  PE: { x: 452, y: 178 },
  AL: { x: 475, y: 210 },
  SE: { x: 450, y: 210 },
  BA: { x: 400, y: 250 },
  TO: { x: 285, y: 260 },
  MT: { x: 202, y: 285 },
  GO: { x: 305, y: 355 },
  DF: { x: 342, y: 348 },
  MG: { x: 375, y: 360 },
  ES: { x: 452, y: 368 },
  RJ: { x: 422, y: 415 },
  SP: { x: 340, y: 430 },
  MS: { x: 217, y: 395 },
  PR: { x: 300, y: 468 },
  SC: { x: 312, y: 503 },
  RS: { x: 300, y: 552 },
  RO: { x: 112, y: 270 },
  AC: { x: 42, y: 255 },
}

const COLOR_SCALE = [
  { min: 0, max: 20, color: '#e74c3c', label: '0–20%' },
  { min: 20, max: 30, color: '#f39c12', label: '20–30%' },
  { min: 30, max: 40, color: '#2ecc71', label: '30–40%' },
  { min: 40, max: Infinity, color: '#27ae60', label: '40%+' },
]

const NO_DATA_COLOR = '#374151'

function getColor(percentual: number | undefined): string {
  if (percentual === undefined) return NO_DATA_COLOR
  for (const band of COLOR_SCALE) {
    if (percentual >= band.min && percentual < band.max) return band.color
  }
  return COLOR_SCALE[COLOR_SCALE.length - 1]!.color
}

const currencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
})

const numberFormatter = new Intl.NumberFormat('pt-BR')

export default function BrazilMap({ data }: Props) {
  const [tooltip, setTooltip] = useState<TooltipState>({
    visible: false,
    x: 0,
    y: 0,
    uf: '',
    percentual_mpe: 0,
    total_contratacoes: 0,
    valor_total: 0,
  })

  const dataMap = new Map(data.map((d) => [d.uf, d]))

  const handleMouseEnter = useCallback(
    (uf: string, event: React.MouseEvent<SVGPathElement>) => {
      const rect = (event.currentTarget.closest('svg') as SVGSVGElement).getBoundingClientRect()
      const x = event.clientX - rect.left
      const y = event.clientY - rect.top
      const ufData = dataMap.get(uf)
      setTooltip({
        visible: true,
        x,
        y,
        uf,
        percentual_mpe: ufData?.percentual_mpe ?? 0,
        total_contratacoes: ufData?.total_contratacoes ?? 0,
        valor_total: ufData?.valor_total ?? 0,
      })
    },
    [dataMap],
  )

  const handleMouseMove = useCallback(
    (event: React.MouseEvent<SVGPathElement>) => {
      const rect = (event.currentTarget.closest('svg') as SVGSVGElement).getBoundingClientRect()
      const x = event.clientX - rect.left
      const y = event.clientY - rect.top
      setTooltip((prev) => ({ ...prev, x, y }))
    },
    [],
  )

  const handleMouseLeave = useCallback(() => {
    setTooltip((prev) => ({ ...prev, visible: false }))
  }, [])

  return (
    <div className="rounded-xl border border-white/5 bg-obs-bg p-4">
      <h3 className="mb-3 text-sm font-medium text-gray-400">
        Participação MPE por UF (%)
      </h3>

      <div className="relative">
        <svg viewBox="0 0 500 600" className="w-full" xmlns="http://www.w3.org/2000/svg">
          {Object.entries(STATE_PATHS).map(([uf, path]) => {
            const ufData = dataMap.get(uf)
            const fill = getColor(ufData?.percentual_mpe)
            return (
              <g key={uf}>
                <path
                  d={path}
                  fill={fill}
                  stroke="#132D42"
                  strokeWidth={1.5}
                  className="cursor-pointer transition-opacity hover:opacity-80"
                  onMouseEnter={(e) => handleMouseEnter(uf, e)}
                  onMouseMove={handleMouseMove}
                  onMouseLeave={handleMouseLeave}
                />
                <text
                  x={STATE_LABEL_POS[uf]!.x}
                  y={STATE_LABEL_POS[uf]!.y}
                  fill="#ffffff"
                  fontSize={10}
                  fontWeight={600}
                  textAnchor="middle"
                  dominantBaseline="central"
                  className="pointer-events-none select-none"
                >
                  {uf}
                </text>
              </g>
            )
          })}
        </svg>

        {tooltip.visible && (
          <div
            className="pointer-events-none absolute z-50 rounded-lg border border-white/10 px-3 py-2 text-xs shadow-lg"
            style={{
              left: tooltip.x + 12,
              top: tooltip.y - 10,
              backgroundColor: '#1a2332',
            }}
          >
            <p className="font-semibold text-white">
              {UF_NAMES[tooltip.uf] ?? tooltip.uf}
            </p>
            <p className="mt-1 text-gray-300">
              MPE: {tooltip.percentual_mpe.toFixed(1)}%
            </p>
            <p className="text-gray-300">
              Contratações: {numberFormatter.format(tooltip.total_contratacoes)}
            </p>
            <p className="text-gray-300">
              Valor: {currencyFormatter.format(tooltip.valor_total)}
            </p>
          </div>
        )}
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-center gap-4">
        {COLOR_SCALE.map((band) => (
          <div key={band.label} className="flex items-center gap-1.5">
            <span
              className="inline-block h-3 w-3 rounded-sm"
              style={{ backgroundColor: band.color }}
            />
            <span className="text-xs text-gray-400">{band.label}</span>
          </div>
        ))}
        <div className="flex items-center gap-1.5">
          <span
            className="inline-block h-3 w-3 rounded-sm"
            style={{ backgroundColor: NO_DATA_COLOR }}
          />
          <span className="text-xs text-gray-400">Sem dados</span>
        </div>
      </div>
    </div>
  )
}
