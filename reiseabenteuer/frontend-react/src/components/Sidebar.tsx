import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography,
  Box,
  useTheme,
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import ExploreIcon from '@mui/icons-material/Explore';
import StyleIcon from '@mui/icons-material/Style';

const DRAWER_WIDTH = 240;

const Sidebar = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      text: 'Reisenspiel',
      icon: <ExploreIcon />,
      path: '/travel-game',
    },
    {
      text: 'Karteikarten',
      icon: <StyleIcon />,
      path: '/flashcards',
    },
  ];

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          bgcolor: 'background.paper',
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" color="primary">
          Reiseabenteuer
        </Typography>
      </Box>
      
      <List>
        {menuItems.map((item) => (
          <ListItem
            button
            key={item.text}
            onClick={() => navigate(item.path)}
            sx={{
              bgcolor: location.pathname === item.path ? 'action.selected' : null,
              '&:hover': {
                bgcolor: 'action.hover',
              },
            }}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
};

export default Sidebar; 