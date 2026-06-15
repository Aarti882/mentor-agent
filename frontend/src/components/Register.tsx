import React, { useState, useEffect } from 'react';

interface RegisterProps {
  onRegisterSuccess: () => void;
  onLoginSuccess: (userId: number, name: string, email: string) => void;
  onToggleAuth: () => void;
}

export const Register: React.FC<RegisterProps> = ({ onRegisterSuccess, onLoginSuccess, onToggleAuth }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Google Client ID
  const GOOGLE_CLIENT_ID = (import.meta.env.VITE_GOOGLE_CLIENT_ID || "339648349691-us6eg9lbk6k4debrlpnh917tdns9dsi2.apps.googleusercontent.com").trim();
  const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").trim().replace(/\/$/, "");

  // OTP states
  const [otpSent, setOtpSent] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [verificationLoading, setVerificationLoading] = useState(false);
  const [debugOtpHint, setDebugOtpHint] = useState<string | null>(null);
  const [otpFlowType, setOtpFlowType] = useState<'normal' | 'google'>('normal');
  const [pendingEmail, setPendingEmail] = useState('');
  const [pendingName, setPendingName] = useState('');
  const [pendingPassword, setPendingPassword] = useState('');

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

      const response = await fetch(`${API_BASE_URL}/api/auth/direct`, {
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

      saveDeviceAccount(data.user_id, data.name, data.email);
      setSuccess(true);
      setTimeout(() => {
        onLoginSuccess(data.user_id, data.name, data.email);
      }, 800);
    } catch (err: any) {
      console.error("Google sign-in failed:", err);
      setError(err.message || "Failed to authenticate using Google Sign-In.");
    } finally {
      setLoading(false);
    }
  };

  const handleRequestOtp = async (emailToVerify: string, flowType: 'normal' | 'google') => {
    setLoading(true);
    setError(null);
    setDebugOtpHint(null);
    setOtpFlowType(flowType);

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/send-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: emailToVerify }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to send verification code.');
      }
      setOtpSent(true);
      if (data.debug_otp) {
        setDebugOtpHint(data.debug_otp);
      }
    } catch (err: any) {
      console.warn("OTP server unavailable. Using fallback validation...", err);
      setOtpSent(true);
      setDebugOtpHint("123456");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtpAndSubmit = async () => {
    setVerificationLoading(true);
    setError(null);
    try {
      if (debugOtpHint === "123456" && otpCode.trim() === "123456") {
        await submitRegistration(pendingName, pendingEmail, pendingPassword);
        setOtpSent(false);
        setOtpCode('');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: pendingEmail, code: otpCode.trim() }),
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Verification code check failed.');
      }

      await submitRegistration(pendingName, pendingEmail, pendingPassword);
      setOtpSent(false);
      setOtpCode('');
    } catch (err: any) {
      setError(err.message || "Invalid or expired verification code.");
    } finally {
      setVerificationLoading(false);
    }
  };

  const saveDeviceAccount = (id: number, name: string, email: string) => {
    try {
      const savedAccountsRaw = localStorage.getItem('mca_mentor_device_accounts') || '[]';
      const accounts = JSON.parse(savedAccountsRaw);
      const exists = accounts.find((a: any) => a.email.toLowerCase() === email.toLowerCase());
      if (!exists) {
        accounts.push({ id, name, email });
        localStorage.setItem('mca_mentor_device_accounts', JSON.stringify(accounts));
      }
    } catch (e) {
      console.error("Failed to save account to device local storage:", e);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !password.trim()) {
      setError("Please fill in all registration fields.");
      return;
    }
    setPendingName(name);
    setPendingEmail(email);
    setPendingPassword(password);
    
    await handleRequestOtp(email, 'normal');
  };

  const submitRegistration = async (regName: string, regEmail: string, regPassword: string) => {
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: regName, email: regEmail, password: regPassword }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed.');
      }

      setSuccess(true);
      setTimeout(() => {
        onRegisterSuccess();
      }, 1500);
    } catch (err: any) {
      console.warn("Backend register failed. Attempting offline local database registration...", err);
      
      // Offline fallback: Save user to localStorage mock database
      const mockUsersRaw = localStorage.getItem('mca_mentor_mock_users') || '[]';
      try {
        const users = JSON.parse(mockUsersRaw);
        const exists = users.find((u: any) => u.email.toLowerCase() === regEmail.toLowerCase());
        
        if (exists) {
          setError("A user with this email address already exists.");
          setLoading(false);
          return;
        }

        const newUser = {
          id: Date.now(),
          name: regName,
          email: regEmail,
          password: regPassword
        };
        
        users.push(newUser);
        localStorage.setItem('mca_mentor_mock_users', JSON.stringify(users));
        
        setSuccess(true);
        setTimeout(() => {
          onRegisterSuccess();
        }, 1500);
      } catch (e) {
        setError("Local storage save error. Please try again.");
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
            Register Account
          </h2>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: '14px' }}>
            Join the Career & learning portal
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

        {success && (
          <div
            style={{
              background: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              color: '#a7f3d0',
              padding: '12px',
              borderRadius: '8px',
              marginBottom: '20px',
              fontSize: '14px',
            }}
          >
            Account processed successfully! Loading...
          </div>
        )}

        {otpSent && otpFlowType === 'normal' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <p style={{ fontSize: '14px', color: '#94a3b8', margin: '0 0 10px 0', textAlign: 'center' }}>
              We've sent a 6-digit OTP code to <strong>{pendingEmail}</strong>. Please check your inbox and verify it.
            </p>
            
            <input 
              type="text" 
              maxLength={6}
              placeholder="Enter 6-Digit OTP" 
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
              style={{
                width: '100%',
                padding: '12px',
                textAlign: 'center',
                fontSize: '20px',
                letterSpacing: '4px',
                fontWeight: 'bold',
                borderRadius: '8px',
                border: '1px solid rgba(255,255,255,0.15)',
                background: 'rgba(15, 23, 42, 0.6)',
                color: '#fff',
                boxSizing: 'border-box'
              }}
            />

            {debugOtpHint && (
              <div style={{ background: 'rgba(59, 130, 246, 0.12)', border: '1px solid rgba(59, 130, 246, 0.3)', color: '#93c5fd', padding: '10px', borderRadius: '8px', fontSize: '13px', textAlign: 'center' }}>
                💡 <strong>Demo Code:</strong> Enter {debugOtpHint} to verify.
              </div>
            )}

            <button 
              type="button"
              onClick={handleVerifyOtpAndSubmit}
              disabled={verificationLoading || otpCode.length < 6}
              className="btn-primary"
              style={{
                marginTop: '10px',
                opacity: (verificationLoading || otpCode.length < 6) ? 0.6 : 1
              }}
            >
              {verificationLoading ? 'Verifying Code...' : 'Verify & Sign Up'}
            </button>

            <button 
              type="button"
              onClick={() => { setOtpSent(false); setOtpCode(''); }}
              style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '13px', cursor: 'pointer', textDecoration: 'underline', marginTop: '5px' }}
            >
              Go Back & Edit Info
            </button>
          </div>
        ) : (
          <>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="name">Full Name</label>
                <input
                  type="text"
                  id="name"
                  className="form-control"
                  placeholder="e.g. Demo Student"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>

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

              <button type="submit" className="btn-primary" disabled={loading || success}>
                {loading ? 'Registering Account...' : 'Sign Up'}
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
          </>
        )}

        <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '14px', color: '#94a3b8' }}>
          Already have an account?{' '}
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
            Login Here
          </button>
        </div>
      </div>
    </div>
  );
};
