## shein-selenium-woocommerce-api

This script automates the process of creating products in a WooCommerce store based on information scraped from Shein product pages.

### Inputs

- **URL:** The URL of the Shein product page to be scraped.
- **Tallas (Sizes):** A comma-separated list of available sizes for the product (e.g., "S,M,XL").
- **Discount:** The discount percentage to apply to the product price (e.g., "20").
- **Gender:** A numerical code representing the product's gender category: 
  - 1: Women
  - 2: Men
  - 3: Kids
  - 4: Beauty
  - 5: Women's Jewelry
  - 6: Women's Footwear
  - 7: Men's Jewelry
  - 8: Men's Footwear

### Outputs

- **Product Creation:** The script creates a new product in the WooCommerce store using the provided information.
- **Variation Creation:** For products with size and/or color variations, the script creates corresponding variations in the WooCommerce store.
- **Review Translation and Addition:** Reviews from the Shein product page are translated into Spanish and added to the WooCommerce product as customer reviews.

### Process Overview

1. **Scrape Shein Data:** The script accesses the specified Shein product page using Selenium and extracts key information, including:
   - Product name
   - SKU
   - Price
   - Categories
   - Images
   - Product description
   - Color (if applicable)
   - Reviews
2. **Translate Reviews:** The script uses the Deep Translator library to translate the reviews from Shein's language (likely Chinese) into Spanish.
3. **Create WooCommerce Categories:** The script analyzes the product's categories and ensures they exist in the WooCommerce store. If a category is missing, it is created dynamically.
4. **Create WooCommerce Product:** The script creates a new WooCommerce product based on the scraped Shein data. This includes:
   - Product name
   - Product description
   - Categories
   - Images
   - Product type (variable)
   - Attributes (size and color, if applicable)
5. **Create WooCommerce Variations:** If the product has size and/or color variations, the script creates the corresponding variations with their respective SKUs, prices, and images.
6. **Add Reviews:** The script adds the translated reviews to the WooCommerce product as customer reviews with fake reviewer names and emails.