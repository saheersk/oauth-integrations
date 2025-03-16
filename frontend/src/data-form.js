import { useState } from "react";
import {
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
} from "@mui/material";
import axios from "axios";

const endpointMapping = {
  Notion: "notion",
  Airtable: "airtable",
  HubSpot: "hubspot",
};

export const DataForm = ({ integrationType, credentials, userId }) => {
  const [loadedData, setLoadedData] = useState(null);
  const [loading, setLoading] = useState(false); // New state for loading
  const endpoint = endpointMapping[integrationType];

  const handleLoad = async () => {
    if (!endpoint) {
      alert("Unsupported integration type");
      return;
    }

    setLoading(true); // Start loading

    try {
      const formData = new FormData();

      const credentialsWithUser = { ...credentials, user_id: userId, org_id: 'TestOrg' };
      formData.append("credentials", JSON.stringify(credentialsWithUser));

      // Make API request to the corresponding endpoint
      const response = await axios.post(
        `http://localhost:8000/integrations/${endpoint}/load`,
        formData
      );

      if (response.status === 429) {
        alert("Rate limit exceeded. Please try again later.");
        return;
      }

      setLoadedData(response.data);
      console.log(response.data, "hubspot data")
    } catch (e) {
      console.log(e, "===e====")
      alert(e?.response?.data || "Error loading data");
    } finally {
      setLoading(false);
    }
  };

  const renderTable = () => {
    if (!loadedData) return <p>There is no data</p>;

    const keys = Object.keys(loadedData[0]?.properties || {});

    if (keys.length > 0) {
      return (
        <Box sx={{ maxHeight: "200px", overflowY: "auto", overflowX: "auto" }}>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  {keys.map((key, index) => (
                    <TableCell key={index}>{key}</TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {loadedData.map((row, rowIndex) => (
                  <TableRow key={rowIndex}>
                    {keys.map((key, colIndex) => (
                      <TableCell key={colIndex}>
                        {row.properties[key]}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      );
    } else {
      return (
        <Box
          sx={{
            maxHeight: "200px",
            overflowY: "auto",
            overflowX: "auto",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          <pre>{JSON.stringify(loadedData, null, 2)}</pre>
        </Box>
      );
    }
  };

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      flexDirection="column"
      width="100%"
    >
      <Box width="100%">
        {renderTable()}
        <Box display="flex" flexDirection="column" width="100%">
          <Button
            onClick={handleLoad}
            sx={{
              mt: 2,
              minWidth: "200px",
              padding: "10px",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
            }}
            variant="contained"
            disabled={loading}
          >
            {loading ? (
              <CircularProgress size={24} sx={{ marginRight: "10px" }} />
            ) : (
              "Load Data"
            )}
          </Button>
          <Button
            onClick={() => setLoadedData(null)}
            sx={{ mt: 1, minWidth: "200px", padding: "10px" }}
            variant="contained"
          >
            Clear Data
          </Button>
        </Box>
      </Box>
    </Box>
  );
};
