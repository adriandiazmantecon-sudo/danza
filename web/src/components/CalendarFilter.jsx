import React, { useState, useMemo, useRef, useEffect } from 'react';
import { 
  format, 
  addMonths, 
  subMonths, 
  startOfMonth, 
  endOfMonth, 
  startOfWeek, 
  endOfWeek, 
  eachDayOfInterval, 
  isSameDay, 
  isSameMonth, 
  parseISO,
  setMonth,
  setYear,
  getYear,
  getMonth
} from 'date-fns';
import { es } from 'date-fns/locale';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, ChevronDown, X } from 'lucide-react';

export default function CalendarFilter({ events, onDateSelect, selectedDate }) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const containerRef = useRef(null);

  // Close when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Extract all dates with events
  const eventDates = useMemo(() => {
    const dates = new Set();
    events.forEach(event => {
      event.sessions.forEach(session => {
        try {
          const dateStr = format(parseISO(session.date), 'yyyy-MM-dd');
          dates.add(dateStr);
        } catch (e) {
          // Ignore invalid dates
        }
      });
    });
    return dates;
  }, [events]);

  const days = useMemo(() => {
    const start = startOfWeek(startOfMonth(currentMonth), { weekStartsOn: 1 });
    const end = endOfWeek(endOfMonth(currentMonth), { weekStartsOn: 1 });
    return eachDayOfInterval({ start, end });
  }, [currentMonth]);

  const handlePrevMonth = () => setCurrentMonth(subMonths(currentMonth, 1));
  const handleNextMonth = () => setCurrentMonth(addMonths(currentMonth, 1));

  const years = useMemo(() => {
    const currentYear = getYear(new Date());
    const yearsArr = [];
    for (let i = currentYear - 2; i <= currentYear + 2; i++) {
      yearsArr.push(i);
    }
    return yearsArr;
  }, []);

  const months = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
  ];

  return (
    <div className="calendar-filter-container" ref={containerRef}>
      <button 
        className={`month-selector-btn ${isOpen ? 'active' : ''} ${selectedDate ? 'has-selection' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <CalendarIcon size={18} className="selector-icon-static" />
        <span style={{ flex: 1 }}>
          {selectedDate 
            ? format(parseISO(selectedDate), "d 'de' MMMM", { locale: es }) 
            : 'Calendario'}
        </span>
        {selectedDate ? (
          <X 
            size={16} 
            className="clear-date" 
            onClick={(e) => {
              e.stopPropagation();
              onDateSelect(null);
            }} 
          />
        ) : (
          <ChevronDown size={16} className={`chevron ${isOpen ? 'open' : ''}`} />
        )}
      </button>

      {isOpen && (
        <div className="calendar-dropdown glass-card">
          <div className="calendar-header">
            <button onClick={handlePrevMonth} className="nav-btn"><ChevronLeft size={20} /></button>
            
            <div className="calendar-selectors">
              <select 
                value={getMonth(currentMonth)} 
                onChange={(e) => setCurrentMonth(setMonth(currentMonth, parseInt(e.target.value)))}
                className="calendar-select"
              >
                {months.map((m, i) => (
                  <option key={m} value={i}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>
                ))}
              </select>
              
              <select 
                value={getYear(currentMonth)} 
                onChange={(e) => setCurrentMonth(setYear(currentMonth, parseInt(e.target.value)))}
                className="calendar-select"
              >
                {years.map(y => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>

            <button onClick={handleNextMonth} className="nav-btn"><ChevronRight size={20} /></button>
          </div>

          <div className="calendar-grid">
            {['L', 'M', 'X', 'J', 'V', 'S', 'D'].map(day => (
              <div key={day} className="weekday-label">{day}</div>
            ))}
            
            {days.map((day, i) => {
              const dateStr = format(day, 'yyyy-MM-dd');
              const hasEvents = eventDates.has(dateStr);
              const isSelected = selectedDate === dateStr;
              const isCurrentMonth = isSameMonth(day, currentMonth);
              const isToday = isSameDay(day, new Date());

              return (
                <button
                  key={i}
                  className={`calendar-day ${!isCurrentMonth ? 'other-month' : ''} ${isSelected ? 'selected' : ''} ${isToday ? 'today' : ''} ${hasEvents ? 'has-events' : ''}`}
                  onClick={() => {
                    onDateSelect(dateStr);
                    setIsOpen(false);
                  }}
                >
                  <span className="day-number">{format(day, 'd')}</span>
                  {hasEvents && <div className="event-dot"></div>}
                </button>
              );
            })}
          </div>

          <div className="calendar-footer">
            <button 
              className="text-button" 
              onClick={() => {
                onDateSelect(null);
                setIsOpen(false);
              }}
            >
              Ver todos
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
