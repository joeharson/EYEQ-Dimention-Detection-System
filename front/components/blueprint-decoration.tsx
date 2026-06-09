export function BlueprintDecoration() {
  return (
    <svg className="absolute inset-0 w-full h-full opacity-30 pointer-events-none" xmlns="http://www.w3.org/2000/svg">
      {/* Washer technical drawing */}
      <g transform="translate(100, 80)" stroke="currentColor" fill="none" strokeWidth="1" opacity="0.4">
        <circle cx="40" cy="40" r="35" />
        <circle cx="40" cy="40" r="15" />
        <line x1="40" y1="5" x2="40" y2="0" strokeDasharray="2,2" />
        <line x1="40" y1="75" x2="40" y2="80" strokeDasharray="2,2" />
        <line x1="5" y1="40" x2="0" y2="40" strokeDasharray="2,2" />
        <line x1="75" y1="40" x2="80" y2="40" strokeDasharray="2,2" />
        <text x="85" y="43" fontSize="8" fill="currentColor">
          Ø35
        </text>
      </g>

      {/* Bolt technical drawing */}
      <g transform="translate(700, 150)" stroke="currentColor" fill="none" strokeWidth="1" opacity="0.3">
        <polygon points="30,10 50,10 52,15 28,15" />
        <rect x="32" y="15" width="16" height="40" />
        <line x1="40" y1="10" x2="40" y2="0" strokeDasharray="2,2" />
        <line x1="40" y1="55" x2="40" y2="65" strokeDasharray="2,2" />
        <text x="55" y="35" fontSize="8" fill="currentColor">
          M8
        </text>
      </g>

      {/* Nut technical drawing */}
      <g transform="translate(150, 400)" stroke="currentColor" fill="none" strokeWidth="1" opacity="0.35">
        <polygon points="40,15 50,25 50,40 40,50 30,40 30,25" />
        <circle cx="40" cy="32.5" r="8" />
        <line x1="40" y1="15" x2="40" y2="5" strokeDasharray="2,2" />
        <text x="55" y="35" fontSize="8" fill="currentColor">
          M10
        </text>
      </g>

      {/* Additional measurement lines */}
      <g transform="translate(600, 400)" stroke="currentColor" strokeWidth="0.5" opacity="0.25">
        <line x1="0" y1="20" x2="80" y2="20" strokeDasharray="3,3" />
        <line x1="0" y1="20" x2="0" y2="15" />
        <line x1="80" y1="20" x2="80" y2="15" />
        <text x="30" y="15" fontSize="7" fill="currentColor">
          80mm
        </text>
      </g>
    </svg>
  )
}
