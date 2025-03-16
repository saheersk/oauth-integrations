import { useState } from "react";
import {
  Box,
  Autocomplete,
  TextField,
  Typography,
  Paper,
  Button,
} from "@mui/material";
import { AirtableIntegration } from "./integrations/airtable";
import { NotionIntegration } from "./integrations/notion";
import { HubSpotIntegration } from "./integrations/hubspot";
import { DataForm } from "./data-form";

const integrationMapping = {
  Notion: NotionIntegration,
  Airtable: AirtableIntegration,
  HubSpot: HubSpotIntegration,
};

export const IntegrationForm = () => {
  const [integrationParams, setIntegrationParams] = useState({});
  const [user, setUser] = useState("TestUser");
  const [org, setOrg] = useState("TestOrg");
  const [currType, setCurrType] = useState(null);
  const CurrIntegration = integrationMapping[currType];

  const handleRemoveToken = () => {
    setIntegrationParams({});
    setCurrType(null);
  };

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      flexDirection="column"
      sx={{
        width: "100wh",
        minHeight: "100vh",
        backgroundColor: "#f5f5f5",
        padding: 2,
      }}
    >
      <Paper
        sx={{
          padding: 4,
          width: "100%",
          maxWidth: 800,
          borderRadius: 2,
          boxShadow: 3,
          backgroundColor: "#fff",
        }}
      >
        <Typography
          variant="h6"
          sx={{ mb: 2, textAlign: "center", color: "#333" }}
        >
          Integration Setup
        </Typography>

        <Box display="flex" flexDirection="column" gap={2}>
          <TextField
            label="User"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            sx={{ width: "100%" }}
            variant="outlined"
          />
          <TextField
            label="Organization"
            value={org}
            onChange={(e) => setOrg(e.target.value)}
            sx={{ width: "100%" }}
            variant="outlined"
          />
          <Autocomplete
            id="integration-type"
            options={Object.keys(integrationMapping)}
            sx={{ width: "100%" }}
            renderInput={(params) => (
              <TextField
                {...params}
                label="Integration Type"
                variant="outlined"
              />
            )}
            onChange={(e, value) => setCurrType(value)}
          />
        </Box>
        {currType && (
          <Box sx={{ mt: 4 }}>
            <CurrIntegration
              user={user}
              org={org}
              integrationParams={integrationParams}
              setIntegrationParams={setIntegrationParams}
            />
          </Box>
        )}
        {integrationParams?.credentials && (
          <Box sx={{ mt: 2, display: "flex", justifyContent: "center" }}>
            <Button
              variant="outlined"
              color="warning"
              onClick={handleRemoveToken}
              sx={{ width: "50%" }}
            >
              Logout
            </Button>
          </Box>
        )}
        {integrationParams?.credentials && (
          <Box sx={{ mt: 4 }}>
            <DataForm
              integrationType={integrationParams?.type}
              credentials={integrationParams?.credentials}
              userId={user}
            />
          </Box>
        )}
      </Paper>
    </Box>
  );
};
