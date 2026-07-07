# Project Structure

```text
order-ops-dashboard/
  backend/
    app/
      models/        SQLAlchemy models
      routes/        Flask API blueprints
      config.py      Backend configuration
      extensions.py  Flask extensions
      __init__.py    App factory and blueprint registration
    data/            Local source datasets, ignored by git
    scripts/         Import and database maintenance scripts
    requirements.txt Python dependencies
    run.py           Backend entry point
  frontend/
    public/          Static public assets
    src/
      api/           Axios request wrapper
      views/         Vue pages
      App.vue        Main layout and navigation
      main.js        Vue entry
    package.json     Frontend dependencies and scripts
```

Runtime caches, local virtual environments, `node_modules`, build output, logs, and large raw datasets are ignored by the root `.gitignore`.
