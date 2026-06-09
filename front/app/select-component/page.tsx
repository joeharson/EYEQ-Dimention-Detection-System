"use client"

import { useRouter } from "next/navigation"
import { Eye, Circle, Hexagon, Square, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

const components = [
  {
    id: "ball-bearing",
    name: "Ball Bearing",
    icon: Circle,
    description: "Spherical rolling element bearings",
    color: "text-primary",
    bgColor: "bg-primary/10",
  },
  {
    id: "nut",
    name: "Nut",
    icon: Hexagon,
    description: "Hexagonal threaded fasteners",
    color: "text-secondary",
    bgColor: "bg-secondary/10",
  },
  {
    id: "washer",
    name: "Washer",
    icon: Circle,
    description: "Circular thin plates with holes",
    color: "text-accent",
    bgColor: "bg-accent/10",
  },
  {
    id: "square-washer",
    name: "Square Washer",
    icon: Square,
    description: "Square thin plates with holes",
    color: "text-chart-2",
    bgColor: "bg-chart-2/10",
  },
]

export default function SelectComponentPage() {
  const router = useRouter()

  const handleSelectComponent = (componentId: string) => {
    // Store selection in sessionStorage for use in next steps
    sessionStorage.setItem("selectedComponent", componentId)
    router.push("/upload-cad")
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-md bg-primary flex items-center justify-center">
                <Eye className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-semibold text-foreground">EyeQ</span>
            </div>
            <Button variant="outline" onClick={() => router.push("/welcome")}>
              Back
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Progress indicator */}
        <div className="mb-12">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold">
              1
            </div>
            <div className="flex-1 h-1 bg-muted" />
            <div className="w-8 h-8 rounded-full bg-muted text-muted-foreground flex items-center justify-center text-sm font-semibold">
              2
            </div>
            <div className="flex-1 h-1 bg-muted" />
            <div className="w-8 h-8 rounded-full bg-muted text-muted-foreground flex items-center justify-center text-sm font-semibold">
              3
            </div>
            <div className="flex-1 h-1 bg-muted" />
            <div className="w-8 h-8 rounded-full bg-muted text-muted-foreground flex items-center justify-center text-sm font-semibold">
              4
            </div>
          </div>
          <div className="text-sm text-muted-foreground">
            Step 1 of 4: <span className="text-foreground font-medium">Select Component Type</span>
          </div>
        </div>

        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-foreground mb-4">Select Component Type</h1>
          <p className="text-lg text-muted-foreground">Choose the type of component you want to inspect</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {components.map((component) => {
            const Icon = component.icon
            return (
              <Card
                key={component.id}
                className="p-8 hover:shadow-xl transition-all cursor-pointer hover:border-primary"
                onClick={() => handleSelectComponent(component.id)}
              >
                <div className="flex items-start gap-6">
                  <div
                    className={`w-16 h-16 rounded-lg ${component.bgColor} flex items-center justify-center flex-shrink-0`}
                  >
                    <Icon className={`w-8 h-8 ${component.color}`} />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-semibold text-card-foreground mb-2">{component.name}</h3>
                    <p className="text-muted-foreground mb-4">{component.description}</p>
                    <div className={`flex items-center gap-2 ${component.color} font-medium`}>
                      Select & Continue
                      <ArrowRight className="w-4 h-4" />
                    </div>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}
