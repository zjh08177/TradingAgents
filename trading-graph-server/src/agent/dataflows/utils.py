import os
import json
# FIXED: Lazy import for pandas to prevent circular import issues in Studio
# import pandas as pd  # <- REMOVED module-level import
from datetime import date, timedelta, datetime
from typing import Annotated

# LAZY LOADER for pandas - prevents pandas circular import in Studio
def _get_pandas():
    """Lazy loader for pandas to prevent circular import issues"""
    try:
        import pandas as pd
        return pd
    except ImportError as e:
        raise ImportError(f"Pandas is required but not available: {e}")

SavePathType = Annotated[str, "File path to save data. If None, data is not saved."]

def save_output(data, tag: str, save_path: SavePathType = None) -> None:
    """Save data to CSV file using lazy pandas import"""
    if save_path:
        # Use lazy pandas import to get DataFrame class for type checking
        pd = _get_pandas()
        if hasattr(data, 'to_csv'):  # Check if it's a DataFrame-like object
            data.to_csv(save_path)
        else:
            # Convert to DataFrame if it's not already
            pd.DataFrame(data).to_csv(save_path)
        print(f"{tag} saved to {save_path}")


def get_current_date():
    return date.today().strftime("%Y-%m-%d")


def decorate_all_methods(decorator):
    def class_decorator(cls):
        for attr_name, attr_value in cls.__dict__.items():
            if callable(attr_value):
                setattr(cls, attr_name, decorator(attr_value))
        return cls

    return class_decorator


def get_next_weekday(date):

    if not isinstance(date, datetime):
        date = datetime.strptime(date, "%Y-%m-%d")

    if date.weekday() >= 5:
        days_to_add = 7 - date.weekday()
        next_weekday = date + timedelta(days=days_to_add)
        return next_weekday
    else:
        return date
