import React, { useState, useEffect } from 'react';
import { X, Mail, User } from 'lucide-react';

interface LoginProps {
  onLoginSuccess: (userId: number, name: string, email: string) => void;
  onToggleAuth: () => void;
}

export const Login: React.FC<LoginProps> = ({ onLoginSuccess, onToggleAuth }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Google Selector Modal states
  const [showGoogleSelector, setShowGoogleSelector] = useState(false);
  const [showCustomGoogle, setShowCustomGoogle] = useState(false);
  const [customGoogleEmail, setCustomGoogleEmail] = useState('');
  const [customGoogleName, setCustomGoogleName] = useState('');
  const [usersList, setUsersList] = useState<{ id: number; name: string; email: string }[]>([]);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/users');
        if (response.ok) {
          const data = await response.json();
          setUsersList(data);
        } else {
          loadMockUsers();
        }
      } catch (err) {
        console.warn("Backend user list fetch failed. Loading local mock database users...");
        loadMockUsers();
      }
    };

    const loadMockUsers = () => {
      const mockUsersRaw = localStorage.getItem('mca_mentor_mock_users');
      if (mockUsersRaw) {
        try {
          const users = JSON.parse(mockUsersRaw);
          if (users && users.length > 0) {
            setUsersList(users);
            return;
          }
        } catch (e) {
          console.error("Failed to parse mock database users:", e);
        }
      }
      // Seed with initial options if none exists
      const defaultUsers = [
        { id: 1, name: 'Aarti kumari', email: '22aartikumari32@gmail.com' },
        { id: 2, name: 'Guest Candidate', email: 'guest.candidate@gmail.com' }
      ];
      localStorage.setItem('mca_mentor_mock_users', JSON.stringify(defaultUsers));
      setUsersList(defaultUsers);
    };

    if (showGoogleSelector) {
      fetchUsers();
    }
  }, [showGoogleSelector]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to authenticate user account.');
      }

      onLoginSuccess(data.user_id, data.name, data.email);
    } catch (err: any) {
      console.warn("Backend login failed. Attempting offline localStorage database lookup...", err);
      
      // Offline fallback: Check localStorage mock database
      const mockUsersRaw = localStorage.getItem('mca_mentor_mock_users');
      if (mockUsersRaw) {
        try {
          const users = JSON.parse(mockUsersRaw);
          const matchedUser = users.find(
            (u: any) => u.email.toLowerCase() === email.toLowerCase() && u.password === password
          );
          
          if (matchedUser) {
            onLoginSuccess(matchedUser.id, matchedUser.name, matchedUser.email);
            setLoading(false);
            return;
          }
        } catch (e) {
          console.error("Failed to parse mock database:", e);
        }
      }
      
      setError('Invalid email or password. (Offline Mode: Register account first to log in locally).');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async (googleEmail: string, googleName: string) => {
    setLoading(true);
    setShowGoogleSelector(false);
    setError(null);
    try {
      // Attempt direct simulated Google OAuth login
      const response = await fetch('http://127.0.0.1:8000/api/auth/direct', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: googleName,
          email: googleEmail
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Direct authentication failed.');
      }

      onLoginSuccess(data.user_id, data.name, data.email);
    } catch (err: any) {
      // Offline fallback: Demo Mode
      console.warn("Backend offline or direct auth failed. Logging in locally:", err);
      
      // Save Google User in local storage mock database to make it persistent
      const mockUsersRaw = localStorage.getItem('mca_mentor_mock_users') || '[]';
      try {
        const users = JSON.parse(mockUsersRaw);
        const exists = users.find((u: any) => u.email.toLowerCase() === googleEmail.toLowerCase());
        const mockId = exists ? exists.id : Date.now();
        
        if (!exists) {
          users.push({
            id: mockId,
            name: googleName,
            email: googleEmail,
            password: 'google_oauth_fallback_secret_password_phrase'
          });
          localStorage.setItem('mca_mentor_mock_users', JSON.stringify(users));
        }
        
        onLoginSuccess(mockId, googleName, googleEmail);
      } catch (e) {
        onLoginSuccess(Date.now(), googleName, googleEmail);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="glass-panel auth-card">
        <div className="auth-header">
          <h2 style={{ margin: '0 0 8px 0', fontSize: '28px' }} className="gradient-text">
            Student Login
          </h2>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: '14px' }}>
            Career & Syllabus Mentor Agent
          </p>
        </div>

        {error && (
          <div
            style={{
              background: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#fca5a5',
              padding: '12px',
              borderRadius: '8px',
              marginBottom: '20px',
              fontSize: '14px',
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              className="form-control"
              placeholder="e.g. student@gmail.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              className="form-control"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', textAlign: 'center', margin: '15px 0', color: '#94a3b8', fontSize: '13px' }}>
          <hr style={{ flex: 1, borderColor: 'rgba(255,255,255,0.08)' }} />
          <span style={{ padding: '0 10px' }}>OR</span>
          <hr style={{ flex: 1, borderColor: 'rgba(255,255,255,0.08)' }} />
        </div>

        <button 
          type="button" 
          onClick={() => setShowGoogleSelector(true)}
          disabled={loading}
          style={{
            width: '100%',
            padding: '12px 20px',
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.15)',
            background: '#ffffff',
            color: '#0f172a',
            fontSize: '15px',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
            opacity: loading ? 0.6 : 1
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v3.927h6.6c-.29 1.5-.143 2.5-1.5 3.4l2.4 1.86a11.9 11.9 0 0 0 3.745-7.117Z" />
            <path fill="#34A853" d="M12 24c3.24 0 5.97-1.08 7.96-2.913l-3.86-3a7.5 7.5 0 0 1-11.45-3.953l-4 3.093A12 12 0 0 0 12 24Z" />
            <path fill="#FBBC05" d="M4.65 14.133a7.16 7.16 0 0 1 0-4.266l-4-3.093a11.98 11.98 0 0 0 0 10.452l4-3.093Z" />
            <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.43-3.43A11.93 11.93 0 0 0 12 0 12 12 0 0 0 .65 6.774l4 3.093a7.43 7.43 0 0 1 7.35-5.117Z" />
          </svg>
          Continue with Google
        </button>

        <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '14px', color: '#94a3b8' }}>
          Don't have an account?{' '}
          <button
            onClick={onToggleAuth}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#8b5cf6',
              cursor: 'pointer',
              fontWeight: 600,
              padding: 0,
            }}
          >
            Register Here
          </button>
        </div>
      </div>

      {/* ----------------- GOOGLE IDENTITY SERVICES MODAL POPUP ----------------- */}
      {showGoogleSelector && (
        <div className="modal-overlay" style={{ background: 'rgba(0,0,0,0.85)' }} onClick={() => setShowGoogleSelector(false)}>
          <div className="modal-content" style={{ maxWidth: '380px', padding: '25px', background: '#ffffff', color: '#1f2937', border: 'none' }} onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" style={{ color: '#94a3b8', top: '15px', right: '15px' }} onClick={() => setShowGoogleSelector(false)}>
              <X size={20} />
            </button>
            
            <div style={{ textAlign: 'center', marginBottom: '20px' }}>
              <svg width="32" height="32" viewBox="0 0 24 24" style={{ marginBottom: '10px' }}>
                <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v3.927h6.6c-.29 1.5-.143 2.5-1.5 3.4l2.4 1.86a11.9 11.9 0 0 0 3.745-7.117Z" />
                <path fill="#34A853" d="M12 24c3.24 0 5.97-1.08 7.96-2.913l-3.86-3a7.5 7.5 0 0 1-11.45-3.953l-4 3.093A12 12 0 0 0 12 24Z" />
                <path fill="#FBBC05" d="M4.65 14.133a7.16 7.16 0 0 1 0-4.266l-4-3.093a11.98 11.98 0 0 0 0 10.452l4-3.093Z" />
                <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.43-3.43A11.93 11.93 0 0 0 12 0 12 12 0 0 0 .65 6.774l4 3.093a7.43 7.43 0 0 1 7.35-5.117Z" />
              </svg>
              <h3 style={{ margin: '0 0 5px 0', fontSize: '18px', color: '#111827', fontWeight: 700 }}>Choose an account</h3>
              <p style={{ margin: 0, fontSize: '13px', color: '#6b7280' }}>to continue to Career Mentor</p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '250px', overflowY: 'auto', marginBottom: '15px' }}>
              {usersList.map((usr) => {
                const initial = usr.name ? usr.name.charAt(0).toUpperCase() : '?';
                const colors = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#14b8a6'];
                const avatarBg = colors[usr.name.length % colors.length] || '#8b5cf6';
                
                return (
                  <button 
                    key={usr.id}
                    onClick={() => handleGoogleLogin(usr.email, usr.name)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      width: '100%',
                      padding: '12px',
                      background: '#f9fafb',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      textAlign: 'left'
                    }}
                  >
                    <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: avatarBg, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
                      {initial}
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, color: '#111827', fontSize: '13px' }}>{usr.name}</div>
                      <div style={{ color: '#6b7280', fontSize: '11px' }}>{usr.email}</div>
                    </div>
                  </button>
                );
              })}
              {usersList.length === 0 && (
                <p style={{ textAlign: 'center', fontSize: '13px', color: '#6b7280', margin: '20px 0' }}>
                  No accounts registered yet.
                </p>
              )}
            </div>

            {/* Custom Google Account option toggle */}
            {!showCustomGoogle ? (
              <button 
                onClick={() => setShowCustomGoogle(true)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  width: '100%',
                  padding: '10px',
                  background: 'transparent',
                  border: '1px dashed #d1d5db',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: 600,
                  color: '#4b5563'
                }}
              >
                Use another account
              </button>
            ) : (
              <div style={{ background: '#f3f4f6', padding: '12px', borderRadius: '8px', marginTop: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '12px', fontWeight: 700, color: '#4b5563' }}>Enter Account Info</span>
                  <button onClick={() => setShowCustomGoogle(false)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#9ca3af', padding: 0 }}><X size={14} /></button>
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ position: 'relative' }}>
                    <User size={12} style={{ position: 'absolute', left: '8px', top: '10px', color: '#9ca3af' }} />
                    <input 
                      type="text" 
                      placeholder="Google Name" 
                      value={customGoogleName}
                      onChange={(e) => setCustomGoogleName(e.target.value)}
                      style={{ width: '100%', padding: '6px 8px 6px 26px', fontSize: '12px', borderRadius: '4px', border: '1px solid #d1d5db', boxSizing: 'border-box' }}
                    />
                  </div>
                  <div style={{ position: 'relative' }}>
                    <Mail size={12} style={{ position: 'absolute', left: '8px', top: '10px', color: '#9ca3af' }} />
                    <input 
                      type="email" 
                      placeholder="Google Email" 
                      value={customGoogleEmail}
                      onChange={(e) => setCustomGoogleEmail(e.target.value)}
                      style={{ width: '100%', padding: '6px 8px 6px 26px', fontSize: '12px', borderRadius: '4px', border: '1px solid #d1d5db', boxSizing: 'border-box' }}
                    />
                  </div>
                  <button 
                    type="button"
                    onClick={() => {
                      if (customGoogleEmail && customGoogleName) {
                        handleGoogleLogin(customGoogleEmail, customGoogleName);
                      } else {
                        alert("Please provide both name and email.");
                      }
                    }}
                    style={{ width: '100%', padding: '6px', background: '#111827', color: '#fff', fontSize: '12px', fontWeight: 'bold', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                  >
                    Confirm & Sign In
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
