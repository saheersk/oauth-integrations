import { useState } from 'react';
import {
    Box,
    TextField,
    Button,
} from '@mui/material';
import axios from 'axios';

const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'HubSpot': 'hubspot', 
};

export const DataForm = ({ integrationType, credentials, userId }) => {
    const [loadedData, setLoadedData] = useState(null);
    const endpoint = endpointMapping[integrationType];

    const handleLoad = async () => {
        if (!endpoint) {
            alert('Unsupported integration type');
            return;
        }

        try {
            const formData = new FormData();

            const credentialsWithUser = { ...credentials, user_id: userId };
            formData.append('credentials', JSON.stringify(credentialsWithUser));


            // Make API request to the corresponding endpoint
            const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/load`, formData);
            
            if (response.status === 429) {
                alert('Rate limit exceeded. Please try again later.');
                return;
            }

            const data = JSON.stringify(response.data);
            setLoadedData(data);
        } catch (e) {
            alert(e?.response?.data?.detail || 'Error loading data');
        }
    };
    
    
    return (
        <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' width='100%'>
            <Box display='flex' flexDirection='column' width='100%'>
                <TextField
                    label="Loaded Data"
                    value={loadedData || ''}
                    sx={{ mt: 2 }}
                    InputLabelProps={{ shrink: true }}
                    multiline
                    rows={6}
                    disabled
                />
                <Button
                    onClick={handleLoad}
                    sx={{ mt: 2 }}
                    variant='contained'
                >
                    Load Data
                </Button>
                <Button
                    onClick={() => setLoadedData(null)}
                    sx={{ mt: 1 }}
                    variant='contained'
                >
                    Clear Data
                </Button>
            </Box>
        </Box>
    );
};
