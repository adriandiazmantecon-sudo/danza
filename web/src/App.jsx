// Version 3.0 - Month Filtering & Unified Filters
import React, { useState, useEffect, useMemo } from 'react';
import { format, parseISO, startOfMonth, endOfMonth, isWithinInterval } from 'date-fns';
import { es } from 'date-fns/locale';
import EventCard from './components/EventCard';
import AdminPanel from './components/AdminPanel';
import FilterMenu from './components/FilterMenu';
import { Search, Lock, RefreshCw, Calendar, SlidersHorizontal } from 'lucide-react';

function App() {
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterType, setFilterType] = useState('All');
  const [filterMunicipality, setFilterMunicipality] = useState('All');
  const [filterVenue, setFilterVenue] = useState('All');
  const [filterMonth, setFilterMonth] = useState('All'); // YYYY-MM
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

  // Calculate available months for the dropdown
  const availableMonths = useMemo(() => {
    const monthsSet = new Set();
    events.forEach(e => {
      e.sessions.forEach(s => {
        const d = parseISO(s.date);
        const key = format(d, 'yyyy-MM');
        monthsSet.add(key);
      });
    });
    return Array.from(monthsSet).sort();
  }, [events]);

  const venueCounts = useMemo(() => {
    const counts = {};
    events.forEach(e => {
      counts[e.venue.name] = (counts[e.venue.name] || 0) + 1;
    });
    return counts;
  }, [events]);

  const venues = ['All', ...Object.keys(venueCounts).sort()];
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

    // Month filter
    if (filterMonth !== 'All') {
      const hasSessionInMonth = e.sessions.some(s => {
        const sessionDate = parseISO(s.date);
        return format(sessionDate, 'yyyy-MM') === filterMonth;
      });
      if (!hasSessionInMonth) return false;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const hasFutureSession = e.sessions.length === 0 || e.sessions.some(s => {
      const sessionDate = parseISO(s.date);
      sessionDate.setHours(0, 0, 0, 0);
      return sessionDate >= today;
    });
    if (!showPastEvents && !hasFutureSession) return false;

    return true;
  });

  const handleAdminLogin = (e) => {
    e.preventDefault();
    if (adminPassword.length > 0) {
      setIsAdminAuthenticated(true);
    } else {
      alert('Por favor, introduce la contraseña');
    }
  };

  const sortedEvents = [...filteredEvents].sort((a, b) => {
    const getFirstDate = (event) => {
      const dates = event.sessions.map(s => parseISO(s.date).getTime());
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

      <div className="controls-bar glass-card">
        <div className="search-wrapper">
          <Search size={20} className="search-icon" />
          <input 
            type="text" 
            placeholder="Buscar espectáculos..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        <div className="dropdowns-group">
          <div className="month-selector">
            <Calendar size={18} className="selector-icon" />
            <select value={filterMonth} onChange={(e) => setFilterMonth(e.target.value)}>
              <option value="All">Cualquier mes</option>
              {availableMonths.map(m => (
                <option key={m} value={m}>
                  {format(parseISO(`${m}-01`), 'MMMM yyyy', { locale: es })}
                </option>
              ))}
            </select>
          </div>

          <FilterMenu 
            filterType={filterType} setFilterType={setFilterType} types={types}
            filterMunicipality={filterMunicipality} setFilterMunicipality={setFilterMunicipality} municipalities={municipalities}
            filterVenue={filterVenue} setFilterVenue={setFilterVenue} venues={venues} totalVenuesCount={totalVenuesCount}
            isFreeOnly={isFreeOnly} setIsFreeOnly={setIsFreeOnly}
            showPastEvents={showPastEvents} setShowPastEvents={setShowPastEvents}
            sortBy={sortBy} setSortBy={setSortBy}
          />
        </div>
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
            venueCounts={venueCounts}
            onLogout={() => { 
              setIsAdminAuthenticated(false); 
              setAdminPassword('');
              setView('home'); 
            }} 
          />
        )
      ) : (
        <>
          <div className="results-summary">
            Mostrando <strong>{sortedEvents.length}</strong> espectáculos
            {filterMonth !== 'All' && <span> en <strong>{format(parseISO(`${filterMonth}-01`), 'MMMM yyyy', { locale: es })}</strong></span>}
          </div>

          <div className="events-grid">
            {sortedEvents.map(event => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
          
          {sortedEvents.length === 0 && !isLoading && (
            <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
              <p>No se encontraron espectáculos con esos filtros.</p>
              <button className="text-button" style={{ marginTop: '1rem' }} onClick={() => {
                setFilterType('All');
                setFilterMunicipality('All');
                setFilterVenue('All');
                setFilterMonth('All');
                setSearchQuery('');
                setIsFreeOnly(false);
                setShowPastEvents(false);
              }}>Limpiar todos los filtros</button>
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
        <p>Madrid Dance © 2026 | Versión 3.0</p>
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
