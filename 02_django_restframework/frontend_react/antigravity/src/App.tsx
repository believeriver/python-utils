import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import StockDashboard from './components/StockDashboard';
import LoginPage from './components/LoginPage';
import './App.css';

const App: React.FC = () => {
    return (
        <Router>
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route 
                    path="/" 
                    element={<StockDashboard />} 
                />
            </Routes>
        </Router>
    );
};

export default App;
