# EyeQ Backend API Server

## Setup

1. Install dependencies:
```bash
cd camera
pip install -r requirements.txt
```

2. Start the API server:
```bash
python api_server.py
```

The server will run on `http://localhost:8000`

## API Endpoints

### Health Check
- `GET /` - API information
- `GET /health` - Health check

### CAD File Upload
- `POST /api/upload-cad` - Upload DXF file
  - Body: multipart/form-data with `file` field
  - Returns: `{ success, filename, path, size }`

### Inspection
- `POST /api/start-inspection` - Start inspection process
  - Body: `{ component_type: string, cad_file_path: string }`
  - Returns: `{ success, inspection_id, message }`

- `GET /api/inspection-status/{inspection_id}` - Get inspection status
  - Returns: `{ status, step, message, results, cad_dimensions, live_measurement }`

- `POST /api/stop-inspection/{inspection_id}` - Stop active inspection

### Measurements
- `GET /api/live-measurement` - Get current live measurement
- `GET /api/cad-dimensions` - Get extracted CAD dimensions
- `GET /api/comparison-report` - Get latest comparison report

### Dashboard
- `GET /api/dashboard-stats` - Get dashboard statistics
- `GET /api/recent-inspections?limit=10` - Get recent inspection results

## Integration with Frontend

The frontend is configured to connect to `http://localhost:8000` by default. Update `NEXT_PUBLIC_API_URL` in the frontend `.env` file if needed.

## Workflow

1. Upload CAD file → `/api/upload-cad`
2. Start inspection → `/api/start-inspection`
3. Poll status → `/api/inspection-status/{id}` (every 1 second)
4. Get results → `/api/comparison-report`

