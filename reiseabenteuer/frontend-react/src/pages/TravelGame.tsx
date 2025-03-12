import React, { useState } from 'react';
import { 
  Typography, 
  Box, 
  Checkbox, 
  FormControlLabel, 
  Button, 
  TextField,
  FormGroup,
  Switch,
  Paper,
  CircularProgress,
  Divider,
  List,
  ListItem
} from '@mui/material';
import axios from 'axios';

interface Destination {
  destination_name: string;
  state: string;
}

const TravelGame = () => {
  const [selectedActivities, setSelectedActivities] = useState<string[]>([]);
  const [customActivity, setCustomActivity] = useState('');
  const [isCustomActivitySelected, setIsCustomActivitySelected] = useState(false);
  const [isGerman, setIsGerman] = useState(false);
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const activities = {
    en: [
      'Outdoor activities',
      'Site seeing',
      'Historical landmarks',
      'Archaeological landmarks',
      'Museums',
      'Local culture',
      'Nature sites'
    ],
    de: [
      'Outdoor-Aktivitäten',
      'Besichtigungen',
      'Historische Wahrzeichen',
      'Archäologische Wahrzeichen',
      'Museen',
      'Lokale Kultur',
      'Naturstätten'
    ]
  };

  const handleActivityChange = (activity: string) => {
    setSelectedActivities(prev => {
      if (prev.includes(activity)) {
        return prev.filter(a => a !== activity);
      }
      const totalSelected = prev.length + (isCustomActivitySelected ? 1 : 0);
      if (totalSelected < 3) {
        return [...prev, activity];
      }
      return prev;
    });
  };

  const handleCustomActivityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCustomActivity(e.target.value);
  };

  const handleCustomActivitySelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const isChecked = e.target.checked;
    setIsCustomActivitySelected(isChecked);
    if (!isChecked && selectedActivities.length >= 3) {
      // If unchecking and already at limit, don't allow
      e.preventDefault();
      return;
    }
  };

  const handleClear = () => {
    setSelectedActivities([]);
    setCustomActivity('');
    setIsCustomActivitySelected(false);
    setDestinations([]);
  };

  const handleSubmit = async () => {
    try {
      setIsLoading(true);
      const activitiesList = [
        ...selectedActivities.map(activity => activity.toLowerCase()),
        ...(isCustomActivitySelected && customActivity ? [customActivity.toLowerCase()] : [])
      ];

      console.log('Sending request with activities:', activitiesList);
      const response = await axios.post('http://localhost:8000/destinations', {
        activities: activitiesList.slice(0, 3)
      });
      console.log('Received response:', response.data);
      setDestinations(response.data);
    } catch (error) {
      console.error('Error fetching destinations:', error);
      if (axios.isAxiosError(error)) {
        console.error('Response data:', error.response?.data);
        console.error('Response status:', error.response?.status);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Box sx={{ display: 'flex', gap: 3 }}>
        {/* Left column - Activities selection */}
        <Box sx={{ width: '400px' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h4" gutterBottom>
              {isGerman ? 'Reisenspiel' : 'Travel Game'}
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={isGerman}
                  onChange={(e) => setIsGerman(e.target.checked)}
                />
              }
              label={isGerman ? 'Deutsch' : 'English'}
            />
          </Box>

          <Typography variant="h6" gutterBottom>
            {isGerman 
              ? 'Wählen Sie bis zu 3 Aktivitäten aus:'
              : 'Select up to 3 activities:'}
          </Typography>

          <Paper sx={{ p: 2, mb: 3 }}>
            <FormGroup>
              {activities[isGerman ? 'de' : 'en'].map((activity) => (
                <FormControlLabel
                  key={activity}
                  control={
                    <Checkbox
                      checked={selectedActivities.includes(activity)}
                      onChange={() => handleActivityChange(activity)}
                      disabled={
                        selectedActivities.length + (isCustomActivitySelected ? 1 : 0) >= 3 && 
                        !selectedActivities.includes(activity)
                      }
                    />
                  }
                  label={activity}
                />
              ))}
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mt: 2 }}>
                <Checkbox
                  checked={isCustomActivitySelected}
                  onChange={handleCustomActivitySelect}
                  disabled={
                    !customActivity || 
                    (selectedActivities.length >= 3 && !isCustomActivitySelected)
                  }
                />
                <TextField
                  fullWidth
                  margin="normal"
                  label={isGerman ? 'Eigene Aktivität' : 'Custom Activity'}
                  value={customActivity}
                  onChange={handleCustomActivityChange}
                  sx={{ mt: 0 }}
                  error={isCustomActivitySelected && !customActivity}
                  helperText={
                    isCustomActivitySelected && !customActivity
                      ? (isGerman 
                          ? 'Bitte geben Sie eine Aktivität ein'
                          : 'Please enter an activity')
                      : ''
                  }
                />
              </Box>
            </FormGroup>
          </Paper>

          <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <Button variant="outlined" onClick={handleClear}>
              {isGerman ? 'Zurücksetzen' : 'Clear'}
            </Button>
            <Button 
              variant="contained" 
              onClick={handleSubmit}
              disabled={selectedActivities.length === 0 && !customActivity || isLoading}
            >
              {isGerman ? 'Absenden' : 'Submit'}
            </Button>
          </Box>
        </Box>

        {/* Right column - Results */}
        <Box sx={{ flex: 1 }}>
          <Paper sx={{ p: 2, minHeight: '400px', position: 'relative' }}>
            <Typography variant="h6" gutterBottom>
              {isGerman ? 'Reiseziele:' : 'Destinations:'}
            </Typography>
            
            {isLoading ? (
              <Box sx={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center',
                height: '300px'
              }}>
                <CircularProgress />
                <Typography sx={{ ml: 2 }}>
                  {isGerman ? 'Suche läuft...' : 'Searching...'}
                </Typography>
              </Box>
            ) : destinations.length > 0 ? (
              <List sx={{ width: '100%' }}>
                {destinations.map((dest, index) => (
                  <React.Fragment key={index}>
                    <ListItem sx={{ 
                      py: 1,
                      px: 2,
                      '&:hover': {
                        backgroundColor: 'rgba(0, 0, 0, 0.04)'
                      }
                    }}>
                      <Typography>
                        {dest.destination_name}, {dest.state}
                      </Typography>
                    </ListItem>
                    {index < destinations.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            ) : (
              <Typography sx={{ textAlign: 'center', color: 'text.secondary', mt: 4 }}>
                {isGerman 
                  ? 'Wählen Sie Aktivitäten aus und klicken Sie auf "Absenden"'
                  : 'Select activities and click "Submit"'}
              </Typography>
            )}
          </Paper>
        </Box>
      </Box>
    </Box>
  );
};

export default TravelGame; 