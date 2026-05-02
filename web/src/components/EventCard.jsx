import React from 'react';
import { MapPin, Calendar, Clock, Ticket } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

export default function EventCard({ event }) {
  // Get the next upcoming session or the first one if all are past
  const sessions = [...event.sessions].sort((a, b) => new Date(a.date) - new Date(b.date));
  
  return (
    <div className="glass-card">
      {event.image_url && (
        <img 
          src={event.image_url} 
          alt={event.title} 
          className="event-image" 
          loading="lazy" 
          referrerPolicy="no-referrer"
        />
      )}
      <div className="tag">{event.type}</div>
      <h3 className="event-title">{event.title}</h3>
      <p className="subtitle" style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>{event.company}</p>
      
      <div className="event-venue">
        <MapPin size={16} />
        <span>{event.venue.name}, {event.venue.municipality}</span>
      </div>
      
      <div style={{ marginTop: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
          <Calendar size={16} />
          <span style={{ fontSize: '0.9rem' }}>Sesiones: {sessions.length}</span>
        </div>
        
        <div className="sessions-list" style={{ maxHeight: '100px', overflowY: 'auto', paddingRight: '0.5rem' }}>
          {sessions.map((session, idx) => (
             <div key={idx} className="event-dates" style={{ display: 'flex', justifyContent: 'space-between', padding: '0.25rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span>{format(parseISO(session.date), "d 'de' MMMM 'de' yyyy", { locale: es })}</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                   <Clock size={12} /> {session.time}
                </span>
             </div>
          ))}
        </div>
      </div>
      
      <div className="event-price" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
           <Ticket size={16} /> {event.price_range}
        </span>
        <a href={event.url} target="_blank" rel="noopener noreferrer" style={{
            background: 'var(--accent-primary)',
            color: 'white',
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            textDecoration: 'none',
            fontSize: '0.9rem',
            fontWeight: '500'
        }}>
           Saber más
        </a>
      </div>
    </div>
  );
}
