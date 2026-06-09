"use client"

import { useRouter } from "next/navigation"
import { Eye, ArrowRight, Package } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

export default function WelcomePage() {
  const router = useRouter()

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
            <Button variant="outline" onClick={() => router.push("/")}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-lg bg-primary/10 mb-6">
            <Eye className="w-10 h-10 text-primary" />
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-foreground mb-4">
            Welcome to EyeQ – Intelligent Visual Inspection System
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Precision quality control powered by advanced computer vision
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          <Card
            className="p-8 hover:shadow-lg transition-all cursor-pointer"
            onClick={() => router.push("/select-component")}
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Package className="w-6 h-6 text-primary" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-card-foreground mb-2">Start New Inspection</h3>
                <p className="text-muted-foreground mb-4">
                  Begin the inspection workflow by selecting a component type
                </p>
                <div className="flex items-center gap-2 text-primary font-medium">
                  Select Component
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            </div>
          </Card>

          <Card className="p-8 hover:shadow-lg transition-all cursor-pointer" onClick={() => router.push("/dashboard")}>
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-secondary/10 flex items-center justify-center flex-shrink-0">
                <Eye className="w-6 h-6 text-secondary" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-card-foreground mb-2">View Dashboard</h3>
                <p className="text-muted-foreground mb-4">Access analytics, KPIs, and inspection history</p>
                <div className="flex items-center gap-2 text-secondary font-medium">
                  Open Dashboard
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            </div>
          </Card>
        </div>

        <div className="mt-12 text-center">
          <p className="text-sm text-muted-foreground">
            System Status: <span className="text-green-500 font-medium">Online</span>
          </p>
        </div>
      </div>
    </div>
  )
}
