import os
import yaml
from datetime import datetime

HOLIDAY_DIR = os.path.join(os.path.dirname(__file__), "holidays")


class SchoolHolidayAPI:
    def get_countries(self):
        """Return available countries (based on YAML files in the holidays folder)."""
        countries = {}
        for filename in os.listdir(HOLIDAY_DIR):
            if filename.endswith(".yaml"):
                country_code = filename[:-5]  # Strip .yaml
                countries[country_code.capitalize()] = country_code
        return countries

    def get_regions(self, country):
        """Return regions defined in the YAML file for the given country."""
        regions = {}
        country_file = os.path.join(HOLIDAY_DIR, f"{country.lower()}.yaml")
        if not os.path.exists(country_file):
            return {}

        with open(country_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            for region in data:
                regions[region["name"]] = region["name"]
        return regions

    def parse_date(value):
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Invalid date format: {value}")


    def get_holidays(self, country, region):
        """Return holiday info for today and upcoming dates."""
        today = datetime.now().date()
        country_file = os.path.join(HOLIDAY_DIR, f"{country.lower()}.yaml")

        if not os.path.exists(country_file):
            return {}

        with open(country_file, "r", encoding="utf-8") as f:
            regions = yaml.safe_load(f)

        for reg in regions:
            if reg["name"] == region:
                upcoming = []
                current = None

                for holiday in reg.get("holidays", []):
                    try:
                        start = self.parse_date(holiday["date_from"])
                        end = self.parse_date(holiday["date_till"])

                        if start <= today <= end:
                            current = holiday["name"]
                        elif start > today:
                            upcoming.append({
                                "name": holiday["name"],
                                "starts_in_days": (start - today).days,
                                "date_from": str(start),
                                "date_till": str(end)
                            })
                    except Exception as e:
                        continue

                return {
                    "current_holiday_status": current is not None,
                    "current_holiday": current or "None",
                    "upcoming_holidays": sorted(upcoming, key=lambda x: x["starts_in_days"])
                }

        return {}
