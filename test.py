from selenium import webdriver

# Create a WebDriver instance using Chrome
driver = webdriver.Chrome()

# Navigate to a webpage
driver.get("https://coupon.devplay.com/coupon/ck/en")

# Perform actions on the webpage
# For example, click a button
# driver.find_element_by_css_selector("button.some-button").click()

# You can also fill out forms, interact with elements, and more.

# Capture screenshots if needed
# driver.save_screenshot("screenshot.png")

# Close the browser window when done
driver.quit()
