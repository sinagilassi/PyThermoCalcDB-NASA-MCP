# import libs
from __future__ import annotations

import logging
from typing import Any

from pythermodb_settings.models import Component

# ! models

# ! tools
from pythermocalcdb_nasa_mcp.tools.model_source_builder import (
    build_model_source_from_reference,
)

# NOTE: set up logger for this module
logger = logging.getLogger(__name__)

# SECTION:
# | Calculation | Temperature | Reference range needed |
# | --- | --- | --- |
# | `H_T(CO2)` | `300 K` | `NASA9-1`, 200-1000 K |
# | `S_T(CH4)` | `400 K` | `NASA9-1`, 200-1000 K |
# | `G_T(CO2)` | `500 K` | `NASA9-1`, 200-1000 K |
# | `Cp_T(CH4)` | `600 K` | `NASA9-1`, 200-1000 K |
# | `dH_rxn_STD(WGS)` | `398.15 K` | `NASA9-1`, 200-1000 K for CO, H2O, CO2, H2 |
# | `dS_rxn_STD(WGS)` | `398.15 K` | `NASA9-1`, 200-1000 K for CO, H2O, CO2, H2 |
# | `dG_rxn_STD(WGS)` | `398.15 K` | `NASA9-1`, 200-1000 K for CO, H2O, CO2, H2 |
# | `Keq(WGS)` | `1000 K` | `NASA9-1`, 200-1000 K for CO, H2O, CO2, H2 |
