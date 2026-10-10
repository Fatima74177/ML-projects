import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

if (localStorage.getItem("eef_theme") === "light") {
  document.documentElement.dataset.theme = "light";
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
