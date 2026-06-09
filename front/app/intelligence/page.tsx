"use client"

import { Navigation } from "@/components/navigation"
import { Card } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Factory, Plane, AlertCircle, TrendingUp, Package } from "lucide-react"

export default function IntelligencePage() {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="pt-24 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-foreground mb-3">Industry Intelligence</h1>
            <p className="text-lg text-muted-foreground">
              Sector-specific defect patterns and quality insights for Automotive and Aerospace
            </p>
          </div>

          <Tabs defaultValue="automotive" className="w-full">
            <TabsList className="grid w-full max-w-md grid-cols-2 mb-8">
              <TabsTrigger value="automotive" className="gap-2">
                <Factory className="w-4 h-4" />
                Automotive
              </TabsTrigger>
              <TabsTrigger value="aerospace" className="gap-2">
                <Plane className="w-4 h-4" />
                Aerospace
              </TabsTrigger>
            </TabsList>

            <TabsContent value="automotive" className="space-y-6">
              <Card className="p-6 bg-card">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Factory className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-semibold text-card-foreground">Automotive Industry</h2>
                    <p className="text-sm text-muted-foreground">High-volume production quality standards</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                  <div className="p-4 bg-muted/50 rounded-lg border border-border">
                    <div className="text-3xl font-bold text-foreground mb-1">2,847</div>
                    <div className="text-sm text-muted-foreground">Components Inspected</div>
                    <div className="text-xs text-primary mt-1">↑ 12% this month</div>
                  </div>
                  <div className="p-4 bg-muted/50 rounded-lg border border-border">
                    <div className="text-3xl font-bold text-foreground mb-1">94.2%</div>
                    <div className="text-sm text-muted-foreground">Pass Rate</div>
                    <div className="text-xs text-primary mt-1">↑ 2.1% improvement</div>
                  </div>
                  <div className="p-4 bg-muted/50 rounded-lg border border-border">
                    <div className="text-3xl font-bold text-foreground mb-1">3</div>
                    <div className="text-sm text-muted-foreground">Critical Defect Types</div>
                    <div className="text-xs text-muted-foreground mt-1">Most common issues</div>
                  </div>
                </div>

                <h3 className="text-lg font-semibold text-foreground mb-4">Common Defects by Component Type</h3>

                <div className="space-y-4">
                  <Card className="p-5 bg-muted/30 border-border">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <Package className="w-5 h-5 text-secondary" />
                        <div>
                          <h4 className="font-semibold text-foreground">Washers</h4>
                          <p className="text-sm text-muted-foreground">Flat washers, spring washers, lock washers</p>
                        </div>
                      </div>
                      <Badge className="bg-secondary/20 text-secondary hover:bg-secondary/20">432 inspected</Badge>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Dimensional deviation</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">42% of defects</div>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Surface irregularities</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">28% of defects</div>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Material defects</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">18% of defects</div>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-5 bg-muted/30 border-border">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <Package className="w-5 h-5 text-secondary" />
                        <div>
                          <h4 className="font-semibold text-foreground">Bolts & Screws</h4>
                          <p className="text-sm text-muted-foreground">Hex bolts, socket head cap screws</p>
                        </div>
                      </div>
                      <Badge className="bg-secondary/20 text-secondary hover:bg-secondary/20">587 inspected</Badge>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Thread pitch errors</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">38% of defects</div>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Head dimension issues</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">32% of defects</div>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Shank diameter variation</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">20% of defects</div>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-5 bg-muted/30 border-border">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <Package className="w-5 h-5 text-secondary" />
                        <div>
                          <h4 className="font-semibold text-foreground">Nuts</h4>
                          <p className="text-sm text-muted-foreground">Hex nuts, lock nuts, flange nuts</p>
                        </div>
                      </div>
                      <Badge className="bg-secondary/20 text-secondary hover:bg-secondary/20">341 inspected</Badge>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Thread damage</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">45% of defects</div>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Hex dimension errors</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">30% of defects</div>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Thickness out of spec</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">15% of defects</div>
                      </div>
                    </div>
                  </Card>
                </div>
              </Card>

              <Card className="p-6 bg-accent/10 border-accent/30">
                <div className="flex items-center gap-3 mb-4">
                  <TrendingUp className="w-5 h-5 text-accent" />
                  <h3 className="text-lg font-semibold text-foreground">Industry Insights</h3>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  Automotive fasteners require strict adherence to DIN and ISO standards. Most common failures occur
                  during high-speed manufacturing processes where tool wear causes dimensional drift. Regular
                  calibration and real-time monitoring significantly reduce defect rates.
                </p>
              </Card>
            </TabsContent>

            <TabsContent value="aerospace" className="space-y-6">
              <Card className="p-6 bg-card">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 rounded-lg bg-secondary/10 flex items-center justify-center">
                    <Plane className="w-6 h-6 text-secondary" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-semibold text-card-foreground">Aerospace Industry</h2>
                    <p className="text-sm text-muted-foreground">Critical safety and precision requirements</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                  <div className="p-4 bg-muted/50 rounded-lg border border-border">
                    <div className="text-3xl font-bold text-foreground mb-1">1,243</div>
                    <div className="text-sm text-muted-foreground">Components Inspected</div>
                    <div className="text-xs text-primary mt-1">↑ 8% this month</div>
                  </div>
                  <div className="p-4 bg-muted/50 rounded-lg border border-border">
                    <div className="text-3xl font-bold text-foreground mb-1">98.7%</div>
                    <div className="text-sm text-muted-foreground">Pass Rate</div>
                    <div className="text-xs text-primary mt-1">↑ 0.5% improvement</div>
                  </div>
                  <div className="p-4 bg-muted/50 rounded-lg border border-border">
                    <div className="text-3xl font-bold text-foreground mb-1">4</div>
                    <div className="text-sm text-muted-foreground">Critical Defect Types</div>
                    <div className="text-xs text-muted-foreground mt-1">Zero tolerance zones</div>
                  </div>
                </div>

                <h3 className="text-lg font-semibold text-foreground mb-4">Common Defects by Component Type</h3>

                <div className="space-y-4">
                  <Card className="p-5 bg-muted/30 border-border">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <Package className="w-5 h-5 text-secondary" />
                        <div>
                          <h4 className="font-semibold text-foreground">Aerospace Washers</h4>
                          <p className="text-sm text-muted-foreground">High-strength titanium and steel washers</p>
                        </div>
                      </div>
                      <Badge className="bg-secondary/20 text-secondary hover:bg-secondary/20">298 inspected</Badge>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Micro-cracks</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">35% of defects</div>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Precision tolerance violations</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">32% of defects</div>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Surface finish irregularities</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">22% of defects</div>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-5 bg-muted/30 border-border">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <Package className="w-5 h-5 text-secondary" />
                        <div>
                          <h4 className="font-semibold text-foreground">Aerospace Bolts</h4>
                          <p className="text-sm text-muted-foreground">AN, MS, and NAS standard fasteners</p>
                        </div>
                      </div>
                      <Badge className="bg-secondary/20 text-secondary hover:bg-secondary/20">521 inspected</Badge>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Grip length variations</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">40% of defects</div>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Thread class deviations</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">28% of defects</div>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Head marking inconsistencies</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">18% of defects</div>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-5 bg-muted/30 border-border">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <Package className="w-5 h-5 text-secondary" />
                        <div>
                          <h4 className="font-semibold text-foreground">Self-Locking Nuts</h4>
                          <p className="text-sm text-muted-foreground">High-vibration resistant fasteners</p>
                        </div>
                      </div>
                      <Badge className="bg-secondary/20 text-secondary hover:bg-secondary/20">187 inspected</Badge>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Insert integrity issues</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">48% of defects</div>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Torque specification failures</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">28% of defects</div>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-background rounded">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-destructive" />
                          <span className="text-sm text-foreground">Dimensional non-conformance</span>
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">14% of defects</div>
                      </div>
                    </div>
                  </Card>
                </div>
              </Card>

              <Card className="p-6 bg-accent/10 border-accent/30">
                <div className="flex items-center gap-3 mb-4">
                  <TrendingUp className="w-5 h-5 text-accent" />
                  <h3 className="text-lg font-semibold text-foreground">Industry Insights</h3>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  Aerospace fasteners demand extreme precision with tolerances often in micrometers. AS9100
                  certification requires full traceability and 100% inspection. Material integrity is paramount - even
                  microscopic defects can lead to catastrophic failures. Advanced visual inspection combined with
                  non-destructive testing ensures flight safety compliance.
                </p>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  )
}
