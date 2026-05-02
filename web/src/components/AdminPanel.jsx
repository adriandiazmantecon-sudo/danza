import React, { useState } from 'react';
import { Shield, RefreshCw, CheckSquare, Square, ExternalLink, LogOut } from 'lucide-react';

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
  { id: 'mostoles', name: 'Teatro del Bosque' }
];

export default function AdminPanel({ onLogout }) {
  const [selected, setSelected] = useState([]);
  const [isUpdating, setIsUpdating] = useState(false);
  const [status, setStatus] = useState(null);
  const [githubToken, setGithubToken] = useState(localStorage.getItem('gh_token') || '');
  const [isTokenSaved, setIsTokenSaved] = useState(!!localStorage.getItem('gh_token'));

  const toggleTheater = (id) => {
    setSelected(prev => 
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    );
  };

  const selectAll = () => setSelected(THEATERS.map(t => t.id));
  const selectNone = () => setSelected([]);

  const saveToken = () => {
    localStorage.setItem('gh_token', githubToken);
    setIsTokenSaved(true);
    setStatus({ type: 'success', message: 'Token guardado localmente' });
  };

  const handleUpdate = async (venues) => {
    if (!githubToken) {
      setStatus({ type: 'error', message: 'Falta el Token de GitHub' });
      return;
    }

    setIsUpdating(true);
    setStatus({ type: 'info', message: 'Iniciando proceso en GitHub...' });

    try {
      // GitHub API call to trigger workflow
      const response = await fetch('https://api.github.com/repos/adriandiazmantecon-sudo/danza/dispatches', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${githubToken}`,
          'Accept': 'application/vnd.github+json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_type: 'trigger-scrape',
          client_payload: {
            venues: venues.join(',')
          }
        })
      });

      if (response.ok) {
        setStatus({ 
          type: 'success', 
          message: '¡Acción lanzada con éxito! Los datos tardarán unos minutos en actualizarse.' 
        });
      } else {
        const error = await response.json();
        setStatus({ type: 'error', message: `Error de GitHub: ${error.message}` });
      }
    } catch (err) {
      setStatus({ type: 'error', message: `Error de conexión: ${err.message}` });
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="admin-panel glass-card" style={{ maxWidth: '800px', margin: '2rem auto', padding: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
          <Shield className="accent-color" /> Panel de Control
        </h2>
        <button onClick={onLogout} className="secondary-button" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <LogOut size={16} /> Salir
        </button>
      </div>

      <section style={{ marginBottom: '2rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '12px' }}>
        <h4 style={{ marginTop: 0 }}>Configuración de GitHub</h4>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Necesitas un Personal Access Token (PAT) con permisos de 'repo'.
        </p>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input 
            type="password" 
            placeholder="GitHub Token (Classic)" 
            value={githubToken}
            onChange={(e) => setGithubToken(e.target.value)}
            style={{ flexGrow: 1 }}
          />
          <button onClick={saveToken} disabled={!githubToken}>
            {isTokenSaved ? 'Actualizar Token' : 'Guardar Token'}
          </button>
        </div>
        <p style={{ fontSize: '0.75rem', marginTop: '0.5rem', opacity: 0.7 }}>
          * El token se guarda solo en tu navegador (localStorage).
        </p>
      </section>

      <section>
        <h3>Actualizar Eventos</h3>
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
          <button onClick={selectAll} className="text-button">Seleccionar todos</button>
          <button onClick={selectNone} className="text-button">Deseleccionar</button>
        </div>

        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', 
          gap: '0.75rem',
          marginBottom: '2rem' 
        }}>
          {THEATERS.map(theater => (
            <div 
              key={theater.id} 
              onClick={() => toggleTheater(theater.id)}
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem', 
                cursor: 'pointer',
                padding: '0.5rem',
                borderRadius: '8px',
                background: selected.includes(theater.id) ? 'rgba(var(--accent-rgb), 0.2)' : 'transparent',
                border: '1px solid ' + (selected.includes(theater.id) ? 'var(--accent-primary)' : 'rgba(255,255,255,0.1)')
              }}
            >
              {selected.includes(theater.id) ? <CheckSquare size={18} className="accent-color" /> : <Square size={18} />}
              <span style={{ fontSize: '0.9rem' }}>{theater.name}</span>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <button 
            onClick={() => handleUpdate(selected)} 
            disabled={isUpdating || selected.length === 0}
            className="primary-button"
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '1rem 2rem' }}
          >
            <RefreshCw size={18} className={isUpdating ? 'spin' : ''} />
            {isUpdating ? 'Actualizando...' : `Actualizar seleccionados (${selected.length})`}
          </button>
          
          <button 
            onClick={() => handleUpdate([])} 
            disabled={isUpdating}
            className="secondary-button"
          >
            Actualizar TODO
          </button>
        </div>
      </section>

      {status && (
        <div style={{ 
          marginTop: '2rem', 
          padding: '1rem', 
          borderRadius: '8px',
          background: status.type === 'error' ? 'rgba(255,0,0,0.1)' : 
                      status.type === 'success' ? 'rgba(0,255,0,0.1)' : 'rgba(0,0,255,0.1)',
          borderLeft: `4px solid ${status.type === 'error' ? '#ff4444' : 
                                 status.type === 'success' ? '#00c851' : '#33b5e5'}`
        }}>
          {status.message}
          {status.type === 'success' && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.85rem' }}>
              Pueedes ver el progreso en <a href="https://github.com/adriandiazmantecon-sudo/danza/actions" target="_blank" rel="noreferrer" style={{ color: 'inherit', textDecoration: 'underline' }}>GitHub Actions <ExternalLink size={12} /></a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
