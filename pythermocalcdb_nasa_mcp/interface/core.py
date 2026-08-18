# import libs
from __future__ import annotations

import logging
from typing import Any

from pythermodb_settings.models import Component

from pythermocalcdb_nasa import (
    H_T,
    S_T,
    G_T,
    Cp_T,
    dH_rxn_STD,
    dS_rxn_STD,
    dG_rxn_STD,
    Keq
)
# ! models

# ! tools
from pythermocalcdb_nasa_mcp.tools.model_source_builder import (
    build_model_source_from_reference,
)

# NOTE: set up logger for this module
logger = logging.getLogger(__name__)

# SECTION: Calculate enthalpy at temperature T


def calc_H_T():
    pass

# SECTION: Calculate entropy at temperature T


def calc_S_T():
    pass

# SECTION: Calculate Gibbs free energy at temperature T


def calc_G_T():
    pass

# SECTION: Calculate heat capacity at temperature T


def calc_Cp_T():
    pass

# SECTION: Calculate standard enthalpy change of reaction


def calc_dH_rxn_STD():
    pass

# SECTION: Calculate standard entropy change of reaction


def calc_dS_rxn_STD():
    pass

# SECTION: Calculate standard Gibbs free energy change of reaction


def calc_dG_rxn_STD():
    pass

# SECTION: Calculate equilibrium constant at temperature T


def calc_Keq():
    pass
