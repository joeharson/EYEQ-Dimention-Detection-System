"""
FastAPI server for EyeQ inspection system
Provides REST API endpoints for frontend integration
"""
import os
import sys
import subprocess
import threading
import time
import json
from pathlib import Path
from typing import Optional, Dict, List
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import pandas as pd
import uvicorn

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="EyeQ Inspection API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
BASE_DIR = Path(__file__).parent
CAD_INPUT_DIR = BASE_DIR / "cad_inputs"
CAD_INPUT_DIR.mkdir(exist_ok=True)

# Global state
inspection_status: Dict[str, any] = {}
active_inspections: Dict[str, subprocess.Popen] = {}

# Pydantic models
class InspectionRequest(BaseModel):
    component_type: str
    cad_file_path: str

class InspectionStatus(BaseModel):
    status: str
    message: str
    data: Optional[Dict] = None

class MeasurementUpdate(BaseModel):
    timestamp: float
    measurements: Dict[str, float]
    status: str

# Helper functions
def get_cad_dimensions() -> Dict:
    """Load CAD dimensions from CSV"""
    cad_file = BASE_DIR / "dxf_measurements.csv"
    if not cad_file.exists():
        return {}
    
    df = pd.read_csv(cad_file)
    dimensions = {}
    for _, row in df.iterrows():
        dim_type = str(row["type"]).strip().lower()
        value = row.get("value_mm") or row.get("diameter_mm", 0)
        dimensions[dim_type] = float(value)
    return dimensions

def get_live_measurement() -> Optional[str]:
    """Read current measurement from live file"""
    live_file = BASE_DIR / "current_measurement.txt"
    if live_file.exists():
        return live_file.read_text()
    return None

def get_comparison_report() -> Optional[Dict]:
    """Load comparison report"""
    report_file = BASE_DIR / "component_comparison_report.csv"
    if not report_file.exists():
        return None
    
    df = pd.read_csv(report_file)
    if df.empty:
        return None
    
    # Get latest result
    latest = df.iloc[-1].to_dict()
    return latest

