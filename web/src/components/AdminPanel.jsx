import React, { useState } from 'react';
import { 
  Shield, 
  RefreshCw, 
  CheckSquare, 
  Square, 
  ExternalLink, 
  LogOut, 
  BarChart3, 
  LayoutDashboard,
  MapPin,
  Building2,
  ChevronRight,
  Sparkles
} from 'lucide-react';

const THEATERS = [
  { id: 'real', name: 'Teatro Real' },
  { id: 'canal', name: 'Teatros del Canal' },
  { id: 'matadero', name: 'Centro Danza Matadero' },
  { id: 'zarzuela', name: 'Teatro de la Zarzuela' },
  { id: 'gran_via', name: 'Teatro Gran Vía' },
  { id: 'real_coliseo', name: 'Real Coliseo Carlos III' },
  { id: 'paco_rabal', name: 'Centro Cultural Paco Rabal' },
  { id: 'majadahonda', name: 'Casa de la Cultura Carmen Conde' },
  { id: 'getafe', name: 'Teatro Federico García Lorca' },
  { id: 'mostoles', name: 'Teatro del Bosque' },
  { id: 'boadilla', name: 'Boadilla del Monte' },
  { id: 'conde_duque', name: 'Conde Duque' },
  { id: 'el_pozo', name: 'CC El Pozo' },
  { id: 'maris_stella', name: 'CEAC Maris Stella' },
  { id: 'el_torito', name: 'CC El Torito' },
  { id: 'casa_de_vacas', name: 'CC Casa de Vacas' },
  { id: 'ciudad_pegaso', name: 'CC Ciudad Pegaso' },
  { id: 'vallecas_teatro', name: 'Teatro de Vallecas' },
  { id: 'las_californias', name: 'CC Las Californias' },
  { id: 'trece_rosas', name: 'Auditorio Trece Rosas' },
  { id: 'museo_historia', name: 'Museo de Historia' },
  { id: 'ivan_de_vargas', name: 'Biblioteca Iván de Vargas' },
  { id: 'dulce_chacon', name: 'EI Dulce Chacón' },
  { id: 'escalera_jacob', name: 'La Escalera de Jacob' },
  { id: 'la_usina', name: 'Teatro La Usina' },
  { id: 'cuarta_pared', name: 'Sala Cuarta Pared' },
  { id: 'corral_usera', name: 'El Corral de Usera' },
  { id: 'fuenlabrada_tomas_valiente', name: 'Teatro Tomás y Valiente' },
  { id: 'fuenlabrada_josep_carreras', name: 'Teatro Josep Carreras' },
  { id: 'replika', name: 'Réplika Teatro' },
  { id: 'dt_espacio', name: 'DT Espacio Escénico' },
  { id: 'ahuja', name: 'Teatro Elías Ahuja' },
  { id: 'placido', name: 'Auditorio Plácido Domingo' }
];

