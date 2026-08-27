#!/usr/bin/env python3
"""
Parse TLE (Two-Line Element) data from CelesTrak into expanded satellite catalogue.
TLE Format:
  Line 0: Satellite name
  Line 1: Satellite number, classification, epoch, mean motion derivatives
  Line 2: Inclination, RAAN, eccentricity, arg perigee, mean anomaly, mean motion
"""

import json
import math
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone


@dataclass
class TLEEntry:
    """Parsed TLE orbital data."""
    name: str
    norad_id: str
    classification: str
    epoch_year: int
    epoch_day: float
    mean_motion: float  # rev/day
    eccentricity: float
    inclination_deg: float
    raan_deg: float  # Right Ascension of Ascending Node
    arg_perigee_deg: float
    mean_anomaly_deg: float
    rev_number: int
    altitude_km: float = 0.0
    period_min: float = 0.0
    category: str = "unknown"
    source_file: str = ""

    def __post_init__(self):
        """Calculate derived orbital parameters."""
        if self.mean_motion > 0:
            self.period_min = 1440.0 / self.mean_motion  # minutes per orbit
            # Semi-major axis from Kepler's 3rd law (Earth mu = 398600.4418 km^3/s^2)
            mu = 398600.4418
            n = self.mean_motion * 2 * math.pi / 86400.0  # rad/s
            a = (mu / (n ** 2)) ** (1.0 / 3.0)  # km
            self.altitude_km = a - 6371.0  # Subtract Earth radius


def parse_tle_line1(line: str) -> Dict:
    """Parse TLE Line 1 fields."""
    # TLE scientific notation: e.g., "00000+0" means 0.00000e+0
    # Format: XXXXXXY where XXXXXX is mantissa (decimal assumed after first digit), Y is exponent
    def parse_tle_sci(s: str) -> float:
        """Parse TLE scientific notation like '00000+0' or '15348-3'."""
        s = s.strip()
        if not s or s == '00000+0':
            return 0.0
        # Last character is exponent sign + digit
        exp_sign = s[-2]
        exp_val = s[-1]
        mantissa = s[:-2]
        # Decimal point assumed after first character
        num = float(mantissa[0] + '.' + mantissa[1:] + 'e' + exp_sign + exp_val)
        return num

    return {
        "norad_id": line[2:7].strip(),
        "classification": line[7],
        "epoch_year": int(line[18:20]),
        "epoch_day": float(line[20:32]),
        "mean_motion_dot": float(line[33:43]),
        "mean_motion_ddot": parse_tle_sci(line[44:52]),
        "bstar": parse_tle_sci(line[53:61]),
        "rev_number": int(line[63:68]),
    }


def parse_tle_line2(line: str) -> Dict:
    """Parse TLE Line 2 fields."""
    ecc_str = line[26:33].strip()
    return {
        "inclination_deg": float(line[8:16]),
        "raan_deg": float(line[17:25]),
        "eccentricity": float("0." + ecc_str),
        "arg_perigee_deg": float(line[34:42]),
        "mean_anomaly_deg": float(line[43:51]),
        "mean_motion": float(line[52:63]),
    }


def parse_tle_file(filepath: str, category: str = "unknown") -> List[TLEEntry]:
    """Parse a TLE file and return list of entries."""
    entries = []
    if not os.path.exists(filepath):
        return entries

    with open(filepath, 'r') as f:
        lines = [l.rstrip() for l in f.readlines() if l.strip()]

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is TLE Line 1 (starts with '1 ')
        if line.startswith('1 '):
            # No name line, generate from NORAD ID
            name = f"SAT-{line[2:7].strip()}"
            line1 = line
            i += 1
            if i < len(lines) and lines[i].startswith('2 '):
                line2 = lines[i]
                i += 1
            else:
                continue
        elif not line.startswith('2 '):
            # This is a name line (doesn't start with '1 ' or '2 ')
            name = line.strip()
            # Remove leading '0 ' if present
            if name.startswith('0 '):
                name = name[2:].strip()
            i += 1
            if i < len(lines) and lines[i].startswith('1 '):
                line1 = lines[i]
                i += 1
                if i < len(lines) and lines[i].startswith('2 '):
                    line2 = lines[i]
                    i += 1
                else:
                    continue
            else:
                continue
        else:
            i += 1
            continue

        try:
            data1 = parse_tle_line1(line1)
            data2 = parse_tle_line2(line2)

            entry = TLEEntry(
                name=name,
                norad_id=data1["norad_id"],
                classification=data1["classification"],
                epoch_year=data1["epoch_year"],
                epoch_day=data1["epoch_day"],
                mean_motion=data2["mean_motion"],
                eccentricity=data2["eccentricity"],
                inclination_deg=data2["inclination_deg"],
                raan_deg=data2["raan_deg"],
                arg_perigee_deg=data2["arg_perigee_deg"],
                mean_anomaly_deg=data2["mean_anomaly_deg"],
                rev_number=data1["rev_number"],
                category=category,
                source_file=os.path.basename(filepath),
            )
            entries.append(entry)
        except (ValueError, IndexError) as e:
            # Skip malformed entries
            pass

    return entries


