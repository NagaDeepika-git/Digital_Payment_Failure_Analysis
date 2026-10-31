"""
Capture High-Resolution Screenshots of All 8 Dashboard Tabs.
Digital Payment Failure Analysis
"""

import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows console
sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

TAB_SPECS = [
    (0, "tab1_executive_overview.png", "Executive Overview"),
    (1, "tab2_failure_diagnostics.png", "Failure Diagnostics"),
    (2, "tab3_time_dynamics.png", "Time Dynamics"),
    (3, "tab4_amount_latency.png", "Amount & Latency"),
    (4, "tab5_statistical_rigor.png", "Statistical Rigor"),
    (5, "tab6_data_quality.png", "Data Quality"),
    (6, "tab7_operational_actions.png", "Operational Actions"),
    (7, "tab8_transaction_explorer.png", "Transaction Explorer"),
]


def capture_all_tabs(port: int = 8501):
    url = f"http://localhost:{port}"
    print(f"Connecting to Streamlit application at {url}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Desktop viewport: 1440x950 with 1.5x scale for sharp text and crisp charts
        context = browser.new_context(viewport={"width": 1440, "height": 950}, device_scale_factor=1.5)
        page = context.new_page()

        print("Navigating to application and awaiting hydration...")
        page.goto(url, wait_until="networkidle", timeout=45000)
        page.wait_for_selector(".stApp", timeout=30000)
        time.sleep(3.0)  # Allow Streamlit initial hydration

        # 1. Take full initial dashboard overview screenshot
        overview_path = SCREENSHOTS_DIR / "dashboard_overview.png"
        page.screenshot(path=str(overview_path))
        print(f"Captured: {overview_path.name} ({overview_path.stat().st_size:,} bytes)")

        # Locate all 8 tab elements using [role="tab"]
        tab_buttons = page.locator('[role="tab"]')
        total_tabs = tab_buttons.count()
        print(f"Found {total_tabs} tabs in Streamlit interface.")

        for idx, filename, label in TAB_SPECS:
            print(f"Capturing Tab {idx+1}: {label} -> {filename}...")
            
            # Click the tab
            tab_buttons.nth(idx).click()
            
            # Wait for Plotly animations, data rendering, and layout stabilization
            time.sleep(3.0)

            # Scroll to top of content
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)

            target_path = SCREENSHOTS_DIR / filename
            page.screenshot(path=str(target_path))
            print(f"  Saved: {target_path.name} ({target_path.stat().st_size:,} bytes)")

        browser.close()

    print("\nAll 8 dashboard tab screenshots successfully captured in assets/screenshots/!")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8501
    capture_all_tabs(port)
