import React from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { Box } from '@mui/material';
import Sidebar from './Sidebar.tsx';
import TravelGame from '../pages/TravelGame.tsx';
import Flashcards from '../pages/Flashcards.tsx';

const Layout = () => {
  // const location = useLocation();

  return (
    <>
      <Sidebar />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          bgcolor: 'background.default',
          minHeight: '100vh',
        }}
      >
        <Routes>
          <Route path="/" element={<TravelGame />} />
          <Route path="/travel-game" element={<TravelGame />} />
          <Route path="/flashcards" element={<Flashcards />} />
        </Routes>
      </Box>
    </>
  );
};

export default Layout; 