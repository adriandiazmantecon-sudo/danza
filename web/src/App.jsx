// Version 2.7 - UI Optimizations and Stats
import React, { useState, useEffect } from 'react';
import EventCard from './components/EventCard';
import AdminPanel from './components/AdminPanel';
import { Search, Lock, RefreshCw } from 'lucide-react';
function App() {
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterType, setFilterType] = useState('All');
  const [filterMunicipality, setFilterMunicipality] = useState('All');
  const [filterVenue, setFilterVenue] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('DateAsc');
  const [isFreeOnly, setIsFreeOnly] = useState(false);
  const [showPastEvents, setShowPastEvents] = useState(false);
  const [view, setView] = useState('home'); // 'home' or 'admin'
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(false);
  const [adminPassword, setAdminPassword] = useState('');

  useEffect(() => {
    fetch('/data/events.json')
      .then(res => res.json())
      .then(data => {
        setEvents(data);
        setIsLoading(false);
      })
      .catch(err => {
        console.error("Error loading events:", err);
        setIsLoading(false);
      });
  }, []);

  // Helper to get counts based on current filters
  const getVenueCounts = () => {
    const counts = {};
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    events.forEach(e => {
        const hasFutureSession = e.sessions.some(s => {
          const sessionDate = new Date(s.date);
          sessionDate.setHours(0, 0, 0, 0);
          return sessionDate >= today;
        });
        
        if (showPastEvents || hasFutureSession) {
          counts[e.venue.name] = (counts[e.venue.name] || 0) + 1;
        }
    });
    return counts;
  };

  const fullVenueCounts = {};
  events.forEach(e => {
    fullVenueCounts[e.venue.name] = (fullVenueCounts[e.venue.name] || 0) + 1;
  });

  const venueCounts = getVenueCounts();
  const venues = ['All', ...Object.keys(fullVenueCounts).sort()];
  const totalAbsoluteEventsCount = events.length;
  const totalVenuesCount = venues.length - 1;

  const types = ['All', ...new Set(events.map(e => e.type))].sort();
  const municipalities = ['All', ...new Set(events.map(e => e.venue.municipality))].sort();

  const filteredEvents = events.filter(e => {
    if (filterType !== 'All' && e.type !== filterType) return false;
    if (filterMunicipality !== 'All' && e.venue.municipality !== filterMunicipality) return false;
    if (filterVenue !== 'All' && e.venue.name !== filterVenue) return false;
    if (searchQuery && !e.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    if (isFreeOnly && !e.is_free) return false;

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const hasFutureSession = e.sessions.some(s => {
      const sessionDate = new Date(s.date);
      sessionDate.setHours(0, 0, 0, 0);
      return sessionDate >= today;
    });
    if (!showPastEvents && !hasFutureSession) return false;

    return true;
  });

  const handleAdminLogin = (e) => {
    e.preventDefault();
    // Security: The real password check now happens in the PHP backend.
    // We just allow entry to the UI here.
    if (adminPassword.length > 0) {
      setIsAdminAuthenticated(true);
    } else {
      alert('Por favor, introduce la contraseña');
    }
  };

  const sortedEvents = [...filteredEvents].sort((a, b) => {
    const getFirstDate = (event) => {
      const dates = event.sessions.map(s => new Date(s.date).getTime());
      return dates.length > 0 ? Math.min(...dates) : Infinity;
    };

    if (sortBy === 'DateAsc') return getFirstDate(a) - getFirstDate(b);
    if (sortBy === 'DateDesc') return getFirstDate(b) - getFirstDate(a);

    const parsePrice = (priceStr) => {
       if (!priceStr) return 9999;
       if (priceStr.toLowerCase().includes('gratis') || priceStr.toLowerCase().includes('gratuito')) return 0;
       const match = priceStr.match(/\d+/);
       return match ? parseInt(match[0], 10) : 9999;
    };

    if (sortBy === 'PriceAsc') return parsePrice(a.price_range) - parsePrice(b.price_range);
    if (sortBy === 'PriceDesc') {
       const pa = parsePrice(a.price_range) === 9999 ? -1 : parsePrice(a.price_range);
       const pb = parsePrice(b.price_range) === 9999 ? -1 : parsePrice(b.price_range);
       return pb - pa;
    }
    if (sortBy === 'Venue') return a.venue.name.localeCompare(b.venue.name);
    if (sortBy === 'Municipality') return a.venue.municipality.localeCompare(b.venue.municipality);
    
    return 0;
  });

  return (
    <div className="app-container">
      <header>
        <h1>Danza en Madrid</h1>
        <p className="subtitle">{totalAbsoluteEventsCount} espectáculos de ballet, danza contemporánea, baile y flamenco.</p>
      </header>

      <div className="filters-container">
        <div style={{ position: 'relative', flexGrow: 1, minWidth: '250px' }}>
          <Search size={20} style={{ position: 'absolute', left: '10px', top: '12px', color: 'var(--text-secondary)' }} />
          <input 
            type="text" 
            placeholder="Buscar espectáculos..." 
            style={{ width: '100%', paddingLeft: '2.5rem' }}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
          {types.map(t => <option key={t} value={t}>{t === 'All' ? 'Todos los tipos' : t}</option>)}
        </select>
        
        <select value={filterMunicipality} onChange={(e) => setFilterMunicipality(e.target.value)}>
          {municipalities.map(m => <option key={m} value={m}>{m === 'All' ? 'Todos los municipios' : m}</option>)}
        </select>

        <select value={filterVenue} onChange={(e) => setFilterVenue(e.target.value)}>
          <option value="All">Todos los teatros ({totalVenuesCount})</option>
          {venues.filter(v => v !== 'All').map(v => (
            <option key={v} value={v}>{v}</option>
          ))}
        </select>

        <label className="checkbox-label">
          <input 
            type="checkbox" 
            checked={isFreeOnly} 
            onChange={(e) => setIsFreeOnly(e.target.checked)} 
          />
          Solo gratuitos
        </label>

        <label className="checkbox-label">
          <input 
            type="checkbox" 
            checked={showPastEvents} 
            onChange={(e) => setShowPastEvents(e.target.checked)} 
          />
          Mostrar pasados
        </label>
        
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          <option value="DateAsc">Fecha (Más cercanos)</option>
          <option value="DateDesc">Fecha (Más lejanos)</option>
          <option value="PriceAsc">Precio (Menor a mayor)</option>
          <option value="PriceDesc">Precio (Mayor a menor)</option>
          <option value="Venue">Teatro (A-Z)</option>
          <option value="Municipality">Municipio (A-Z)</option>
        </select>
      </div>

      {view === 'admin' ? (
        !isAdminAuthenticated ? (
          <div className="glass-card" style={{ maxWidth: '400px', margin: '4rem auto', textAlign: 'center' }}>
            <Lock size={48} className="accent-color" style={{ marginBottom: '1rem' }} />
            <h3>Acceso Administrador</h3>
            <form onSubmit={handleAdminLogin} style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <input 
                type="password" 
                placeholder="Contraseña" 
                value={adminPassword}
                onChange={(e) => setAdminPassword(e.target.value)}
                autoFocus
              />
              <button type="submit" className="primary-button" style={{ padding: '0.75rem' }}>Entrar</button>
              <button type="button" onClick={() => setView('home')} className="text-button">Volver al inicio</button>
            </form>
          </div>
        ) : (
          <AdminPanel 
            password={adminPassword} 
            venueCounts={fullVenueCounts}
            onLogout={() => { 
              setIsAdminAuthenticated(false); 
              setAdminPassword('');
              setView('home'); 
            }} 
          />
        )
      ) : (
        <>

          <div className="events-grid">
            {sortedEvents.map(event => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
          
          {sortedEvents.length === 0 && !isLoading && (
            <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
              <p>No se encontraron espectáculos con esos filtros.</p>
            </div>
          )}

          {isLoading && (
             <div style={{ textAlign: 'center', padding: '4rem' }}>
                <RefreshCw className="spin accent-color" size={48} />
                <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>Cargando eventos...</p>
             </div>
          )}
        </>
      )}
      
      <footer>
        <p>Madrid Dance © 2026 | Versión 2.7</p>
        <div style={{ marginTop: '1rem' }}>
           <span className="admin-link" onClick={() => setView(view === 'admin' ? 'home' : 'admin')}>
             {view === 'admin' ? 'Ver Cartelera' : 'Administración'}
           </span>
        </div>
      </footer>
    </div>
  );
}

export default App;
