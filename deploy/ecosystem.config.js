module.exports = {
  apps: [
    {
      name: "flexr-api",
      cwd: "/flexr/backend",
      script: "venv/bin/uvicorn",
      args: "app.main:app --host 127.0.0.1 --port 8000",
      interpreter: "none",
      env: {
        // .env wird von pydantic-settings automatisch aus backend/.env gelesen
      },
      autorestart: true,
      max_restarts: 10,
      watch: false,
    },
  ],
};
