from playwright.sync_api import sync_playwright
import pandas as pd

def main():
    # playwright test
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.google.com")
        title = page.title()
        print(f"Page title: {title}")
        browser.close()

    # upload csv test
    df = pd.DataFrame({"name": ["Alice", "Bob"], "score": [90, 85]})
    df.to_csv("data/output.csv", index=False)
    print("✅ CSV saved to data/output.csv")

if __name__ == "__main__":
    main()
