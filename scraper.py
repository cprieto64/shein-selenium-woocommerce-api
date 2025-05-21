import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from deep_translator import GoogleTranslator

class SheinScraper:
    def __init__(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless") # Optional: run in headless mode
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--lang=es")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        # Preferences to disable images and JavaScript for faster loading (optional)
        # prefs = {"profile.managed_default_content_settings.images": 2,
        #          "profile.managed_default_content_settings.javascript": 2} # 1:Allow, 2:Block
        # chrome_options.add_experimental_option("prefs", prefs)

        try:
            self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        except Exception as e:
            print(f"Error initializing WebDriver: {e}")
            # Fallback or specific version if needed
            try:
                print("Attempting fallback to specific ChromeDriverManager version...")
                self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager(version="114.0.5735.90").install()), options=chrome_options)
            except Exception as e_fallback:
                print(f"Fallback WebDriver initialization failed: {e_fallback}")
                raise  # Re-raise the exception if fallback also fails
                
        self.driver.set_page_load_timeout(120)

    def load_page(self, url):
        try:
            self.driver.get(url)
            time.sleep(5)  # Wait for the page to load initially
        except Exception as e:
            print(f"Error loading page {url}: {e}")
            # Consider adding more robust error handling or retries here

    def close_popup_if_present(self):
        try:
            time.sleep(2) # Wait for popup to potentially appear
            popup_close_button = WebDriverWait(self.driver, 10).until(
                EC((By.XPATH, '//div[@class="c-coupon-box"]//i | //div[@class="sui-dialog-close"]'))) # Added alternative XPath
            popup_close_button.click()
            print("Popup closed.")
            time.sleep(2) # Wait for popup to disappear
        except Exception as e:
            print(f"No popup found or error closing popup: {e}")

    def extract_product_details(self):
        details = {
            "product_name": None,
            "sku": None,
            "shein_price": None,
            "shein_categories": [],
            "image_urls": [],
            "description": None,
            "color": None,
        }

        # Product Name
        try:
            product_name_element = WebDriverWait(self.driver, 10).until(EC((By.XPATH, '//div[@class="product-intro__info"]//h1')))
            details["product_name"] = product_name_element.text.strip()
        except Exception as e:
            print(f"Error extracting product name: {e}")

        # SKU
        try:
            sku_element = WebDriverWait(self.driver, 10).until(EC((By.XPATH, '//div[@class="product-intro__head-sku"]')))
            details["sku"] = sku_element.text.replace("SKU: ", "").strip()
        except Exception as e:
            print(f"Error extracting SKU: {e}")

        # Shein Price
        try:
            price_element = WebDriverWait(self.driver, 10).until(EC((By.XPATH, '//div[@class="product-intro__head-price j-expose__product-intro__head-price"]/div[1]//span')))
            details["shein_price"] = float(price_element.text.replace('€', '').replace(',', '.').strip())
        except Exception as e:
            print(f"Error extracting Shein price: {e}")
            try: # Fallback for different price structure
                price_element_fallback = WebDriverWait(self.driver, 5).until(EC((By.XPATH, '//div[@class="from"]')))
                price_text = price_element_fallback.text.replace('€', '').replace(',', '.').strip()
                details["shein_price"] = float(price_text)
            except Exception as e_fallback:
                print(f"Fallback error extracting Shein price: {e_fallback}")


        # Shein Categories
        try:
            category_elements = WebDriverWait(self.driver, 10).until(EC((By.XPATH, '//div[@class="bread-crumb__inner"]//div[@class="bread-crumb__item"][a or span]')))
            categories_raw = [elem.text.strip() for elem in self.driver.find_elements(By.XPATH, '//div[@class="bread-crumb__inner"]//div[@class="bread-crumb__item"][a or span]')]
            categories_processed = []
            for cat_text in categories_raw:
                if '&' in cat_text:
                    categories_processed.extend([c.strip() for c in cat_text.split('&')])
                else:
                    categories_processed.append(cat_text)
            
            unwanted_categories = {"SHEIN", "rebajas", "Rebajas", "Home", "Hogar"} # Added "Hogar"
            details["shein_categories"] = [cat for cat in categories_processed if cat and cat not in unwanted_categories]

        except Exception as e:
            print(f"Error extracting categories: {e}")

        # Image URLs
        try:
            images_container = WebDriverWait(self.driver, 10).until(EC((By.XPATH, '//div[@class="product-intro__thumbs-inner"]')))
            thumbnail_elements = images_container.find_elements(By.XPATH, './/div[@class="product-intro__thumbs-item"]//img') # Simpler XPath for img
            
            image_urls_raw = []
            for thumb in thumbnail_elements:
                src = thumb.get_attribute('src')
                if src:
                    image_urls_raw.append(src)
            
            cleaned_urls = []
            for url in image_urls_raw:
                if url.startswith("//"):
                    url = "https:" + url
                url = url.replace('_thumbnail_', '_') # General replacement for higher quality
                # Ensure .webp, but avoid double .webp.webp
                if ".webp" not in url:
                     if ".jpg" in url:
                         url = url.split(".jpg")[0] + ".webp"
                     elif ".png" in url:
                         url = url.split(".png")[0] + ".webp"
                     else: # if no common extension, just append (less ideal)
                         url += ".webp"
                elif url.endswith(".webp.webp"):
                    url = url[:-5]

                if url not in cleaned_urls: # Avoid duplicates
                    cleaned_urls.append(url)
            details["image_urls"] = cleaned_urls
        except Exception as e:
            print(f"Error extracting image URLs: {e}")

        # Description
        try:
            # Click to reveal description (if necessary)
            try:
                desc_icon = WebDriverWait(self.driver, 5).until(EC((By.XPATH, '//div[@class="product-intro__description"]//i')))
                self.driver.execute_script("arguments[0].click();", desc_icon) # JS click
                time.sleep(1)
            except Exception:
                print("Description reveal icon not found or not clickable, proceeding anyway.")

            desc_items = WebDriverWait(self.driver, 10).until(
                EC((By.XPATH, '//div[contains(@class,"product-intro__description-table-item")]'))
            )
            description_parts = []
            
            # Corrected XPath to target individual key and value elements
            # This assumes keys are in 'key' class and values in 'val' class within each item
            items = self.driver.find_elements(By.XPATH, '//div[contains(@class,"product-intro__description-table-item")]')
            for item in items:
                try:
                    key_element = item.find_element(By.XPATH, './/div[contains(@class,"key")]')
                    value_element = item.find_element(By.XPATH, './/div[contains(@class,"val")]')
                    key = key_element.text.strip().replace(":", "")
                    value = value_element.text.strip()
                    if key and value: # Ensure both key and value are present
                         description_parts.append(f"{key}: {value}")
                except Exception as e_item:
                    # If specific key/value structure is not found, try to get text of the item
                    print(f"Could not parse key/value for a description item: {e_item}. Using item's text.")
                    item_text = item.text.strip()
                    if item_text: # Add if text is not empty
                        description_parts.append(item_text)

            details["description"] = "\n".join(description_parts)
            if not details["description"]: # Fallback if structured description is empty
                 print("Structured description was empty. Trying to get general description text.")
                 general_desc_element = self.driver.find_element(By.XPATH, '//div[@class="product-intro__description"]')
                 details["description"] = general_desc_element.text.strip()


        except Exception as e:
            print(f"Error extracting description: {e}")

        # Color
        try:
            color_element = WebDriverWait(self.driver, 10).until(EC((By.XPATH, '//div[@class="product-intro__color j-expose__product-intro__color"]/div/span/span')))
            details["color"] = color_element.text.strip()
        except Exception as e:
            print(f"Color not found or error extracting color: {e}")
            details["color"] = "No especificado" # Default if not found

        return details

    def extract_and_translate_reviews(self):
        reviews_list = []
        try:
            review_elements_xpath = '//div[contains(@class,"common-reviews__list")]//div[contains(@class,"j-expose__common-reviews__list-item")]//div[@class="rate-des"]'
            WebDriverWait(self.driver, 15).until(EC((By.XPATH, review_elements_xpath)))
            review_elements = self.driver.find_elements(By.XPATH, review_elements_xpath)
            
            if not review_elements:
                print("No review elements found on the page.")
                return []

            print(f"Found {len(review_elements)} review elements.")
            translator = GoogleTranslator(source='auto', target='es')

            for i, review_element in enumerate(review_elements):
                try:
                    review_text = review_element.text.strip()
                    if review_text:
                        # Basic cleaning of review text (optional, can be expanded)
                        review_text = review_text.replace("\n", " ").strip()
                        
                        # Translate if not empty
                        if review_text:
                            time.sleep(1) # Sleep before translation to avoid rate limiting
                            translated_text = translator.translate(review_text)
                            reviews_list.append(translated_text)
                            print(f"Review {i+1} translated: {translated_text[:50]}...") # Print first 50 chars
                        else:
                            print(f"Review {i+1} was empty after cleaning, skipping translation.")
                    else:
                        print(f"Review {i+1} has no text, skipping.")
                except Exception as e_review:
                    print(f"Error processing or translating review {i+1}: {e_review}")
                    original_text = review_element.text.strip() # Try to get original text for logging
                    if original_text:
                        reviews_list.append(f"[Translation Error] {original_text}") # Add original with error mark
                    else:
                        reviews_list.append("[Translation Error] Review text was empty or unreadable")
                
                if i >= 4 and not reviews_list: # If first 5 reviews failed, likely a broader issue
                    print("First 5 reviews failed to process. Aborting further review extraction.")
                    break
        
        except Exception as e:
            print(f"Error finding or processing review container: {e}")
        
        if not reviews_list:
            print("No reviews were extracted or translated.")
        
        return reviews_list

    def quit_driver(self):
        if self.driver:
            self.driver.quit()
            print("WebDriver session closed.")

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    scraper = SheinScraper()
    
    # Test with a product URL
    # product_url = "https://es.shein.com/Manfinity-Mode-Men-Solid-Button-Up-Shirt-p-13133081-cat-1977.html" # Replace with a valid Shein URL
    product_url = "https://es.shein.com/Letter-Graphic-Drop-Shoulder-Tee-p-11365602-cat-1738.html" # A different product for testing
    
    scraper.load_page(product_url)
    scraper.close_popup_if_present()
    
    product_data = scraper.extract_product_details()
    print("\n--- Product Details ---")
    for key, value in product_data.items():
        print(f"{key.replace('_', ' ').capitalize()}: {value}")
        
    reviews = scraper.extract_and_translate_reviews()
    print("\n--- Translated Reviews ---")
    if reviews:
        for i, review in enumerate(reviews):
            print(f"Review {i+1}: {review}")
    else:
        print("No reviews available for this product.")
            
    scraper.quit_driver()
    print("\nSheinScraper example usage finished.")
