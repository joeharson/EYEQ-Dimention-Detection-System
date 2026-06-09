"use client"

import { Navigation } from "@/components/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Upload, FileText, Ruler, CheckCircle2 } from "lucide-react"
import { useState } from "react"

export default function DXFPage() {
  const [uploaded, setUploaded] = useState(false)

  const handleFileUpload = () => {
    setUploaded(true)
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="pt-24 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-foreground mb-3">DXF Analysis</h1>
            <p className="text-lg text-muted-foreground">
              Upload technical drawings to extract precise dimensions and tolerances
            </p>
          </div>

          {!uploaded ? (
            <Card className="p-8 bg-card">
              <div className="max-w-2xl mx-auto">
                <div className="border-2 border-dashed border-border rounded-lg p-12 text-center hover:border-primary transition-colors cursor-pointer">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 text-primary mb-4">
                    <Upload className="w-8 h-8" />
                  </div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">Upload DXF File</h3>
                  <p className="text-muted-foreground mb-6">Drag and drop your technical drawing or click to browse</p>
                  <Input type="file" accept=".dxf" className="hidden" id="dxf-upload" onChange={handleFileUpload} />
                  <Label htmlFor="dxf-upload">
                    <Button type="button" onClick={() => document.getElementById("dxf-upload")?.click()}>
                      Select DXF File
                    </Button>
                  </Label>
                </div>

                <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium text-foreground text-sm">AutoCAD Compatible</div>
                      <div className="text-xs text-muted-foreground">Supports all standard DXF formats</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium text-foreground text-sm">Auto-Extract</div>
                      <div className="text-xs text-muted-foreground">Instant dimension detection</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium text-foreground text-sm">Tolerance Analysis</div>
                      <div className="text-xs text-muted-foreground">Automatic tolerance parsing</div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* DXF Preview */}
              <Card className="p-6 bg-card">
                <div className="flex items-center gap-2 mb-4">
                  <FileText className="w-5 h-5 text-primary" />
                  <h2 className="text-xl font-semibold text-card-foreground">Technical Drawing</h2>
                </div>

                <div className="aspect-square bg-muted rounded-lg flex items-center justify-center relative overflow-hidden blueprint-grid-fine">
                  {/* DXF visualization - Washer example */}
                  <svg
                    className="w-3/4 h-3/4"
                    viewBox="0 0 200 200"
                    xmlns="http://www.w3.org/2000/svg"
                    stroke="currentColor"
                    fill="none"
                    strokeWidth="2"
                  >
                    {/* Main washer outline */}
                    <circle cx="100" cy="100" r="70" className="text-foreground" />
                    <circle cx="100" cy="100" r="30" className="text-foreground" />

                    {/* Dimension lines - Outer diameter */}
                    <line x1="100" y1="30" x2="100" y2="20" className="text-muted-foreground" strokeDasharray="2,2" />
                    <line x1="100" y1="170" x2="100" y2="180" className="text-muted-foreground" strokeDasharray="2,2" />
                    <line x1="95" y1="20" x2="95" y2="180" className="text-primary" strokeWidth="1" />
                    <line x1="92" y1="20" x2="98" y2="20" className="text-primary" strokeWidth="1" />
                    <line x1="92" y1="180" x2="98" y2="180" className="text-primary" strokeWidth="1" />
                    <text
                      x="85"
                      y="105"
                      fontSize="12"
                      fill="currentColor"
                      className="text-primary font-mono"
                      transform="rotate(-90 85 105)"
                    >
                      Ø140
                    </text>

                    {/* Dimension lines - Inner diameter */}
                    <line x1="100" y1="70" x2="100" y2="60" className="text-muted-foreground" strokeDasharray="2,2" />
                    <line x1="100" y1="130" x2="100" y2="140" className="text-muted-foreground" strokeDasharray="2,2" />
                    <line x1="110" y1="60" x2="110" y2="140" className="text-secondary" strokeWidth="1" />
                    <line x1="107" y1="60" x2="113" y2="60" className="text-secondary" strokeWidth="1" />
                    <line x1="107" y1="140" x2="113" y2="140" className="text-secondary" strokeWidth="1" />
                    <text
                      x="120"
                      y="105"
                      fontSize="12"
                      fill="currentColor"
                      className="text-secondary font-mono"
                      transform="rotate(-90 120 105)"
                    >
                      Ø60
                    </text>

                    {/* Center marks */}
                    <line x1="95" y1="100" x2="105" y2="100" className="text-accent" strokeWidth="1" />
                    <line x1="100" y1="95" x2="100" y2="105" className="text-accent" strokeWidth="1" />
                  </svg>

                  <div className="absolute top-3 right-3 px-3 py-1 bg-primary/10 text-primary text-xs font-medium rounded">
                    washer_m8.dxf
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">Last modified: 2 hours ago</div>
                  <Button variant="outline" size="sm">
                    Replace File
                  </Button>
                </div>
              </Card>

              {/* Extracted Dimensions */}
              <Card className="p-6 bg-card">
                <div className="flex items-center gap-2 mb-4">
                  <Ruler className="w-5 h-5 text-secondary" />
                  <h2 className="text-xl font-semibold text-card-foreground">Extracted Dimensions</h2>
                </div>

                <div className="space-y-4">
                  <div className="p-4 bg-muted/50 rounded-lg border border-border">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-muted-foreground">Outer Diameter</span>
                      <CheckCircle2 className="w-4 h-4 text-primary" />
                    </div>
                    <div className="text-2xl font-bold text-foreground font-mono">140.0 mm</div>
                    <div className="text-xs text-muted-foreground mt-1">Tolerance: ±0.5 mm</div>
                  </div>

                  <div className="p-4 bg-muted/50 rounded-lg border border-border">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-muted-foreground">Inner Diameter</span>
                      <CheckCircle2 className="w-4 h-4 text-primary" />
                    </div>
                    <div className="text-2xl font-bold text-foreground font-mono">60.0 mm</div>
                    <div className="text-xs text-muted-foreground mt-1">Tolerance: ±0.3 mm</div>
                  </div>

                  <div className="p-4 bg-muted/50 rounded-lg border border-border">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-muted-foreground">Thickness</span>
                      <CheckCircle2 className="w-4 h-4 text-primary" />
                    </div>
                    <div className="text-2xl font-bold text-foreground font-mono">5.0 mm</div>
                    <div className="text-xs text-muted-foreground mt-1">Tolerance: ±0.2 mm</div>
                  </div>

                  <div className="p-4 bg-accent/10 rounded-lg border border-accent/30">
                    <div className="flex items-center gap-2 mb-2">
                      <Ruler className="w-4 h-4 text-accent" />
                      <span className="text-sm font-medium text-accent">Quality Grade</span>
                    </div>
                    <div className="text-lg font-semibold text-accent">ISO 8738-1 Class A</div>
                    <div className="text-xs text-muted-foreground mt-1">Precision grade washer standard</div>
                  </div>
                </div>

                <div className="mt-6 pt-6 border-t border-border">
                  <Button className="w-full gap-2">
                    Proceed to Inspection
                    <CheckCircle2 className="w-4 h-4" />
                  </Button>
                </div>
              </Card>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
