# script.py
import sys
from selenium import webdriver
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main(email, code):
    # Specify the path to ChromeDriver (replace with the actual path)
    chrome_driver_path = "/home/ws-admin/.cache/selenium/chromedriver/linux64/117.0.5938.62/chromedriver"
    time.sleep(5)

    # Set the PATH environment variable to include the directory containing ChromeDriver
    os.environ["PATH"] += os.pathsep + os.path.dirname(chrome_driver_path)

    # Configure ChromeOptions
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=DEBUG")
    chrome_options.add_argument("--verbose")

    # Initialize WebDriver without specifying executable_path
    driver = webdriver.Chrome(options=chrome_options)

    # Navigate to the website
    driver.get("https://coupon.devplay.com/coupon/ck/en")

    # Find and fill the email and coupon code fields
    email_field = driver.find_element(By.ID, "email-box")
    coupon_field = driver.find_element(By.ID, "code-box")

    email_field.send_keys(email)
    coupon_field.send_keys(code)

    # Submit the form
    submit_button = driver.find_element(By.CSS_SELECTOR, ".submit-button")
    submit_button.click()

    alert_text = ""  # Initialize the alert_text variable

    try:
        # Wait for the alert to appear
        wait = WebDriverWait(driver, 10)
        alert = wait.until(EC.alert_is_present())

        # Handle the alert
        if alert:
            alert_text = alert.text
            print(alert_text)

            # Check if the alert message matches any of the specified messages
            if alert_text in [
                "Done! Log in to the game to claim your reward!",
                "Please check your DevPlay account!",
                "Please check the coupon code!",
                "This coupon code is invalid.",
                "This coupon code is currently not available. Please check the coupon code usage dates.",
                "This coupon code has already been used!",
                "You have exceeded the number of available coupons."
            ]:
                pass  # Do nothing if the alert matches
            else:
                # Handle the alert based on your requirements here (e.g., accept or dismiss)
                alert.accept()  # Dismiss the alert
    except Exception as e:
        print("An error occurred:", str(e))

    # Close the WebDriver when done (in case the alert was not triggered)
    driver.quit()

    return alert_text  # Return the alert text

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <email> <code>")
        sys.exit(1)
    email = sys.argv[1]
    code = sys.argv[2]
    alert_text = main(email, code)
