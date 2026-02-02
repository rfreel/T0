# Manufacturing Supply Chain Generalist: High-Taste Repos

A curated set of open-source manufacturing and supply chain projects worth cloning to study architecture, domain modeling, and production-grade problem solving.

## Primary contenders

1. **frePPLe/frepple** (Python)
   - Advanced planning & scheduling (APS) plus demand forecasting for manufacturing.
   - Why high taste: clear separation of concerns, clean solver integration, thoughtful UI/UX, and production-grade modeling for constraints (capacity, materials, lead times).
   - Great for studying: realistic manufacturing planning logic without over-engineering.
   - Clone:
     ```bash
     git clone https://github.com/frePPLe/frepple.git
     ```

2. **openboxes/openboxes** (Groovy/Grails + modern frontend)
   - Full supply chain + inventory management system with strong warehouse workflows.
   - Why high taste: robust domain modeling (lots, expirations, traceability, multi-location), clean service layers, and pragmatic extensibility.
   - Great for studying: enterprise inventory flows, lot/serial tracking, stock movements.
   - Clone:
     ```bash
     git clone https://github.com/openboxes/openboxes.git
     ```

3. **msupply-foundation/open-msupply** (TypeScript + Rust backend)
   - Open-source evolution of the long-standing mSupply LMIS, built for public health supply chains but broadly applicable.
   - Why high taste: battle-tested in dozens of countries; careful modernization, offline-first mobile support, and strong auditability.
   - Clone:
     ```bash
     git clone https://github.com/msupply-foundation/open-msupply.git
     ```

4. **xtuple/xtuple** (JavaScript + PostgreSQL)
   - Open-source ERP/CRM with strong manufacturing modules (job shop, assemble-to-order).
   - Why high taste: expressive domain modeling for BOMs, routings, and work orders; integrated accounting without ERP bloat.
   - Clone:
     ```bash
     git clone https://github.com/xtuple/xtuple.git
     ```

## Notable mentions

- **Part-DB/Part-DB-server** (PHP/Symfony)
  - Clean inventory system for electronic components with elegant entity design.
  - Clone:
    ```bash
    git clone https://github.com/Part-DB/Part-DB-server.git
    ```

- **fleetbase/fleetbase**
  - Logistics and fleet operations platform; good reference for microservice architecture in logistics domains.
  - Clone:
    ```bash
    git clone https://github.com/fleetbase/fleetbase.git
    ```

- **dalton/awesome-supply-chain**
  - Curated list of supply chain resources (not code, but a good discovery hub).
  - Clone:
    ```bash
    git clone https://github.com/dalton/awesome-supply-chain.git
    ```

## Notes

- Supply chain code taste often prioritizes correctness, traceability, and performance over minimalism.
- If you need a narrower focus (optimization solvers, healthcare, inventory simulation, etc.), update this list with your target domain and stack.
