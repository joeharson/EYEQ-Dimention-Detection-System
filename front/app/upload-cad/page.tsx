"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Eye, Upload, File, CheckCircle2, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"

export default function UploadCADPage() {
  const router = useRouter()
  const [selectedComponent, setSelectedComponent] = useState("")
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  useEffect(() => {
    const component = sessionStorage.getItem("selectedComponent") || ""
    setSelectedComponent(component)
  }, [])

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadedFile(file)
    }
  }

  const handleContinue = async () => {
    if (!uploadedFile) return

    setIsProcessing(true)
    try {
      // Upload file to backend
      const { apiClient } = await import("@/lib/api")
      const response = await apiClient.uploadCADFile(uploadedFile)

      // Store file info in sessionStorage
      sessionStorage.setItem("uploadedFile", uploadedFile.name)
      sessionStorage.setItem("filePath", response.path)
      sessionStorage.setItem("fileType", uploadedFile.name.split(".").pop() || "")

      router.push("/dimension-extraction")
    } catch (error) {
      console.error("Upload failed:", error)
      alert(`Upload failed: ${error instanceof Error ? error.message : "Unknown error"}`)
    } finally {
      setIsProcessing(false)
    }
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
            <Button variant="outline" onClick={() => router.push("/select-component")}>
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
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div className="flex-1 h-1 bg-primary" />
            <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold">
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
            Step 2 of 4: <span className="text-foreground font-medium">Upload CAD File</span>
          </div>
        </div>

        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-foreground mb-4">Upload CAD File</h1>
          <p className="text-lg text-muted-foreground">
            Selected Component:{" "}
            <span className="text-foreground font-medium capitalize">{selectedComponent.replace("-", " ")}</span>
          </p>
        </div>

        <div className="max-w-2xl mx-auto">
          <Card className="p-8">
            <div className="space-y-6">
              <div>
                <Label htmlFor="cad-upload" className="text-base mb-3 block">
                  Select DXF or STL File
                </Label>
                <div className="border-2 border-dashed border-border rounded-lg p-8 hover:border-primary transition-colors cursor-pointer">
                  <input
                    id="cad-upload"
                    type="file"
                    accept=".dxf,.stl"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <label htmlFor="cad-upload" className="flex flex-col items-center cursor-pointer">
                    <Upload className="w-12 h-12 text-muted-foreground mb-4" />
                    <p className="text-foreground font-medium mb-2">Click to upload or drag and drop</p>
                    <p className="text-sm text-muted-foreground">DXF or STL files only</p>
                  </label>
                </div>
              </div>

              {uploadedFile && (
                <Card className="p-4 bg-muted/30">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                      <File className="w-6 h-6 text-primary" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-foreground">{uploadedFile.name}</p>
                      <p className="text-sm text-muted-foreground">{(uploadedFile.size / 1024).toFixed(2)} KB</p>
                    </div>
                    <Badge variant="secondary">{uploadedFile.name.split(".").pop()?.toUpperCase()}</Badge>
                  </div>
                </Card>
              )}

              <Button
                className="w-full gap-2"
                size="lg"
                onClick={handleContinue}
                disabled={!uploadedFile || isProcessing}
              >
                {isProcessing ? "Processing..." : "Continue to Dimension Extraction"}
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
