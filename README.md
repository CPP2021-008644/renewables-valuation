# <img    src="https://afs-services.com/wp-content/uploads/2025/07/renewable_valuation_resized.png"    alt="Renewables Valuation Logo"    height="80"  >  Renewables Valuation

This repository provides tools for valuation of renewable energy projects using DCF methodologies. It enables creation, analysis, and comparison of different technology projects (solar PV, offshore wind, green hydrogen, etc.) through an extensible `Project` class, predefined archetypes, and sensitivity/visualization utilities.

## Project Overview

The goal of this project is to offer a flexible Python library and example notebooks to model cash flows, compute financial metrics (NPV, IRR, LCOE), and run sensitivity analyses for renewable energy initiatives, putting special emphasis on clean hydrogen projects. The core logic resides in the `Project` class (in `renewablesValuation.py`), while example workflows and case studies are provided in the Jupyter notebooks.

## Repository Structure

### Core Library

- **`renewablesValuation.py`**: Defines the `Project` and `MainProduct` classes, methods for managing cash flows, and functions for NPV, IRR, and cash flow aggregation.  
- **`valuation_dcf.py`**: Auxiliary DCF tools, inflow/outflow generation and helper functions.  
- **`hydrogen_analysis.py`**: Implements the `HydrogenProject` archetype, sensitivity analysis routines (`run_sensitivity`), and plotting functions (`plot_spider_chart`, `plot_surface_plot`).  


### Notebooks (Examples and Case Studies)

- **`Code examples - The basic building blocks.ipynb`**: Demonstrates fundamental usage of the `Project` class.  
- **`Code examples - The standard valuation tables.ipynb`**: Shows generation of standard valuation tables and summaries.  
- **`python CF Analysis.ipynb`**: Case studies for solar PV, offshore wind, and green hydrogen, including cash flow generation and metric calculation.
- **`wind_example/wind_plant_exercise.ipynb`**: Project valuation exercise, including cash flow generation from energy simulation results.

### Diagrams and Resources

- **`buildingblockshierarchy.drawio`**: Draw.io diagram illustrating the class and module relationships.

## Acknowledgements

This work has been supported by the Government of Spain (Ministerio de Ciencia e Innovación) and the European Union through Project CPP2021-008644 / AEI / 10.13039/501100011033 / Unión Europea Next GenerationEU / PRTR. Visit our website for more information [Green and Digital Finance – Next GenerationEU](https://afs-services.com/proyectos-nextgen-eu/).


<p align="center">
  <img
    src="https://afs-services.com/wp-content/uploads/2025/06/logomciaienetgeneration-1232x264.png"
    alt="Logo MCIAI NetGeneration"
    height="100"
  >
</p>
