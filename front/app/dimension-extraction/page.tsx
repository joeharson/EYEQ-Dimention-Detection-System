"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Eye, CheckCircle2, Ruler, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api"

export default function DimensionExtractionPage() {
  const router = useRouter()
  const [fileName, setFileName] = useState("")
  const [fileType, setFileType] = useState("")
  const [isExtracting, setIsExtracting] = useState(true)
  const [dimensions, setDimensions] = useState<Record<string, number>>({})
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const file = sessionStorage.getItem("uploadedFile") || ""
    const type = sessionStorage.getItem("fileType") || ""
    const filePath = sessionStorage.getItem("filePath") || ""
    setFileName(file)
    setFileType(type)

    // Extract CAD dimensions from backend
    const extractDimensions = async () => {
      try {
        setIsExtracting(true)
        const filePath = sessionStorage.getItem("filePath")
        
        if (!filePath) {
          setError("No file path found. Please upload a file first.")
          setIsExtracting(false)
          return
        }
        
        // Trigger CAD extraction via API
        try {
          const extractResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/extract-cad`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ cad_file_path: filePath }),
          })
          
          if (!extractResponse.ok) {
            throw new Error("Failed to trigger CAD extraction")
          }
        } catch (err) {
          console.error("Extraction trigger error:", err)
          // Continue to poll anyway
        }
        
        // Poll for CAD dimensions after extraction
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        const maxAttempts = 15
        let attempts = 0
        
        while (attempts < maxAttempts) {
          try {
            const response = await apiClient.getCADDimensions()
            if (response.dimensions && Object.keys(response.dimensions).length > 0) {
              setDimensions(response.dimensions)
              setIsExtracting(false)
              return
            }
          } catch (err) {
            // Dimensions not ready yet, continue polling
          }
          
          await new Promise(resolve => setTimeout(resolve, 1000))
          attempts++
        }
        
        // If extraction takes too long, show error
        setError("CAD extraction timed out. Please try again.")
        setIsExtracting(false)
      } catch (err) {
        console.error("Extraction error:", err)
        setError(err instanceof Error ? err.message : "Failed to extract dimensions")
        setIsExtracting(false)
      }
    }

    extractDimensions()
  }, [])

  const handleContinue = () => {
    // Store dimensions for comparison
    sessionStorage.setItem("cadDimensions", JSON.stringify(dimensions))
    router.push("/inspection")
  }

  const formatDimension = (key: string, value: number): string => {
    return `${value.toFixed(2)} mm`
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
            <Button variant="outline" onClick={() => router.push("/upload-cad")}>
              Back
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Progress indicator */}
        <div className="mb-12">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div className="flex-1 h-1 bg-primary" />
            <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div className="flex-1 h-1 bg-primary" />
            <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold">
              3
            </div>
            <div className="flex-1 h-1 bg-muted" />
            <div className="w-8 h-8 rounded-full bg-muted text-muted-foreground flex items-center justify-center text-sm font-semibold">
              4
            </div>
          </div>
          <div className="text-sm text-muted-foreground">
            Step 3 of 4: <span className="text-foreground font-medium">CAD Dimension Extraction</span>
          </div>
        </div>

        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-foreground mb-4">CAD Dimension Extraction</h1>
          {isExtracting ? (
            <p className="text-lg text-muted-foreground">Analyzing CAD file and extracting dimensions...</p>
          ) : (
            <p className="text-lg text-muted-foreground">Dimensions successfully extracted from CAD file</p>
          )}
        </div>

        {isExtracting ? (
          <div className="max-w-2xl mx-auto">
            <Card className="p-12">
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                <p className="text-foreground font-medium">Processing {fileName}...</p>
                <Badge variant="secondary">{fileType.toUpperCase()}</Badge>
              </div>
            </Card>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* CAD Preview Panel */}
            <Card className="lg:col-span-2 p-6">
              <h3 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
                <Ruler className="w-5 h-5" />
                CAD Preview
              </h3>
              <div className="aspect-video bg-muted rounded-lg flex items-center justify-center border-2 border-dashed border-border">
                <div className="text-center">
                  <div className="w-24 h-24 mx-auto mb-4 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Ruler className="w-12 h-12 text-primary" />
                  </div>
                  <p className="text-muted-foreground">CAD Model Preview</p>
                  <p className="text-sm text-muted-foreground mt-2">{fileName}</p>
                </div>
              </div>
            </Card>

            {/* Extracted Dimensions */}
            <Card className="p-6">
              <h3 className="text-xl font-semibold text-foreground mb-4">Extracted Dimensions</h3>
              {error ? (
                <div className="p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-destructive">
                  {error}
                </div>
              ) : (
                <div className="space-y-4">
                  {Object.entries(dimensions).map(([key, value]) => (
                    <div key={key} className="p-4 bg-muted/30 rounded-lg">
                      <p className="text-sm text-muted-foreground mb-1 capitalize">
                        {key.replace(/_/g, " ")}
                      </p>
                      <p className="text-2xl font-bold text-foreground">{formatDimension(key, value)}</p>
                    </div>
                  ))}

                  {Object.keys(dimensions).length === 0 && !isExtracting && (
                    <div className="p-4 bg-muted/30 rounded-lg text-center text-muted-foreground">
                      No dimensions extracted
                    </div>
                  )}

                  <div className="p-4 bg-accent/10 rounded-lg border border-accent/30">
                    <p className="text-sm text-muted-foreground mb-1">Tolerance Range</p>
                    <p className="text-xl font-bold text-accent">± 2.0 mm</p>
                  </div>

                  <Button 
                    className="w-full gap-2" 
                    size="lg" 
                    onClick={handleContinue}
                    disabled={Object.keys(dimensions).length === 0}
                  >
                    Start Inspection
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </div>
              )}
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
