import { MapContainer, Marker, Popup, TileLayer, CircleMarker } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Link } from 'react-router-dom'
import { SEVERITY_META, categoryLabel, formatDateTime } from '../constants'
import { SeverityBadge, StatusBadge } from './Badges'

const DEFAULT_CENTER = [-33.96, 25.6]

// Default Leaflet marker icons break under bundlers; use a simple div icon instead.
const pinIcon = (color) =>
  L.divIcon({
    className: '',
    html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 0 0 1px rgba(0,0,0,.3)"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  })

export default function IncidentMap({ incidents = [], selectedId, onSelect, height = 'h-[480px]' }) {
  const withCoords = incidents.filter((i) => i.latitude != null && i.longitude != null)
  const bounds = withCoords.length
    ? L.latLngBounds(withCoords.map((i) => [i.latitude, i.longitude])).pad(0.2)
    : null

  return (
    <div className={`overflow-hidden rounded-xl border border-slate-200 ${height}`}>
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={12}
        scrollWheelZoom
        className="h-full w-full"
        bounds={bounds || undefined}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {withCoords.map((incident) => {
          const color = SEVERITY_META[incident.severity]?.color || '#64748b'
          const isSelected = incident.incidentId === selectedId
          return (
            <span key={incident.incidentId}>
              <CircleMarker
                center={[incident.latitude, incident.longitude]}
                radius={isSelected ? 12 : 8}
                pathOptions={{
                  color: '#ffffff',
                  weight: isSelected ? 3 : 1.5,
                  fillColor: color,
                  fillOpacity: 0.9,
                }}
                eventHandlers={{ click: () => onSelect?.(incident) }}
              />
              <Marker
                position={[incident.latitude, incident.longitude]}
                icon={pinIcon(color)}
                eventHandlers={{ click: () => onSelect?.(incident) }}
              />
            </span>
          )
        })}
        {withCoords
          .filter((i) => i.incidentId === selectedId)
          .map((i) => (
            <Popup key={`pop-${i.incidentId}`} position={[i.latitude, i.longitude]}>
              <div style={{ minWidth: 200, fontFamily: 'system-ui, sans-serif' }}>
                <strong style={{ fontSize: 14 }}>🚨 {categoryLabel(i.category)}</strong>
                <p style={{ margin: '6px 0', fontSize: 12, color: '#475569' }}>{i.area}</p>
                <p style={{ margin: '6px 0', fontSize: 12, color: '#475569' }}>
                  Reported: {formatDateTime(i.createdAt)}
                </p>
                <div style={{ display: 'flex', gap: 6, margin: '6px 0' }}>
                  <SeverityBadge severity={i.severity} />
                  <StatusBadge status={i.status} />
                </div>
                <Link
                  to={`/incidents/${i.incidentId}`}
                  style={{ fontSize: 12, color: '#dc2626', fontWeight: 600 }}
                >
                  View details →
                </Link>
              </div>
            </Popup>
          ))}
      </MapContainer>
    </div>
  )
}