export default function AdminPanel({ onLogout, password, venueCounts, municipalityCounts }) {
  const [activeTab, setActiveTab] = useState('update'); // 'update' or 'stats'
  const [selected, setSelected] = useState([]);
  const [isUpdating, setIsUpdating] = useState(false);
  const [status, setStatus] = useState(null);

  const toggleTheater = (id) => {
    setSelected(prev => 
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    );
  };

  const selectAll = () => setSelected(THEATERS.map(t => t.id));
  const selectNone = () => setSelected([]);

  const handleUpdate = async (venues) => {
    setIsUpdating(true);
    setStatus({ type: 'info', message: 'Conectando con el servidor seguro...' });

    try {
      const response = await fetch('/api/dispatch.php', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          password: password,
          venues: venues.join(',')
        })
      });

      const result = await response.json();

      if (response.ok) {
        setStatus({ 
          type: 'success', 
          message: '¡Petición enviada! El servidor está actualizando los datos en segundo plano.' 
        });
      } else {
        setStatus({ type: 'error', message: `Error del Servidor: ${result.message}` });
      }
    } catch (err) {
      setStatus({ type: 'error', message: `Error de conexión: ${err.message}` });
    } finally {
      setIsUpdating(false);
    }
  };

  const renderStats = () => (
    <div className="stats-container animate-fade-in">
      <div className="stats-section">
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
          <Building2 size={20} className="accent-color" /> Por Teatro
        </h3>
        <div className="stats-grid">
          {Object.entries(venueCounts || {}).sort((a,b) => b[1] - a[1]).map(([name, count]) => (
            <div key={name} className="stat-card">
              <span className="stat-label">{name}</span>
              <span className="stat-value">{count}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="stats-section" style={{ marginTop: '3rem' }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
          <MapPin size={20} className="accent-color" /> Por Municipio
        </h3>
        <div className="stats-grid">
          {Object.entries(municipalityCounts || {}).sort((a,b) => b[1] - a[1]).map(([name, count]) => (
            <div key={name} className="stat-card municipality">
              <span className="stat-label">{name}</span>
              <span className="stat-value">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderUpdate = () => (
    <div className="update-container animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1.5rem' }}>
          <div>
            <h3 style={{ margin: 0 }}>Gestión de Scrapers</h3>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', opacity: 0.6 }}>Selecciona los teatros que deseas sincronizar.</p>
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
              <button onClick={selectAll} className="text-button" style={{ fontSize: '0.85rem' }}>Seleccionar todos</button>
              <button onClick={selectNone} className="text-button" style={{ fontSize: '0.85rem' }}>Deseleccionar</button>
          </div>
      </div>

      <div className="theaters-grid">
        {THEATERS.sort((a,b) => a.name.localeCompare(b.name)).map(theater => (
          <div 
            key={theater.id} 
            onClick={() => toggleTheater(theater.id)}
            className={`theater-item ${selected.includes(theater.id) ? 'selected' : ''}`}
          >
            {selected.includes(theater.id) ? <CheckSquare size={18} className="accent-color" /> : <Square size={18} style={{ opacity: 0.3 }} />}
            <span>{theater.name}</span>
          </div>
        ))}
      </div>

      <div className="action-bar glass-card">
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <button 
            onClick={() => handleUpdate(selected)} 
            disabled={isUpdating || selected.length === 0}
            className="primary-button"
            style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '1rem 2rem' }}
          >
            <RefreshCw size={20} className={isUpdating ? 'spin' : ''} />
            {isUpdating ? 'Procesando...' : `Actualizar seleccionados (${selected.length})`}
          </button>
          
          <button 
            onClick={() => handleUpdate([])} 
            disabled={isUpdating}
            className="secondary-button"
            style={{ padding: '1rem 1.5rem' }}
          >
            Actualizar TODO
          </button>
        </div>
        <p style={{ margin: 0, fontSize: '0.8rem', opacity: 0.5, maxWidth: '250px' }}>
          La actualización se realiza en el servidor. Los cambios pueden tardar unos minutos en reflejarse.
        </p>
      </div>
    </div>
  );

  return (
    <div className="admin-panel-wrapper">
      <div className="admin-header">
        <div className="header-title">
          <div className="logo-icon">
            <Shield size={24} />
          </div>
          <div>
            <h2 style={{ margin: 0 }}>Panel de Control</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', opacity: 0.7 }}>
              <Sparkles size={12} className="accent-color" />
              <span>Administrador Autenticado</span>
            </div>
          </div>
        </div>
        <button onClick={onLogout} className="logout-btn">
          <LogOut size={18} />
          <span>Salir</span>
        </button>
      </div>

      <div className="admin-tabs">
        <button 
          className={`tab-btn ${activeTab === 'update' ? 'active' : ''}`}
          onClick={() => setActiveTab('update')}
        >
          <RefreshCw size={18} />
          Actualizar Eventos
        </button>
        <button 
          className={`tab-btn ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          <LayoutDashboard size={18} />
          Estadísticas
        </button>
      </div>

      <div className="admin-content">
        {activeTab === 'update' ? renderUpdate() : renderStats()}
      </div>

      {status && (
        <div className={`status-toast ${status.type}`}>
          <div className="status-icon">
            {status.type === 'success' ? <CheckSquare size={20} /> : <RefreshCw size={20} className="spin" />}
          </div>
          <div className="status-body">
            <div className="status-title">
              {status.type === 'error' ? 'Error' : status.type === 'success' ? 'Éxito' : 'Procesando'}
            </div>
            <div className="status-message">{status.message}</div>
            {status.type === 'success' && (
              <a href="https://github.com/adriandiazmantecon-sudo/danza/actions" target="_blank" rel="noreferrer" className="github-link">
                Ver progreso en GitHub Actions <ExternalLink size={12} />
              </a>
            )}
          </div>
          <button className="close-toast" onClick={() => setStatus(null)}>&times;</button>
        </div>
      )}
    </div>
  );
}
