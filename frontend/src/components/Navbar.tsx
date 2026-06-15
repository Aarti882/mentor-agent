import React from 'react';

interface NavbarProps {
  userName: string;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ userName, onLogout }) => {
  return (
    <header className="navbar">
      <a href="/" className="navbar-brand">
        🎓 <span className="gradient-text">CAREER MENTOR</span>
      </a>

      <div className="navbar-actions">
        <span className="navbar-status">
          <span
            style={{
              display: 'inline-block',
              width: '8px',
              height: '8px',
              backgroundColor: '#10b981',
              borderRadius: '50%',
              marginRight: '6px',
            }}
          ></span>
          Platform Status: Live
        </span>

        <span style={{ fontSize: '14px', color: '#cbd5e1', fontWeight: 500 }}>
          Welcome, <strong style={{ color: '#fff' }}>{userName}</strong>
        </span>

        <button onClick={onLogout} className="btn-logout">
          Sign Out
        </button>
      </div>
    </header>
  );
};
