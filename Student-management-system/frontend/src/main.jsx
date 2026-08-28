import React, { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const fallbackData = {
  students_count: 0,
  teachers_count: 0,
  courses_count: 0,
  attendance_count: 0,
  recent_students: [],
  recent_grades: [],
};

const readData = () => {
  const node = document.getElementById('react-dashboard-data');
  if (!node) return fallbackData;

  try {
    return JSON.parse(node.textContent);
  } catch {
    return fallbackData;
  }
};

function MiniMetric({ label, value }) {
  return (
    <div className="react-mini-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function App() {
  const data = useMemo(readData, []);
  const [mode, setMode] = useState('students');
  const activeCount = mode === 'students' ? data.recent_students.length : data.recent_grades.length;

  return (
    <div className="react-widget compact">
      <div className="react-widget-header">
        <div>
          <h4>Live Snapshot</h4>
          <p>{activeCount} recent {mode === 'students' ? 'students' : 'grade records'}</p>
        </div>
        <div className="react-tabs">
          <button className={mode === 'students' ? 'active' : ''} type="button" onClick={() => setMode('students')}>
            Students
          </button>
          <button className={mode === 'grades' ? 'active' : ''} type="button" onClick={() => setMode('grades')}>
            Grades
          </button>
        </div>
      </div>

      <div className="react-mini-grid">
        <MiniMetric label="Students" value={data.students_count} />
        <MiniMetric label="Courses" value={data.courses_count} />
        <MiniMetric label="Attendance" value={data.attendance_count} />
      </div>
    </div>
  );
}

createRoot(document.getElementById('react-dashboard-root')).render(<App />);
