import React from "react";
import { createRoot } from "react-dom/client";
import SocDashboard from "../mini-soc-dashboard.jsx";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <SocDashboard />
  </React.StrictMode>,
);
