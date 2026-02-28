const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");

const app = express();

const PORT = 8080;
const BACKEND_URL = "http://localhost:8000";
const FRONTEND_URL = "http://localhost:3000";

// Health do proxy
app.get("/proxy-health", (_, res) => {
  res.json({ status: "ok", service: "proxy" });
});

// Backend API
app.use("/api", createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
}));

app.use(["/docs", "/health", "/openapi.json"], createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
}));

// Frontend (sempre por último)
app.use("/", createProxyMiddleware({
  target: FRONTEND_URL,
  changeOrigin: true,
  ws: true,
}));

app.listen(PORT, "0.0.0.0", () => {
  console.log(`Proxy rodando em http://localhost:${PORT}`);
  console.log(`ngrok http ${PORT}`);
});
