import React, { useState } from 'react';
import { Shield, RefreshCw, CheckSquare, Square, ExternalLink, LogOut, CheckCircle2 } from 'lucide-react';

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

export default function AdminPanel({ onLogout, password }) {
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
      // Call our PHP Backend instead of GitHub API
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
          message: '¡Petición enviada! El servidor está actualizando los datos.' 
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

      <div style={{ 
        marginBottom: '2rem', 
        padding: '1rem', 
        background: 'rgba(var(--accent-rgb), 0.1)', 
        borderRadius: '12px',
        border: '1px solid rgba(var(--accent-rgb), 0.2)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem'
      }}>
        <CheckCircle2 className="accent-color" size={20} />
        <p style={{ fontSize: '0.9rem', margin: 0 }}>
          Sesión segura activa. El token de GitHub está protegido en el servidor.
        </p>
      </div>

      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1.5rem' }}>
            <h3 style={{ margin: 0 }}>Actualizar Eventos</h3>
            <div style={{ display: 'flex', gap: '1rem' }}>
                <button onClick={selectAll} className="text-button" style={{ fontSize: '0.85rem' }}>Seleccionar todos</button>
                <button onClick={selectNone} className="text-button" style={{ fontSize: '0.85rem' }}>Deseleccionar</button>
            </div>
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
                padding: '0.75rem',
                borderRadius: '8px',
                background: selected.includes(theater.id) ? 'rgba(var(--accent-rgb), 0.2)' : 'rgba(255,255,255,0.03)',
                border: '1px solid ' + (selected.includes(theater.id) ? 'var(--accent-primary)' : 'rgba(255,255,255,0.05)'),
                transition: 'all 0.2s ease'
              }}
            >
              {selected.includes(theater.id) ? <CheckSquare size={18} className="accent-color" /> : <Square size={18} style={{ opacity: 0.5 }} />}
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
            {isUpdating ? 'Procesando...' : `Actualizar seleccionados (${selected.length})`}
          </button>
          
          <button 
            onClick={() => handleUpdate([])} 
            disabled={isUpdating}
            className="secondary-button"
            style={{ padding: '1rem' }}
          >
            Actualizar TODO
          </button>
        </div>
      </section>

      {status && (
        <div style={{ 
          marginTop: '2rem', 
          padding: '1.25rem', 
          borderRadius: '12px',
          background: status.type === 'error' ? 'rgba(255,68,68,0.1)' : 
                      status.type === 'success' ? 'rgba(0,200,81,0.1)' : 'rgba(51,181,229,0.1)',
          borderLeft: `4px solid ${status.type === 'error' ? '#ff4444' : 
                                 status.type === 'success' ? '#00c851' : '#33b5e5'}`,
          animation: 'slideIn 0.3s ease-out'
        }}>
          <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
            {status.type === 'error' ? 'Error' : status.type === 'success' ? 'Éxito' : 'Info'}
          </div>
          <div style={{ fontSize: '0.95rem' }}>{status.message}</div>
          {status.type === 'success' && (
            <div style={{ marginTop: '0.75rem', fontSize: '0.85rem' }}>
              Puedes ver el progreso en <a href="https://github.com/adriandiazmantecon-sudo/danza/actions" target="_blank" rel="noreferrer" style={{ color: 'var(--accent-primary)', textDecoration: 'underline' }}>GitHub Actions <ExternalLink size={12} /></a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
