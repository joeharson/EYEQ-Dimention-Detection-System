"use client"

import { Navigation } from "@/components/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  CheckCircle2,
  XCircle,
  TrendingUp,
  TrendingDown,
  Download,
  Calendar,
  AlertTriangle,
  Activity,
} from "lucide-react"
import { useEffect, useState } from "react"
import { apiClient } from "@/lib/api"
import {
  Bar,
  BarChart,
  Line,
  LineChart,
  Pie,
  PieChart,
  Cell,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Legend,
} from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const defectTrendData = [
  { month: "Jan", defects: 45 },
  { month: "Feb", defects: 52 },
  { month: "Mar", defects: 38 },
  { month: "Apr", defects: 41 },
  { month: "May", defects: 35 },
  { month: "Jun", defects: 28 },
]

const toleranceData = [
  { component: "Washers", inSpec: 420, outSpec: 32 },
  { component: "Bolts", outSpec: 45, inSpec: 542 },
  { component: "Nuts", inSpec: 309, outSpec: 32 },
]

const componentDefectsData = [
  { name: "Dimensional", value: 42, color: "hsl(var(--chart-1))" },
  { name: "Surface", value: 28, color: "hsl(var(--chart-2))" },
  { name: "Material", value: 18, color: "hsl(var(--chart-3))" },
  { name: "Thread", value: 12, color: "hsl(var(--chart-4))" },
]

const chartConfig = {
  defects: {
    label: "Defects",
    color: "hsl(var(--chart-1))",
  },
  inSpec: {
    label: "In Spec",
    color: "hsl(var(--chart-2))",
  },
  outSpec: {
    label: "Out of Spec",
    color: "hsl(var(--destructive))",
  },
}