def run_inspection_pipeline(cad_file_path: str, inspection_id: str):
    """Run the inspection pipeline in background"""
    try:
        inspection_status[inspection_id] = {
            "status": "running",
            "step": "extracting_cad",
            "message": "Extracting CAD dimensions..."
        }
        
        # Step 1: Extract CAD dimensions
        if cad_file_path.lower().endswith(".dxf"):
            subprocess.run(
                ["python", str(BASE_DIR / "cad" / "cad_extractor.py"), cad_file_path],
                check=True,
                cwd=str(BASE_DIR)
            )
        else:
            raise ValueError("Only DXF files supported")
        
        inspection_status[inspection_id]["step"] = "identifying_component"
        inspection_status[inspection_id]["message"] = "Identifying component type..."
        
        # Step 2: Identify component type
        cad_output = BASE_DIR / "dxf_measurements.csv"
        if not cad_output.exists():
            raise FileNotFoundError("CAD extraction failed")
        
        cad_df = pd.read_csv(cad_output)
        types = cad_df["type"].astype(str).str.lower().tolist()
        
        if "outer_diameter" in types and "inner_diameter" in types:
            part = "bearing"
        elif "outer_width" in types and "inner_diameter" in types:
            part = "square_washer"
        elif "across_flats" in types:
            part = "hex_nut"
        else:
            part = "washer"
        
        inspection_status[inspection_id]["step"] = "camera_inspection"
        inspection_status[inspection_id]["message"] = "Starting camera inspection..."
        inspection_status[inspection_id]["component_type"] = part
        
        # Step 3: Run vision script
        vision_scripts = {
            "bearing": BASE_DIR / "vision" / "bearing.py",
            "washer": BASE_DIR / "vision" / "washer.py",
            "square_washer": BASE_DIR / "vision" / "square_washer.py",
            "hex_nut": BASE_DIR / "vision" / "nut.py"
        }
        
        script_path = vision_scripts.get(part)
        if not script_path or not script_path.exists():
            raise FileNotFoundError(f"Vision script not found for {part}")
        
        # Run vision script (non-blocking)
        # Note: On Windows, CREATE_NEW_CONSOLE opens a new window
        # On Linux/Mac, we run in background
        if sys.platform == "win32":
            process = subprocess.Popen(
                ["python", str(script_path)],
                cwd=str(BASE_DIR),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            process = subprocess.Popen(
                ["python", str(script_path)],
                cwd=str(BASE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        active_inspections[inspection_id] = process
        
        # Wait for process to complete (or timeout)
        try:
            process.wait(timeout=300)  # 5 minute timeout
        except subprocess.TimeoutExpired:
            process.terminate()
            raise subprocess.TimeoutExpired(process.args, 300)
        
        inspection_status[inspection_id]["step"] = "comparing"
        inspection_status[inspection_id]["message"] = "Comparing CAD and measured dimensions..."
        
        # Step 4: Compare results
        subprocess.run(
            ["python", str(BASE_DIR / "comparison" / "compare_results.py")],
            check=True,
            cwd=str(BASE_DIR)
        )
        
        # Get final results
        report = get_comparison_report()
        cad_dims = get_cad_dimensions()
        
        inspection_status[inspection_id] = {
            "status": "completed",
            "step": "completed",
            "message": "Inspection completed successfully",
            "results": report,
            "cad_dimensions": cad_dims
        }
        
    except subprocess.TimeoutExpired:
        inspection_status[inspection_id] = {
            "status": "error",
            "message": "Inspection timeout - camera window may need to be closed manually"
        }
    except Exception as e:
        inspection_status[inspection_id] = {
            "status": "error",
            "message": f"Inspection failed: {str(e)}"
        }
    finally:
        if inspection_id in active_inspections:
            del active_inspections[inspection_id]

# API Endpoints
@app.get("/")
async def root():
    return {"message": "EyeQ Inspection API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/upload-cad")
async def upload_cad_file(file: UploadFile = File(...)):
    """Upload CAD file (DXF)"""
    if not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="Only DXF files are supported")
    
    # Save file
    file_path = CAD_INPUT_DIR / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {
        "success": True,
        "filename": file.filename,
        "path": str(file_path),
        "size": len(content)
    }

@app.post("/api/start-inspection")
async def start_inspection(request: InspectionRequest, background_tasks: BackgroundTasks):
    """Start inspection process"""
    cad_file_path = request.cad_file_path
    
    if not os.path.exists(cad_file_path):
        raise HTTPException(status_code=404, detail="CAD file not found")
    
    # Generate inspection ID
    inspection_id = f"insp_{int(time.time())}"
    
    # Start background task
    background_tasks.add_task(run_inspection_pipeline, cad_file_path, inspection_id)
    
    return {
        "success": True,
        "inspection_id": inspection_id,
        "message": "Inspection started"
    }

@app.get("/api/inspection-status/{inspection_id}")
async def get_inspection_status(inspection_id: str):
    """Get inspection status"""
    if inspection_id not in inspection_status:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    status = inspection_status[inspection_id].copy()
    
    # Add live measurement if available
    live_measurement = get_live_measurement()
    if live_measurement:
        status["live_measurement"] = live_measurement
    
    return status

@app.get("/api/live-measurement")
async def get_live_measurement_endpoint():
    """Get current live measurement"""
    measurement = get_live_measurement()
    if not measurement:
        return {"measurement": None}
    
    return {"measurement": measurement}

class ExtractCADRequest(BaseModel):
    cad_file_path: str

@app.post("/api/extract-cad")
async def extract_cad_endpoint(request: ExtractCADRequest):
    """Trigger CAD dimension extraction"""
    cad_file_path = request.cad_file_path
    
    if not os.path.exists(cad_file_path):
        raise HTTPException(status_code=404, detail="CAD file not found")
    
    # Run CAD extraction
    if cad_file_path.lower().endswith(".dxf"):
        subprocess.run(
            ["python", str(BASE_DIR / "cad" / "cad_extractor.py"), cad_file_path],
            check=True,
            cwd=str(BASE_DIR)
        )
    else:
        raise HTTPException(status_code=400, detail="Only DXF files supported")
    
    dimensions = get_cad_dimensions()
    return {"dimensions": dimensions, "success": True}

@app.get("/api/cad-dimensions")
async def get_cad_dimensions_endpoint():
    """Get extracted CAD dimensions"""
    dimensions = get_cad_dimensions()
    return {"dimensions": dimensions}

@app.get("/api/comparison-report")
async def get_comparison_report_endpoint():
    """Get latest comparison report"""
    report = get_comparison_report()
    if not report:
        raise HTTPException(status_code=404, detail="No comparison report available")
    
    return {"report": report}

@app.get("/api/dashboard-stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    report_file = BASE_DIR / "component_comparison_report.csv"
    
    if not report_file.exists():
        return {
            "total_inspections": 0,
            "defective_count": 0,
            "pass_rate": 0,
            "avg_deviation": 0
        }
    
    df = pd.read_csv(report_file)
    
    total = len(df)
    defective = (df["status"] == "DEFECTIVE").sum() if "status" in df.columns else 0
    pass_rate = ((df["status"] == "NOT DEFECTIVE").sum() / total * 100) if total > 0 else 0
    
    # Calculate average deviation
    error_cols = [c for c in df.columns if c.endswith("_abs_err")]
    avg_deviation = 0
    if error_cols:
        avg_deviation = df[error_cols].mean().mean()
    
    return {
        "total_inspections": int(total),
        "defective_count": int(defective),
        "pass_rate": round(pass_rate, 2),
        "avg_deviation": round(avg_deviation, 3)
    }

@app.get("/api/recent-inspections")
async def get_recent_inspections(limit: int = 10):
    """Get recent inspection results"""
    report_file = BASE_DIR / "component_comparison_report.csv"
    
    if not report_file.exists():
        return {"inspections": []}
    
    df = pd.read_csv(report_file)
    df = df.tail(limit)
    
    inspections = []
    for _, row in df.iterrows():
        inspections.append({
            "timestamp": row.get("timestamp", 0),
            "status": row.get("status", "UNKNOWN"),
            "measurements": {k: v for k, v in row.items() if k.startswith("MEAS_")},
            "errors": {k: v for k, v in row.items() if k.endswith("_abs_err")}
        })
    
    return {"inspections": inspections}

@app.post("/api/stop-inspection/{inspection_id}")
async def stop_inspection(inspection_id: str):
    """Stop active inspection"""
    if inspection_id not in active_inspections:
        raise HTTPException(status_code=404, detail="No active inspection found")
    
    process = active_inspections[inspection_id]
    process.terminate()
    
    inspection_status[inspection_id] = {
        "status": "stopped",
        "message": "Inspection stopped by user"
    }
    
    del active_inspections[inspection_id]
    
    return {"success": True, "message": "Inspection stopped"}

if __name__ == "__main__":
    print("Starting EyeQ API Server on http://0.0.0.0:8000")
    print("Press Ctrl+C to stop")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
    except Exception as e:
        print(f"Error starting server: {e}")
        print("Trying port 8001...")
        uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)

