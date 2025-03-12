import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { Box, CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import Layout from './components/Layout.tsx';

// Create a theme with German-inspired colors
const theme = createTheme({
  palette: {
    primary: {
      main: '#1a237e', // Dark blue
    },
    secondary: {
      main: '#c62828', // Dark red
    },
    background: {
      default: '#f5f5f5',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>
          <Layout />
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App; 