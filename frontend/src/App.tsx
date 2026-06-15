import { useState, useEffect } from 'react';
import { Login } from './components/Login';
import { Register } from './components/Register';
import { Navbar } from './components/Navbar';
import { Dashboard } from './components/Dashboard';
import './App.css';

interface UserSession {
  user_id: number;
  name: string;
  email: string;
}

function App() {
  const [user, setUser] = useState<UserSession | null>(null);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session on mount
    const savedUser = localStorage.getItem('mca_mentor_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        console.error("Failed to parse saved user session:", e);
        localStorage.removeItem('mca_mentor_user');
      }
    }
    setLoading(false);
  }, []);

  const handleLoginSuccess = (userId: number, name: string, email: string) => {
    const sessionData = { user_id: userId, name, email };
    localStorage.setItem('mca_mentor_user', JSON.stringify(sessionData));
    setUser(sessionData);
  };

  const handleLogout = () => {
    localStorage.removeItem('mca_mentor_user');
    setUser(null);
    setAuthMode('login');
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#080d1a', color: '#fff' }}>
        <h2>Loading Platform OS...</h2>
      </div>
    );
  }

  return (
    <div className="app-wrapper">
      {user ? (
        <>
          <Navbar userName={user.name} onLogout={handleLogout} />
          <main>
            <Dashboard userId={user.user_id} />
          </main>
        </>
      ) : authMode === 'login' ? (
        <Login 
          onLoginSuccess={handleLoginSuccess} 
          onToggleAuth={() => setAuthMode('register')} 
        />
      ) : (
        <Register 
          onRegisterSuccess={() => setAuthMode('login')} 
          onLoginSuccess={handleLoginSuccess}
          onToggleAuth={() => setAuthMode('login')} 
        />
      )}
    </div>
  );
}

export default App;