def build_catalogue() -> Dict:
    """Build comprehensive satellite catalogue from all TLE files."""
    tle_files = {
        "stations": "/tmp/stations.tle",
        "visual": "/tmp/visual.tle",
        "active": "/tmp/active.tle",
        "analyst": "/tmp/analyst.tle",
        "starlink": "/tmp/starlink.tle",
        "weather": "/tmp/weather.tle",
        "goes": "/tmp/goes.tle",
        "resource": "/tmp/resource.tle",
        "geodetic": "/tmp/geodetic.tle",
        "intelsat": "/tmp/intelsat.tle",
        "iridium_next": "/tmp/iridium_next.tle",
        "oneweb": "/tmp/oneweb.tle",
        "planet": "/tmp/planet.tle",
        "spire": "/tmp/spire.tle",
        "argos": "/tmp/argos.tle",
        "sarsat": "/tmp/sarsat.tle",
        "cubesat": "/tmp/cubesat.tle",
    }

    catalogue = {
        "timestamp": datetime.now(timezone.utc).timestamp(),
        "source": "CelesTrak Multi-Category TLE",
        "generated": datetime.now(timezone.utc).isoformat(),
        "categories": {},
        "satellites": {},
        "statistics": {},
    }

    all_entries = []
    for category, filepath in tle_files.items():
        entries = parse_tle_file(filepath, category)
        if entries:
            catalogue["categories"][category] = {
                "count": len(entries),
                "file": os.path.basename(filepath),
            }
            all_entries.extend(entries)

    # Category priority - more specific categories win
    category_priority = {
        "stations": 100,
        "visual": 90,
        "analyst": 80,
        "starlink": 70,
        "oneweb": 65,
        "iridium_next": 60,
        "intelsat": 55,
        "weather": 50,
        "goes": 45,
        "resource": 40,
        "geodetic": 35,
        "planet": 30,
        "spire": 25,
        "argos": 20,
        "sarsat": 15,
        "cubesat": 10,
        "active": 0,  # Lowest priority - generic
    }

    # Deduplicate by NORAD ID, keep highest priority category
    seen_ids = {}
    for entry in all_entries:
        priority = category_priority.get(entry.category, 0)
        if entry.norad_id not in seen_ids or priority > seen_ids[entry.norad_id][1]:
            seen_ids[entry.norad_id] = (entry, priority)

    for entry, priority in seen_ids.values():
        catalogue["satellites"][entry.norad_id] = {
                "name": entry.name,
                "norad_id": entry.norad_id,
                "classification": entry.classification,
                "category": entry.category,
                "orbital": {
                    "inclination_deg": round(entry.inclination_deg, 4),
                    "altitude_km": round(entry.altitude_km, 2),
                    "period_min": round(entry.period_min, 2),
                    "eccentricity": entry.eccentricity,
                    "raan_deg": round(entry.raan_deg, 4),
                    "arg_perigee_deg": round(entry.arg_perigee_deg, 4),
                    "mean_anomaly_deg": round(entry.mean_anomaly_deg, 4),
                    "mean_motion": round(entry.mean_motion, 8),
                },
                "epoch": {
                    "year": entry.epoch_year,
                    "day": entry.epoch_day,
                },
                "rev_number": entry.rev_number,
            }

    # Compute statistics
    altitudes = [s["orbital"]["altitude_km"] for s in catalogue["satellites"].values()]
    periods = [s["orbital"]["period_min"] for s in catalogue["satellites"].values()]
    inclinations = [s["orbital"]["inclination_deg"] for s in catalogue["satellites"].values()]

    catalogue["statistics"] = {
        "total_satellites": len(catalogue["satellites"]),
        "categories_count": len(catalogue["categories"]),
        "altitude": {
            "min_km": round(min(altitudes), 2),
            "max_km": round(max(altitudes), 2),
            "mean_km": round(sum(altitudes) / len(altitudes), 2),
        },
        "period": {
            "min_min": round(min(periods), 2),
            "max_min": round(max(periods), 2),
            "mean_min": round(sum(periods) / len(periods), 2),
        },
        "inclination": {
            "min_deg": round(min(inclinations), 2),
            "max_deg": round(max(inclinations), 2),
            "mean_deg": round(sum(inclinations) / len(inclinations), 2),
        },
        "by_classification": {},
    }

    # Count by classification
    for sat in catalogue["satellites"].values():
        cls = sat["classification"]
        catalogue["statistics"]["by_classification"][cls] = \
            catalogue["statistics"]["by_classification"].get(cls, 0) + 1

    return catalogue


if __name__ == "__main__":
    catalogue = build_catalogue()
    output_path = "/Users/jjmarte/delta-stream/qb_protocol/satellite_orbital_data_expanded.json"
    with open(output_path, 'w') as f:
        json.dump(catalogue, f, indent=2)

    print(f"EXPANDED CATALOGUE: {catalogue['statistics']['total_satellites']} satellites")
    print(f"Categories: {catalogue['statistics']['categories_count']}")
    print(f"Altitude range: {catalogue['statistics']['altitude']['min_km']} - {catalogue['statistics']['altitude']['max_km']} km")
    print(f"Period range: {catalogue['statistics']['period']['min_min']} - {catalogue['statistics']['period']['max_min']} min")
    print(f"\nBreakdown by category:")
    for cat, info in catalogue["categories"].items():
        print(f"  {cat}: {info['count']} satellites")
    print(f"\nBy classification: {catalogue['statistics']['by_classification']}")
    print(f"\nSaved to: {output_path}")
