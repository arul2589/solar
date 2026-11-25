"""Plain data types for the calculation engine.

Nothing in this package talks to a database or the web. Every number that is a
rate, price, tax, yield or design assumption arrives through `CalcSettings` (or the
catalogue / rate tables passed in) so it can be set per installer.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class PanelSpec:
    model: str
    wp: float                      # rated power at STC (W)
    voc: float                     # open-circuit voltage (V)
    vmp: float                     # max-power voltage (V)
    isc: float                     # short-circuit current (A)
    imp: float                     # max-power current (A)
    temp_coeff_voc_pct: float      # %/degC (negative, e.g. -0.26)
    temp_coeff_pmax_pct: float     # %/degC (negative, e.g. -0.30); used for Vmp
    length_mm: float
    width_mm: float
    price: Optional[Decimal] = None
    id: Optional[int] = None


@dataclass(frozen=True)
class InverterSpec:
    model: str
    ac_kw: float                   # rated AC output (kW)
    phase: int                     # 1 or 3
    max_dc_voltage: float          # absolute max DC input voltage (V)
    mppt_min_v: float              # full-load MPPT range, lower bound (V)
    mppt_max_v: float              # full-load MPPT range, upper bound (V)
    num_mppt: int
    max_input_current_per_mppt: float   # A
    ac_max_current: float          # A (per phase)
    kind: str = "on_grid"          # on_grid | hybrid | off_grid
    battery_voltage: Optional[float] = None
    price: Optional[Decimal] = None
    id: Optional[int] = None


@dataclass(frozen=True)
class NetworkRate:
    effective_from: date
    rate: Decimal                  # Rs per generated unit


@dataclass(frozen=True)
class TariffSlab:
    """Telescopic slab per billing cycle. `upto` is the cumulative upper bound
    (units in the billing cycle); None means 'and above'."""
    upto: Optional[int]
    rate: Decimal


@dataclass
class CalcSettings:
    # --- yield -------------------------------------------------------------
    cuf_tnerc: float = 0.21                     # TNERC CUF, network charges only
    realistic_yield_low: float = 3.8            # kWh/kW/day, customer estimates (VERIFY)
    realistic_yield_high: float = 4.4           # kWh/kW/day (VERIFY)
    days_per_month: float = 30.0
    sizing_yield_basis: str = "realistic_mid"   # realistic_mid | realistic_low | cuf
    nominal_kw_rounding: str = "floor"          # floor | round  ("sold as" kW label)
    # --- roof ----------------------------------------------------------------
    roof_min_m2_per_kw: float = 7.5
    roof_recommended_m2_per_kw: float = 9.5
    tilt_deg: float = 12.0
    design_sun_elevation_deg: float = 30.0      # for inter-row shadow spacing
    edge_clearance_m: float = 0.3
    min_row_gap_m: float = 0.3
    panel_side_gap_m: float = 0.02
    usable_roof_fraction: float = 0.85          # when only an area (no dims) is given
    # --- electrical design ----------------------------------------------------
    design_min_cell_temp_c: float = 10.0
    design_max_cell_temp_c: float = 70.0
    dc_ac_ratio_min: float = 1.0
    dc_ac_ratio_max: float = 1.3
    single_phase_max_kw: float = 5.0            # above this on 3-phase supply prefer 3-ph inverter
    current_safety_factor: float = 1.25
    dc_vdrop_max_pct: float = 1.5
    ac_vdrop_max_pct: float = 2.0
    copper_resistivity: float = 0.0178          # ohm*mm2/m at ~20C
    ac_voltage_1ph: float = 230.0
    ac_voltage_3ph: float = 415.0
    dc_cable_sizes_mm2: tuple = (4.0, 6.0, 10.0)
    ac_cable_sizes_mm2: tuple = (2.5, 4.0, 6.0, 10.0, 16.0, 25.0)
    dc_cable_ampacity: dict = field(default_factory=lambda: {4.0: 55, 6.0: 70, 10.0: 98})
    ac_cable_ampacity: dict = field(default_factory=lambda: {2.5: 24, 4.0: 32, 6.0: 41, 10.0: 57, 16.0: 76, 25.0: 101})
    standard_breaker_ratings_a: tuple = (6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125)
    dc_fuse_ratings_a: tuple = (10, 12, 15, 16, 20, 25, 32)
    dc_device_voltage_classes: tuple = (500, 600, 1000, 1100)
    dc_run_one_way_m: float = 15.0              # array to DCDB, one way, default
    dcdb_to_inverter_m: float = 1.0
    inverter_to_acdb_m: float = 1.0
    ac_run_m: float = 15.0                      # ACDB to main panel / net meter, default
    earth_conductor_mm2: float = 4.0
    la_conductor_mm2: float = 16.0
    earthing_pits_min: int = 2
    earth_resistance_target_ohm: float = 5.0
    lightning_arrester_default: bool = True
    la_cable_m: float = 15.0
    # --- network charges (Tamil Nadu) ------------------------------------------
    network_pct_domestic_upto_10kw: float = 0.20
    network_pct_other: float = 1.0               # VERIFY
    network_domestic_kw_limit: float = 10.0
    network_gst_pct: float = 18.0
    network_units_rounding: str = "floor"        # floor | round
    # --- savings / costing -----------------------------------------------------
    billing_cycle_months: int = 2               # TANGEDCO bills bi-monthly
    commercial_flat_rate: Decimal = Decimal("9.00")   # Rs/unit when no slabs fit (VERIFY)
    cost_range_band_pct: float = 10.0           # +/- shown on rough cost range
    # --- off-grid / hybrid -------------------------------------------------------
    battery_efficiency: float = 0.8
    battery_dod: float = 0.8
    inverter_power_factor: float = 0.8
    inverter_va_safety: float = 1.25
    charge_controller_safety: float = 1.25
    default_backup_hours: float = 4.0
    default_battery_voltage: float = 48.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["commercial_flat_rate"] = str(self.commercial_flat_rate)
        d["dc_cable_ampacity"] = {str(k): v for k, v in self.dc_cable_ampacity.items()}
        d["ac_cable_ampacity"] = {str(k): v for k, v in self.ac_cable_ampacity.items()}
        d["dc_cable_sizes_mm2"] = list(self.dc_cable_sizes_mm2)
        d["ac_cable_sizes_mm2"] = list(self.ac_cable_sizes_mm2)
        d["standard_breaker_ratings_a"] = list(self.standard_breaker_ratings_a)
        d["dc_fuse_ratings_a"] = list(self.dc_fuse_ratings_a)
        d["dc_device_voltage_classes"] = list(self.dc_device_voltage_classes)
        return d

    @classmethod
    def from_dict(cls, data: dict | None) -> "CalcSettings":
        data = dict(data or {})
        known = {f for f in cls.__dataclass_fields__}
        kw = {k: v for k, v in data.items() if k in known}
        if "commercial_flat_rate" in kw:
            kw["commercial_flat_rate"] = Decimal(str(kw["commercial_flat_rate"]))
        for key in ("dc_cable_ampacity", "ac_cable_ampacity"):
            if key in kw and kw[key] is not None:
                kw[key] = {float(k): float(v) for k, v in kw[key].items()}
        for key in ("dc_cable_sizes_mm2", "ac_cable_sizes_mm2", "standard_breaker_ratings_a", "dc_fuse_ratings_a",
                    "dc_device_voltage_classes"):
            if key in kw and kw[key] is not None:
                kw[key] = tuple(kw[key])
        return cls(**kw)


@dataclass
class SiteInputs:
    monthly_units: Optional[float] = None
    monthly_bill: Optional[float] = None
    phase: int = 1
    sanction_load_kw: Optional[float] = None
    roof_area_m2: Optional[float] = None
    roof_length_m: Optional[float] = None
    roof_width_m: Optional[float] = None
    roof_type: str = "rcc"              # rcc | sheet | tile
    direction: str = "south"
    shade: str = "none"                 # none | some | heavy
    category: str = "domestic"          # domestic | commercial | industrial
    goal: str = "reduce_bill"           # reduce_bill | backup | industrial
    target_kw: Optional[float] = None   # staff override of system size
    panel_count: Optional[int] = None   # staff override
    daily_backup_load_w: Optional[float] = None   # off-grid / hybrid
    backup_hours: Optional[float] = None
    dc_run_one_way_m: Optional[float] = None
    ac_run_m: Optional[float] = None
    tariff: Optional[str] = None


@dataclass
class Warning_:
    code: str
    message: str
    severity: str = "warning"           # info | warning | error

    def to_dict(self):
        return {"code": self.code, "message": self.message, "severity": self.severity}
