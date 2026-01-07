import React, { useState, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import { loginUser, registerUser } from '../features/auth/authSlice';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css';

import type { RootState } from '../app/store';

const LoginPage: React.FC = () => {
    const dispatch = useAppDispatch();
    const navigate = useNavigate();
    const { status, error, token } = useAppSelector((state: RootState) => state.auth);

    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    useEffect(() => {
        if (token) {
            navigate('/');
        }
    }, [token, navigate]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (isLogin) {
            dispatch(loginUser({ email, password }));
        } else {
            // For register, we might want to login automatically or show success
            await dispatch(registerUser({ email, password }));
            // If register success, switch to login or auto login (depends on API)
            // Assuming register just creates user
            if (status === 'succeeded' || status === 'idle') {
                setIsLogin(true);
                alert('Registration successful! Please login.');
            }
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="login-header">
                    <h2>{isLogin ? 'Welcome Back' : 'Create Account'}</h2>
                    <p>{isLogin ? 'Enter your credentials to access the dashboard' : 'Sign up to start tracking markets'}</p>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-group">
                        <label>Email</label>
                        <input 
                            type="email" 
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required 
                            placeholder="name@company.com"
                        />
                    </div>
                    
                    <div className="form-group">
                        <label>Password</label>
                        <input 
                            type="password" 
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required 
                            placeholder="••••••••"
                        />
                    </div>

                    {error && <div className="error-message">{error}</div>}

                    <button type="submit" className="submit-button" disabled={status === 'loading'}>
                        {status === 'loading' ? 'Processing...' : (isLogin ? 'Sign In' : 'Sign Up')}
                    </button>
                </form>

                <div className="login-footer">
                    <p>
                        {isLogin ? "Don't have an account?" : "Already have an account?"}
                        <button 
                            className="toggle-button" 
                            onClick={() => setIsLogin(!isLogin)}
                        >
                            {isLogin ? 'Sign Up' : 'Sign In'}
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
