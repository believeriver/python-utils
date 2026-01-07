import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAppSelector } from './app/hooks';
import StockDashboard from './components/StockDashboard';
import LoginPage from './components/LoginPage';
import './App.css';
import type { RootState } from './app/store';

const ProtectedRoute = ({ children }: { children: React.ReactElement }) => {
    const { token } = useAppSelector((state: RootState) => state.auth);
    if (!token) {
        return <Navigate to="/login" replace />;
    }
    return children;
};

const App: React.FC = () => {
    return (
        <Router>
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route 
                    path="/" 
                    element={
                        <ProtectedRoute>
                            <StockDashboard />
                        </ProtectedRoute>
                    } 
                />
            </Routes>
        </Router>
    );
};

export default App;