export default function DashboardPage() {
  const [stats, setStats] = useState({
    total_inspections: 0,
    defective_count: 0,
    pass_rate: 0,
    avg_deviation: 0,
  })
  const [recentInspections, setRecentInspections] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsData, inspectionsData] = await Promise.all([
          apiClient.getDashboardStats(),
          apiClient.getRecentInspections(5),
        ])
        setStats(statsData)
        setRecentInspections(inspectionsData.inspections)
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    // Refresh every 5 seconds
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="pt-24 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-foreground mb-3">Analytics Dashboard</h1>
              <p className="text-lg text-muted-foreground">Real-time quality metrics and performance insights</p>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" className="gap-2 bg-transparent">
                <Calendar className="w-4 h-4" />
                Last 30 Days
              </Button>
              <Button className="gap-2">
                <Download className="w-4 h-4" />
                Export Report
              </Button>
            </div>
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card className="p-6 bg-card border-primary/30">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Activity className="w-6 h-6 text-primary" />
                </div>
                <Badge className="bg-primary/20 text-primary gap-1 hover:bg-primary/20">
                  <TrendingUp className="w-3 h-3" />
                  12%
                </Badge>
              </div>
              <div className="text-3xl font-bold text-foreground mb-1 font-mono">
                {loading ? "..." : stats.total_inspections.toLocaleString()}
              </div>
              <div className="text-sm text-muted-foreground">Total Inspections</div>
              <div className="text-xs text-primary mt-2">Live data</div>
            </Card>

            <Card className="p-6 bg-card border-secondary/30">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-lg bg-secondary/10 flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6 text-secondary" />
                </div>
                <Badge className="bg-secondary/20 text-secondary gap-1 hover:bg-secondary/20">
                  <TrendingUp className="w-3 h-3" />
                  1.8%
                </Badge>
              </div>
              <div className="text-3xl font-bold text-foreground mb-1 font-mono">
                {loading ? "..." : `${stats.pass_rate.toFixed(1)}%`}
              </div>
              <div className="text-sm text-muted-foreground">Pass Rate</div>
              <div className="text-xs text-secondary mt-2">Real-time</div>
            </Card>

            <Card className="p-6 bg-card border-destructive/30">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-lg bg-destructive/10 flex items-center justify-center">
                  <XCircle className="w-6 h-6 text-destructive" />
                </div>
                <Badge variant="destructive" className="gap-1">
                  <TrendingDown className="w-3 h-3" />
                  15%
                </Badge>
              </div>
              <div className="text-3xl font-bold text-foreground mb-1 font-mono">
                {loading ? "..." : stats.defective_count}
              </div>
              <div className="text-sm text-muted-foreground">Total Defects</div>
              <div className="text-xs text-destructive mt-2">Live count</div>
            </Card>

            <Card className="p-6 bg-card border-accent/30">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-accent" />
                </div>
                <Badge className="bg-accent/20 text-accent gap-1 hover:bg-accent/20">
                  <TrendingDown className="w-3 h-3" />
                  8%
                </Badge>
              </div>
              <div className="text-3xl font-bold text-foreground mb-1 font-mono">
                {loading ? "..." : `±${stats.avg_deviation.toFixed(2)}`}
              </div>
              <div className="text-sm text-muted-foreground">Avg Deviation (mm)</div>
              <div className="text-xs text-accent mt-2">Real-time</div>
            </Card>
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Defect Trends */}
            <Card className="p-6 bg-card">
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-card-foreground mb-2">Defect Trends</h2>
                <p className="text-sm text-muted-foreground">Monthly defect detection over time</p>
              </div>

              <ChartContainer config={chartConfig} className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={defectTrendData}>
                    <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Line
                      type="monotone"
                      dataKey="defects"
                      stroke="hsl(var(--chart-1))"
                      strokeWidth={3}
                      dot={{ fill: "hsl(var(--chart-1))", r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartContainer>

              <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
                <TrendingDown className="w-4 h-4 text-primary" />
                <span>38% reduction in defects since January</span>
              </div>
            </Card>

            {/* Component Defect Distribution */}
            <Card className="p-6 bg-card">
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-card-foreground mb-2">Defect Types Distribution</h2>
                <p className="text-sm text-muted-foreground">Breakdown by defect category</p>
              </div>

              <div className="flex items-center justify-center">
                <ChartContainer config={chartConfig} className="h-[300px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={componentDefectsData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {componentDefectsData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <ChartTooltip content={<ChartTooltipContent />} />
                    </PieChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </div>

              <div className="grid grid-cols-2 gap-3 mt-4">
                {componentDefectsData.map((item, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: item.color }} />
                    <span className="text-sm text-muted-foreground">
                      {item.name} ({item.value}%)
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Tolerance Deviations by Component */}
          <Card className="p-6 bg-card mb-8">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-card-foreground mb-2">Tolerance Deviations by Component</h2>
              <p className="text-sm text-muted-foreground">Comparison of in-spec vs out-of-spec measurements</p>
            </div>

            <ChartContainer config={chartConfig} className="h-[350px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={toleranceData}>
                  <XAxis dataKey="component" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Legend />
                  <Bar dataKey="inSpec" fill="hsl(var(--chart-2))" radius={[4, 4, 0, 0]} name="In Spec" />
                  <Bar dataKey="outSpec" fill="hsl(var(--destructive))" radius={[4, 4, 0, 0]} name="Out of Spec" />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          </Card>

          {/* Recent Inspections */}
          <Card className="p-6 bg-card">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-card-foreground mb-2">Recent Inspections</h2>
              <p className="text-sm text-muted-foreground">Latest quality control results</p>
            </div>

            <div className="space-y-3">
              {loading ? (
                <div className="text-center py-8 text-muted-foreground">Loading inspections...</div>
              ) : recentInspections.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">No inspections yet</div>
              ) : (
                recentInspections.map((inspection, index) => {
                  const isPass = inspection.status === "NOT DEFECTIVE"
                  const timeAgo = inspection.timestamp
                    ? new Date(inspection.timestamp * 1000).toLocaleString()
                    : "Unknown time"
                  
                  return (
                    <div key={index} className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
                      <div className="flex items-center gap-4">
                        <div
                          className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            isPass ? "bg-primary/10" : "bg-destructive/10"
                          }`}
                        >
                          {isPass ? (
                            <CheckCircle2 className="w-5 h-5 text-primary" />
                          ) : (
                            <XCircle className="w-5 h-5 text-destructive" />
                          )}
                        </div>
                        <div>
                          <div className="font-medium text-foreground">
                            Inspection #{index + 1}
                          </div>
                          <div className="text-sm text-muted-foreground">{timeAgo}</div>
                        </div>
                      </div>
                      <Badge
                        variant={isPass ? "default" : "destructive"}
                        className={isPass ? "bg-primary/20 text-primary hover:bg-primary/20" : ""}
                      >
                        {isPass ? "Pass" : "Defect"}
                      </Badge>
                    </div>
                  )
                })
              )}
            </div>

            <div className="mt-6 text-center">
              <Button variant="outline" className="w-full bg-transparent">
                View All Inspections
              </Button>
            </div>
          </Card>
        </div>
      </main>
    </div>
  )
}
