import os
from datetime import datetime


def save_screenshot(driver, folder="screenshots", prefix="error"):
    """
    Save screenshot with timestamp and return file path.
    """
    os.makedirs(folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(folder, f"{prefix}_{timestamp}.png")

    driver.save_screenshot(file_path)
    return file_path