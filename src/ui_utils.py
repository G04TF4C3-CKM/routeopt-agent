"""Utility helpers for runtime and route-time handling in the Streamlit UI.

The backend optimizer works with a single numeric ``time_limit`` value that is
interpreted in the same units as the scenario's computed route times. Because the
raw scenario files do not encode a physical unit, the UI asks the user to
explicitly state the *data* unit and the *input* unit for the driver‑time limit.
These helpers perform the necessary conversion and produce human‑readable
strings for display.
"""

from __future__ import annotations

import math
from typing import Literal

# Types for clarity – the UI restricts the choices to these exact strings.
DataUnit = Literal["Minutes", "Hours", "Abstract units"]
InputUnit = Literal["Same as data unit", "Minutes", "Hours"]


def format_runtime_seconds(runtime_seconds: float) -> str:
    """Format a finite, non-negative workflow runtime for concise display."""
    seconds = float(runtime_seconds)
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError("runtime_seconds must be finite and non-negative")

    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    if seconds < 60:
        return f"{seconds:.2f} s"

    minutes = int(seconds // 60)
    remaining_seconds = seconds - minutes * 60
    return f"{minutes}m {remaining_seconds:.2f}s"


def convert_time_limit_to_data_units(
    value: float, input_unit: InputUnit, data_unit: DataUnit
) -> float:
    """Convert a driver‑time limit entered by the user into the data's unit.

    Parameters
    ----------
    value:
        The numeric time limit entered by the user.
    input_unit:
        The unit the user *said* the entered value is in. ``"Same as data unit"``
        means no conversion.
    data_unit:
        The unit that the scenario's route‑time values are expressed in.

    Returns
    -------
    float
        The value expressed in ``data_unit``.

    Conversion rules
    ----------------
    * If ``data_unit`` is ``"Abstract units"`` no conversion is performed – the
      optimizer works with abstract numbers.
    * If ``input_unit`` is ``"Same as data unit"`` the function returns ``value``
      unchanged.
    * ``Minutes`` ↔ ``Hours`` conversion uses a factor of 60.
    """
    # Abstract units are opaque – treat the number as‑is.
    if data_unit == "Abstract units":
        return value

    if input_unit == "Same as data unit":
        return value

    # At this point both ``data_unit`` and ``input_unit`` are either Minutes or Hours.
    if input_unit == "Hours" and data_unit == "Minutes":
        return value * 60.0
    if input_unit == "Minutes" and data_unit == "Hours":
        return value / 60.0

    # Units already match (Minutes→Minutes or Hours→Hours).
    return value


def format_route_time(value: float, data_unit: DataUnit) -> str:
    """Return a nicely formatted string for a route‑time metric.

    * ``Minutes`` – show minutes with hours in parentheses for readability.
    * ``Hours`` – show hours.
    * ``Abstract units`` – show a generic ``units`` label.
    """
    if data_unit == "Minutes":
        hrs = value / 60.0
        return f"{value:.3f} min ({hrs:.3f} hr)"
    if data_unit == "Hours":
        return f"{value:.3f} hr"
    return f"{value:.3f} units"


def format_route_time_for_display(value: float, data_unit: DataUnit) -> str:
    """Return a route‑time string using a single display unit.

    * ``Minutes`` – convert to hours and label ``hr``.
    * ``Hours`` – keep hours, label ``hr``.
    * ``Abstract units`` – keep raw value, label ``units``.
    """
    if data_unit == "Minutes":
        hrs = value / 60.0
        return f"{hrs:.3f} hr"
    if data_unit == "Hours":
        return f"{value:.3f} hr"
    return f"{value:.3f} units"


def caption_for_data_unit(data_unit: DataUnit) -> str:
    """Return an explanatory caption for the selected data unit."""
    if data_unit == "Minutes":
        return (
            "Data is minute‑scaled. Solver uses minutes internally; "
            "displayed route-time metrics are shown in hours."
        )
    if data_unit == "Hours":
        return (
            "Data is hour‑scaled. Solver and displayed route‑time metrics use hours."
        )
    return (
        "Data uses abstract route‑time units. Solver and displayed metrics use abstract units."
    )
