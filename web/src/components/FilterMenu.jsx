import React, { useState, useRef, useEffect } from 'react';
import { Filter, ChevronDown, Check, X } from 'lucide-react';

export default function FilterMenu({ 
  filterType, setFilterType, types,
  filterMunicipality, setFilterMunicipality, municipalities,
  filterVenue, setFilterVenue, venues, totalVenuesCount,
  isFreeOnly, setIsFreeOnly,
  showPastEvents, setShowPastEvents
}) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const hasActiveFilters = filterType !== 'All' || 
                           filterMunicipality !== 'All' || 
                           filterVenue !== 'All' || 
                           isFreeOnly || 
                           showPastEvents;

  const resetFilters = () => {
    setFilterType('All');
    setFilterMunicipality('All');
    setFilterVenue('All');
    setIsFreeOnly(false);
    setShowPastEvents(false);
  };

  return (
    <div className="filter-menu-wrapper" ref={menuRef}>
      <button 
        className={`filter-toggle-button ${hasActiveFilters ? 'active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <Filter size={18} />
        <span>Filtros</span>
        {hasActiveFilters && <span className="filter-badge">!</span>}
        <ChevronDown size={16} className={`chevron ${isOpen ? 'open' : ''}`} />
      </button>

      {isOpen && (
        <div className="filter-dropdown-panel glass-card">
          <div className="filter-section">
            <h4>Danza</h4>
            <div className="filter-grid">
              {types.map(t => (
                <button 
                  key={t} 
                  className={`filter-option ${filterType === t ? 'selected' : ''}`}
                  onClick={() => setFilterType(t)}
                >
                  {t === 'All' ? 'Todos' : t}
                </button>
              ))}
            </div>
          </div>

          <div className="filter-section">
            <h4>Lugar</h4>
            <div className="filter-controls-row">
              <div className="select-wrapper">
                <label>Municipio</label>
                <select value={filterMunicipality} onChange={(e) => setFilterMunicipality(e.target.value)}>
                  {municipalities.map(m => <option key={m} value={m}>{m === 'All' ? 'Todos' : m}</option>)}
                </select>
              </div>
              <div className="select-wrapper">
                <label>Teatro</label>
                <select value={filterVenue} onChange={(e) => setFilterVenue(e.target.value)}>
                  <option value="All">Todos ({totalVenuesCount})</option>
                  {venues.filter(v => v !== 'All').map(v => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="filter-section">
            <h4>Ver</h4>
            <div className="filter-checkboxes">
              <label className="checkbox-label-mini">
                <input 
                  type="checkbox" 
                  checked={isFreeOnly} 
                  onChange={(e) => setIsFreeOnly(e.target.checked)} 
                />
                Solo gratuitos
              </label>
              <label className="checkbox-label-mini">
                <input 
                  type="checkbox" 
                  checked={showPastEvents} 
                  onChange={(e) => setShowPastEvents(e.target.checked)} 
                />
                Mostrar pasados
              </label>
            </div>
          </div>



          <div className="filter-actions">
            <button className="text-button" onClick={resetFilters}>Limpiar filtros</button>
            <button className="primary-button" onClick={() => setIsOpen(false)}>Aplicar</button>
          </div>
        </div>
      )}
    </div>
  );
}
