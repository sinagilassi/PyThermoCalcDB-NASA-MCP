# import libs
import logging
from typing import Any, Dict
from pyThermoDB.references import (
    check_custom_reference
)


# NOTE: logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SECTION: Check reference content


def check_yaml_reference(
        yaml_content: str,
) -> bool:
    """
    Check if the YAML content can be used as a reference in pyThermoDB.

    Parameters
    ----------
    yaml_content : str
        The YAML content to be checked as a reference.

    Returns
    -------
    bool
        True if the YAML content can be used as a reference. False otherwise.
    """
    try:
        # NOTE: custom ref
        custom_reference: Dict[str, Any] = {'reference': [yaml_content]}

        # NOTE: check custom reference
        if not check_custom_reference(custom_reference):
            logger.error("The YAML content cannot be used as a reference.")
            return False

        return True
    except Exception as e:
        logger.error(
            f"An error occurred while checking the YAML reference: {e}")
        return False
