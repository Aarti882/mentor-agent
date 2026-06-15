import React, { useState, useEffect } from 'react';

interface LoginProps {
  onLoginSuccess: (userId: number, name: string, email: string) => void;
  onToggleAuth: () => void;
}

export const Login: React.FC<LoginProps> = ({ onLoginSuccess, onToggleAuth }) => {
  const GOOGLE_CLIENT_ID = (import.meta.env.VITE_GOOGLE_CLIENT_ID || "339648349691-us6eg9lbk6k4deblpnh917tdns9dsi2.apps.googleusercontent.com").trim();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initGoogleGSI = () => {
      const google = (window as any).google;
      if (google) {
        google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: (response: any) => {
            handleGoogleCredentialResponse(response.credential);
          },
          cancel_on_tap_outside: false
        });

        google.accounts.id.renderButton(
          document.getElementById("google-signin-button"),
          { theme: "outline", size: "large", width: 320, text: "continue_with", shape: "rectangular" }
        );

        google.accounts.id.prompt();
      }
    };

    const scriptExists = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
    if (!scriptExists) {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = initGoogleGSI;
      document.head.appendChild(script);
    } else {
      const timer = setTimeout(initGoogleGSI, 500);
      return () => clearTimeout(timer);
    }
  }, []);

  const parseJwt = (token: string) => {
    try {
      return JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    } catch (e) {
      return null;
    }
  };

  const handleGoogleCredentialResponse = async (credential: string) => {
    setLoading(true);
    setError(null);
    try {
      const payload = parseJwt(credential);
      const googleEmail = payload?.email || '';
      const googleName = payload?.name || 'Google User';

      const response = await fetch('http://127.0.0.1:8000/api/auth/direct', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: googleName,
          email: googleEmail,
          credential: credential
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Google sign-in authentication failed.');
      }

      onLoginSuccess(data.user_id, data.name, data.email);
    } catch (err: any) {
      console.error("Google sign-in failed:", err);
      setError(err.message || "Failed to authenticate using Google Sign-In.");
    } finally {
      setLoading(false);
    }
  };

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

        <div 
          id="google-signin-button" 
          style={{ 
            width: '100%', 
            minHeight: '44px',
            display: 'flex', 
            justifyContent: 'center',
            marginBottom: '15px'
          }}
        />

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
    </div>
  );
};
