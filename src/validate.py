# Module: Open-Meteo Weather & Air Quality API Ingestion (4-Year Data Validation)
# Developed & Maintained by: Noor Fatima (Roll No. 189)

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ValidationError


class AirWeatherRecord(BaseModel):
    """Rules for one hourly row. Each field says what a valid value looks like."""
    city: str
    time: datetime
    # Optional = the value may be missing (None); if present it must respect the limits
    pm2_5: Optional[float] = Field(default=None, ge=0, le=1000)          # ug/m3
    temperature: Optional[float] = Field(default=None, ge=-30, le=60)    # deg C
    humidity: Optional[float] = Field(default=None, ge=0, le=100)        # %
    wind_speed: Optional[float] = Field(default=None, ge=0, le=200)      # km/h
    pressure: Optional[float] = Field(default=None, ge=800, le=1100)     # hPa


def validate_rows(rows):
    """Check every row. Return (valid_rows, invalid_rows)."""
    valid, invalid = [], []
    for row in rows:
        try:
            record = AirWeatherRecord(**row)   # raises an error if a rule is broken
            valid.append(record.model_dump())  # turn the checked record back into a dict
        except ValidationError as e:
            invalid.append({"row": row, "error": str(e)})  # keep the bad row and the reason
    return valid, invalid


if __name__ == "__main__":
    from extract import extract_all  # reuse the extraction step

    rows = extract_all()
    valid, invalid = validate_rows(rows)

    print("Valid rows:", len(valid))
    print("Invalid rows:", len(invalid))

    # Show the first 3 rejected rows (if any) to see why they failed
    for item in invalid[:3]:
        print(item["row"])
        print(item["error"])
