"use client"

import Link from "next/link"
import { Eye } from "lucide-react"
import { Button } from "@/components/ui/button"

export function Navigation() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-md bg-primary flex items-center justify-center">
              <Eye className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-semibold text-foreground">EyeQ</span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <Link href="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Home
            </Link>
            <Link href="/dxf" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              DXF Analysis
            </Link>
            <Link href="/inspection" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Inspection
            </Link>
            <Link
              href="/intelligence"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Intelligence
            </Link>
            <Link href="/dashboard" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Dashboard
            </Link>
          </div>

          <Button className="hidden md:inline-flex">Get Started</Button>
        </div>
      </div>
    </nav>
  )
}
