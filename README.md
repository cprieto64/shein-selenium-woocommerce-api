# shein-selenium-woocommerce-api

Selenium script that receives the product link, sizes and discount to apply, and scrapes all the information about the product, 
translates the reviews and generates a name depending on the configured area (in this case Colombia), then evaluates if the product 
has color and creates the JSON to then send it to the WooCommerce API and create the product, then pass on the size/color variations 
and finish with the reviews.
