// Version 3.0 - Month Filtering & Unified Filters
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { format, parseISO, startOfMonth, endOfMonth, isWithinInterval } from 'date-fns';
import { es } from 'date-fns/locale';
import EventCard from './components/EventCard';
import AdminPanel from './components/AdminPanel';
import FilterMenu from './components/FilterMenu';
import CalendarFilter from './components/CalendarFilter';
import { Search, Lock, RefreshCw, Calendar, SlidersHorizontal, ChevronDown, ChevronUp } from 'lucide-react';

function App() {
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterType, setFilterType] = useState('All');
  const [filterMunicipality, setFilterMunicipality] = useState('All');
  const [filterVenue, setFilterVenue] = useState('All');
  const [filterMonth, setFilterMonth] = useState('All'); // YYYY-MM
  const [filterDate, setFilterDate] = useState(null); // YYYY-MM-DD
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
  const { currentMonths, pastMonths } = useMemo(() => {
    const monthsSet = new Set();
    events.forEach(e => {
      e.sessions.forEach(s => {
        const d = parseISO(s.date);
        const key = format(d, 'yyyy-MM');
        monthsSet.add(key);
      });
    });
    
    const sorted = Array.from(monthsSet).sort().reverse();
    const today = new Date();
    const currentMonthKey = format(today, 'yyyy-MM');
    
    const current = [];
    const past = [];
    
    sorted.forEach(m => {
      if (m >= currentMonthKey) {
        current.push(m);
      } else {
        past.push(m);
      }
    });
    
    return { currentMonths: current, pastMonths: past };
  }, [events]);

  const [isMonthOpen, setIsMonthOpen] = useState(false);
  const [showPastMonths, setShowPastMonths] = useState(false);
  const monthRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (monthRef.current && !monthRef.current.contains(event.target)) {
        setIsMonthOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getMonthName = (m) => {
    if (m === 'All') return 'Cualquier mes';
    return format(parseISO(`${m}-01`), 'MMMM yyyy', { locale: es });
  };

  const venueCounts = useMemo(() => {
    const counts = {};
    events.forEach(e => {
      counts[e.venue.name] = (counts[e.venue.name] || 0) + 1;
    });
    return counts;
  }, [events]);

  const municipalityCounts = useMemo(() => {
    const counts = {};
    events.forEach(e => {
      const muni = e.venue.municipality || 'Madrid';
      counts[muni] = (counts[muni] || 0) + 1;
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

    // Specific date filter
    if (filterDate) {
      const hasSessionOnDay = e.sessions.some(s => {
        return format(parseISO(s.date), 'yyyy-MM-dd') === filterDate;
      });
      if (!hasSessionOnDay) return false;
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
        <h1 onClick={() => window.location.reload()} style={{ cursor: 'pointer' }}>Danza en Madrid</h1>
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
          <div className="month-selector-custom" ref={monthRef}>
            <button 
              className={`month-selector-btn ${isMonthOpen ? 'active' : ''}`}
              onClick={() => setIsMonthOpen(!isMonthOpen)}
            >
              <Calendar size={18} className="selector-icon-static" />
              <span style={{ flex: 1 }}>{getMonthName(filterMonth)}</span>
              <ChevronDown size={16} className={`chevron ${isMonthOpen ? 'open' : ''}`} />
            </button>

            {isMonthOpen && (
              <div className="month-dropdown">
                <button 
                  className={`month-option ${filterMonth === 'All' ? 'active' : ''}`}
                  onClick={() => { setFilterMonth('All'); setIsMonthOpen(false); }}
                >
                  Cualquier mes
                </button>
                
                {currentMonths.map(m => (
                  <button 
                    key={m} 
                    className={`month-option ${filterMonth === m ? 'active' : ''}`}
                    onClick={() => { setFilterMonth(m); setIsMonthOpen(false); }}
                  >
                    {getMonthName(m)}
                  </button>
                ))}

                {pastMonths.length > 0 && (
                  <>
                    <button 
                      className="past-months-toggle"
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowPastMonths(!showPastMonths);
                      }}
                    >
                      <span>Meses anteriores</span>
                      {showPastMonths ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                    
                    {showPastMonths && (
                      <div className="past-months-list">
                        {pastMonths.map(m => (
                          <button 
                            key={m} 
                            className={`month-option ${filterMonth === m ? 'active' : ''}`}
                            onClick={() => { setFilterMonth(m); setIsMonthOpen(false); }}
                            style={{ paddingLeft: '2rem' }}
                          >
                            {getMonthName(m)}
                          </button>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>

          <CalendarFilter 
            events={events} 
            selectedDate={filterDate} 
            onDateSelect={(date) => {
              setFilterDate(date);
              if (date) {
                // If a date is selected, we might want to set the month filter to that month
                // or just keep them independent. Let's keep them independent for now.
              }
            }} 
          />

          <FilterMenu 
            filterType={filterType} setFilterType={setFilterType} types={types}
            filterMunicipality={filterMunicipality} setFilterMunicipality={setFilterMunicipality} municipalities={municipalities}
            filterVenue={filterVenue} setFilterVenue={setFilterVenue} venues={venues} totalVenuesCount={totalVenuesCount}
            isFreeOnly={isFreeOnly} setIsFreeOnly={setIsFreeOnly}
            showPastEvents={showPastEvents} setShowPastEvents={setShowPastEvents}
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
            municipalityCounts={municipalityCounts}
            onLogout={() => { 
              setIsAdminAuthenticated(false); 
              setAdminPassword('');
              setView('home'); 
            }} 
          />
        )
      ) : (
        <>
          <div className="results-header">
            <div className="results-summary">
              Mostrando <strong>{sortedEvents.length}</strong> espectáculos
              {filterDate && <span> el <strong>{format(parseISO(filterDate), "d 'de' MMMM yyyy", { locale: es })}</strong></span>}
              {filterMonth !== 'All' && !filterDate && <span> en <strong>{format(parseISO(`${filterMonth}-01`), 'MMMM yyyy', { locale: es })}</strong></span>}
            </div>

            <div className="sort-wrapper">
              <label htmlFor="sort-select">Ordenar por:</label>
              <select 
                id="sort-select" 
                value={sortBy} 
                onChange={(e) => setSortBy(e.target.value)}
                className="minimal-select"
              >
                <option value="DateAsc">Fecha (Próximos)</option>
                <option value="DateDesc">Fecha (Lejanos)</option>
                <option value="PriceAsc">Precio (Más baratos)</option>
                <option value="PriceDesc">Precio (Más caros)</option>
                <option value="Venue">Teatro (A-Z)</option>
                <option value="Municipality">Municipio (A-Z)</option>
              </select>
            </div>
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
                setFilterDate(null);
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
        <span>Madrid Dance &copy; 2026 | Versión 3.1</span>
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
