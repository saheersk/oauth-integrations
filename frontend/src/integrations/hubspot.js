// hubspot.js

import { useState, useEffect } from 'react';
import { Box, Button, CircularProgress } from '@mui/material';
import axios from 'axios';

export const HubSpotIntegration = ({
  user,
  org,
  integrationParams,
  setIntegrationParams,
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  const handleConnectClick = async () => {
    try {
      setIsConnecting(true);
      const formData = new FormData();
      formData.append('user_id', user);
      formData.append('org_id', org);
      const response = await axios.post(
        `http://localhost:8000/integrations/hubspot/authorize`,
        formData
      );
      const authURL = response?.data;

      const newWindow = window.open(
        authURL,
        'HubSpot Authorization',
        'width=600, height=600'
      );

      const pollTimer = window.setInterval(() => {
        if (newWindow?.closed !== false) {
          window.clearInterval(pollTimer);
          handleWindowClosed();
        }
      }, 200);
    } catch (e) {
      setIsConnecting(false);
      alert(
        e?.response?.data?.detail || 'Failed to start HubSpot authorization.'
      );
    }
  };

  const handleRefreshTokenClick = async () => {
    try {
      setIsConnecting(true); 
      const formData = new FormData();
      formData.append('user_id', user);
      formData.append('org_id', org);

      const response = await axios.post(
        `http://localhost:8000/integrations/hubspot/refresh_token`,
        formData
      );
      const newAccessToken = response?.data?.access_token;

      console.log(integrationParams, 'before=================');

      if (newAccessToken) {
        alert('Access token refreshed successfully!');
        setIntegrationParams((prev) => ({
          ...prev,
          credentials: {
            ...prev.credentials,
            access_token: newAccessToken,
          },
        }));
        console.log(integrationParams, 'after=================');
      }
      setIsConnecting(false);
    } catch (e) {
      setIsConnecting(false);
      alert(
        e?.response?.data?.detail || 'Failed to refresh HubSpot access token.'
      );
    }
  };

  const handleWindowClosed = async () => {
    try {
      const formData = new FormData();
      formData.append('user_id', user);
      formData.append('org_id', org);
      const response = await axios.post(
        `http://localhost:8000/integrations/hubspot/credentials`,
        formData
      );
      const credentials = response.data;
      if (credentials) {
        setIsConnecting(false);
        setIsConnected(true);
        setIntegrationParams((prev) => ({
          ...prev,
          credentials: credentials,
          type: 'HubSpot',
        }));
      }
    } catch (e) {
      setIsConnecting(false);
      alert(
        e?.response?.data?.detail || 'Failed to retrieve HubSpot credentials.'
      );
    }
  };

  useEffect(() => {
    setIsConnected(integrationParams?.credentials ? true : false);
  }, [integrationParams]);

  return (
    <>
      <Box sx={{ mt: 2 }}>
        Parameters
        <Box
          display="flex"
          alignItems="center"
          justifyContent="center"
          sx={{ mt: 2 }}
        >
          <Button
            variant="contained"
            onClick={isConnected ? () => {} : handleConnectClick}
            color={isConnected ? 'success' : 'primary'}
            disabled={isConnecting}
            style={{
              pointerEvents: isConnected ? 'none' : 'auto',
              cursor: isConnected ? 'default' : 'pointer',
              opacity: isConnected ? 1 : undefined,
            }}
          >
            {isConnected ? (
              'HubSpot Connected'
            ) : isConnecting ? (
              <CircularProgress size={20} />
            ) : (
              'Connect to HubSpot'
            )}
          </Button>
        </Box>
        <Box
          display="flex"
          alignItems="center"
          justifyContent="center"
          sx={{ mt: 2 }}
        >
          <Button
            variant="contained"
            onClick={handleRefreshTokenClick}
            color="secondary"
            disabled={isConnecting || !isConnected}
          >
            {isConnecting ? (
              <CircularProgress size={20} />
            ) : (
              'Refresh HubSpot Token'
            )}
          </Button>
        </Box>
      </Box>
    </>
  );
};
