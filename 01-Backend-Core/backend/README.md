---
title: ChemSearch API
emoji: 🧪
colorFrom: gray
colorTo: green
sdk: docker
app_port: 8000
fullWidth: true
short_description: RDKit reaction simulation and ReactionT5 product prediction API
---

# ChemSearch API

FastAPI backend for ChemSearch. It provides PubChem molecule search, RDKit molecule rendering and deterministic reaction rules, plus optional ReactionT5 product prediction.

- Interactive API documentation: `/docs`
- Health check: `/health`
- Container port: `8000`

The first ReactionT5 request downloads the model and can take several minutes on CPU. Deterministic simulation and molecule rendering remain available without loading the ML model.
