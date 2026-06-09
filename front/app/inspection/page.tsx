"use client"

import { Navigation } from "@/components/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Camera, CheckCircle2, XCircle, AlertTriangle, Play, Pause, Loader2 } from "lucide-react"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { apiClient } from "@/lib/api"

export default function InspectionPage() {
  const router = useRouter()
  const [isInspecting, setIsInspecting] = useState(false)
  const [inspectionId, setInspectionId] = useState<string | null>(null)
  const [inspectionStatus, setInspectionStatus] = useState<any>(null)
  const [liveMeasurement, setLiveMeasurement] = useState<string>("")
  const [measurements, setMeasurements] = useState<Record<string, number>>({})
  const [comparisonResult, setComparisonResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Start inspection when page loads
    const startInspection = async () => {
      const filePath = sessionStorage.getItem("filePath")
      const componentType = sessionStorage.getItem("selectedComponent") || "washer"
      
      if (!filePath) {
        setError("No CAD file found. Please upload a file first.")
        return
      }

      try {
        const response = await apiClient.startInspection({
          component_type: componentType,
          cad_file_path: filePath,
        })
        setInspectionId(response.inspection_id)
        setIsInspecting(true)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to start inspection")
      }
    }

    startInspection()
  }, [])

  useEffect(() => {
    if (!inspectionId || !isInspecting) return

    const pollStatus = async () => {
      try {
        const status = await apiClient.getInspectionStatus(inspectionId)
        setInspectionStatus(status)

        if (status.live_measurement) {
          setLiveMeasurement(status.live_measurement)
        }

        if (status.status === "completed") {
          setIsInspecting(false)
          if (status.results) {
            setComparisonResult(status.results)
          }
        } else if (status.status === "error") {
          setIsInspecting(false)
          setError(status.message)
        }
      } catch (err) {
        console.error("Status polling error:", err)
      }
    }

    const interval = setInterval(pollStatus, 1000)
    return () => clearInterval(interval)
  }, [inspectionId, isInspecting])

  useEffect(() => {
    if (!isInspecting) return

    const pollMeasurement = async () => {
      try {
        const response = await apiClient.getLiveMeasurement()
        if (response.measurement) {
          setLiveMeasurement(response.measurement)
        }
      } catch (err) {
        // Ignore errors for live measurement polling
      }
    }

    const interval = setInterval(pollMeasurement, 500)
    return () => clearInterval(interval)
  }, [isInspecting])

  const handleStopInspection = async () => {
    if (inspectionId) {
      try {
        await apiClient.stopInspection(inspectionId)
        setIsInspecting(false)
      } catch (err) {
        console.error("Stop inspection error:", err)
      }
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="pt-24 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-foreground mb-3">Real-Time Inspection</h1>
              <p className="text-lg text-muted-foreground">Live camera feed with AI-powered defect detection</p>
            </div>
            <Button
              size="lg"
              onClick={isInspecting ? handleStopInspection : () => setIsInspecting(true)}
              className="gap-2"
              variant={isInspecting ? "outline" : "default"}
            >
              {isInspecting ? (
                <>
                  <Pause className="w-4 h-4" />
                  Stop Inspection
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Start Inspection
                </>
              )}
            </Button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Live Feed */}
            <div className="lg:col-span-2">
              <Card className="p-6 bg-card">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Camera className="w-5 h-5 text-primary" />
                    <h2 className="text-xl font-semibold text-card-foreground">Live Camera Feed</h2>
                  </div>
                  {isInspecting && (
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-destructive animate-pulse" />
                      <span className="text-sm text-muted-foreground">Recording</span>
                    </div>
                  )}
                </div>

                <div className="aspect-video bg-muted rounded-lg flex items-center justify-center relative overflow-hidden">
                  {isInspecting && !liveMeasurement ? (
                    <div className="flex flex-col items-center gap-4">
                      <Loader2 className="w-8 h-8 animate-spin text-primary" />
                      <p className="text-muted-foreground">{inspectionStatus?.message || "Starting inspection..."}</p>
                    </div>
                  ) : (
                    <>
                      {/* Simulated camera feed with measurement overlays */}
                      <div className="absolute inset-0 bg-gradient-to-br from-muted to-muted/50" />

                  {/* Washer component visualization */}
                  <svg
                    className="w-2/3 h-2/3 relative z-10"
                    viewBox="0 0 200 200"
                    xmlns="http://www.w3.org/2000/svg"
                    stroke="currentColor"
                    fill="none"
                    strokeWidth="3"
                  >
                    <circle cx="100" cy="100" r="65" className="text-foreground" strokeWidth="4" />
                    <circle cx="100" cy="100" r="28" className="text-foreground" strokeWidth="4" />

                    {/* Measurement overlay lines */}
                    <line x1="35" y1="100" x2="20" y2="100" className="text-primary" strokeWidth="2" />
                    <line x1="165" y1="100" x2="180" y2="100" className="text-primary" strokeWidth="2" />
                    <text
                      x="100"
                      y="15"
                      fontSize="10"
                      fill="currentColor"
                      className="text-primary font-mono"
                      textAnchor="middle"
                    >
                      138.7mm
                    </text>

                    {/* Defect indicator */}
                    <circle cx="140" cy="70" r="8" className="text-destructive" fill="currentColor" opacity="0.3" />
                    <circle cx="140" cy="70" r="12" className="text-destructive" strokeWidth="2" />
                  </svg>

                  {/* Camera overlay grid */}
                  <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute top-1/2 left-0 right-0 h-px bg-primary/20" />
                    <div className="absolute left-1/2 top-0 bottom-0 w-px bg-primary/20" />
                    <div className="absolute top-4 left-4 w-3 h-3 border-t-2 border-l-2 border-accent" />
                    <div className="absolute top-4 right-4 w-3 h-3 border-t-2 border-r-2 border-accent" />
                    <div className="absolute bottom-4 left-4 w-3 h-3 border-b-2 border-l-2 border-accent" />
                    <div className="absolute bottom-4 right-4 w-3 h-3 border-b-2 border-r-2 border-accent" />
                  </div>

                  {/* Status overlay */}
                  <div className="absolute top-4 left-4 flex flex-col gap-2">
                    <Badge className="bg-primary/90 text-primary-foreground">
                      {inspectionStatus?.component_type ? `Component: ${inspectionStatus.component_type}` : "Component: Unknown"}
                    </Badge>
                    <Badge className="bg-secondary/90 text-secondary-foreground">
                      {inspectionStatus?.step ? `Step: ${inspectionStatus.step}` : "Initializing..."}
                    </Badge>
                  </div>

                  {/* Live measurement display */}
                  {liveMeasurement && (
                    <div className="absolute bottom-4 left-4 px-3 py-2 bg-background/90 text-foreground rounded-md text-sm font-mono max-w-md">
                      <pre className="whitespace-pre-wrap">{liveMeasurement}</pre>
                    </div>
                  )}

                  {/* Defect alert */}
                  {comparisonResult && comparisonResult.status === "DEFECTIVE" && (
                    <div className="absolute bottom-4 right-4 px-3 py-2 bg-destructive/90 text-destructive-foreground rounded-md text-sm font-medium">
                      Defect Detected
                    </div>
                  )}
                    </>
                  )}
                </div>

                {comparisonResult && (
                  <div className="mt-4 grid grid-cols-3 gap-4">
                    {Object.entries(comparisonResult)
                      .filter(([key]) => key.startsWith("MEAS_"))
                      .slice(0, 3)
                      .map(([key, value]) => (
                        <div key={key} className="text-center p-3 bg-muted/50 rounded-lg">
                          <div className="text-2xl font-bold text-foreground font-mono">
                            {typeof value === "number" ? value.toFixed(2) : value}
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {key.replace("MEAS_", "").replace(/_/g, " ")} (mm)
                          </div>
                        </div>
                      ))}
                  </div>
                )}
              </Card>
            </div>

            {/* Comparison Results */}
            <div className="space-y-6">
              <Card className="p-6 bg-card">
                <h2 className="text-xl font-semibold text-card-foreground mb-4">Inspection Result</h2>

                {error ? (
                  <div className="p-4 bg-destructive/10 border border-destructive/30 rounded-lg mb-4">
                    <div className="font-semibold text-destructive">Error</div>
                    <div className="text-sm text-muted-foreground">{error}</div>
                  </div>
                ) : comparisonResult ? (
                  <>
                    {comparisonResult.status === "DEFECTIVE" ? (
                      <div className="flex items-center gap-3 p-4 bg-destructive/10 border border-destructive/30 rounded-lg mb-4">
                        <XCircle className="w-6 h-6 text-destructive flex-shrink-0" />
                        <div>
                          <div className="font-semibold text-destructive">Defect Found</div>
                          <div className="text-sm text-muted-foreground">Component rejected</div>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center gap-3 p-4 bg-primary/10 border border-primary/30 rounded-lg mb-4">
                        <CheckCircle2 className="w-6 h-6 text-primary flex-shrink-0" />
                        <div>
                          <div className="font-semibold text-primary">Pass</div>
                          <div className="text-sm text-muted-foreground">Component approved</div>
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="p-4 bg-muted/30 rounded-lg mb-4 text-center text-muted-foreground">
                    {isInspecting ? "Inspection in progress..." : "No results yet"}
                  </div>
                )}

                {comparisonResult && (
                  <div className="space-y-3">
                    {Object.entries(comparisonResult)
                      .filter(([key]) => key.endsWith("_abs_err"))
                      .map(([key, error]) => {
                        const dimName = key.replace("_abs_err", "").replace(/_/g, " ")
                        const isPass = error <= 2.0 // 2mm tolerance
                        return (
                          <div key={key} className="flex items-center justify-between p-3 bg-muted/30 rounded">
                            <span className="text-sm text-muted-foreground capitalize">{dimName}</span>
                            <div className="flex items-center gap-2">
                              <Badge
                                variant={isPass ? "default" : "destructive"}
                                className={`gap-1 ${isPass ? "bg-primary/20 text-primary hover:bg-primary/20" : ""}`}
                              >
                                {isPass ? (
                                  <>
                                    <CheckCircle2 className="w-3 h-3" />
                                    Pass
                                  </>
                                ) : (
                                  <>
                                    <XCircle className="w-3 h-3" />
                                    Out of Spec
                                  </>
                                )}
                              </Badge>
                            </div>
                          </div>
                        )
                      })}
                  </div>
                )}
              </Card>

              {comparisonResult && comparisonResult.status === "DEFECTIVE" && (
                <Card className="p-6 bg-card border-destructive/30">
                  <div className="flex items-center gap-2 mb-4">
                    <AlertTriangle className="w-5 h-5 text-destructive" />
                    <h3 className="font-semibold text-card-foreground">Defect Analysis</h3>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <div className="text-sm font-medium text-foreground mb-2">Issue Type</div>
                      <div className="text-sm text-muted-foreground">Dimensional Out of Tolerance</div>
                    </div>

                    {Object.entries(comparisonResult)
                      .filter(([key, value]) => key.endsWith("_abs_err") && value > 2.0)
                      .map(([key, error]) => {
                        const dimName = key.replace("_abs_err", "").replace(/_/g, " ")
                        return (
                          <div key={key}>
                            <div className="text-sm font-medium text-foreground mb-2">Deviation ({dimName})</div>
                            <div className="flex items-baseline gap-2">
                              <span className="text-2xl font-bold text-destructive font-mono">
                                {typeof error === "number" ? `${error.toFixed(2)} mm` : error}
                              </span>
                              <span className="text-sm text-muted-foreground">from spec</span>
                            </div>
                          </div>
                        )
                      })}

                    <div>
                      <div className="text-sm font-medium text-foreground mb-2">Recommendation</div>
                      <div className="text-sm text-muted-foreground leading-relaxed">
                        Reject component. Check machining parameters and tool wear on production line.
                      </div>
                    </div>
                  </div>
                </Card>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
