from woocommerce import API
import config
import time
# utils will be imported within add_reviews to avoid circular dependency issues
# if utils also ends up importing this manager or config directly/indirectly at module level.

class WooCommerceManager:
    def __init__(self):
        """
        Initializes the WooCommerce API client.
        """
        self.wcapi = API(
            url="https://pjwaterfilters.com/",  # TODO: Consider making this a config value
            consumer_key=config.WC_CONSUMER_KEY,
            consumer_secret=config.WC_CONSUMER_SECRET,
            wp_api=True,
            version="wc/v3",
            timeout=120 # Increased timeout
        )
        # Attribute IDs - can be made configurable if they change
        self.attr_id_color = 8 # Assuming 8 is for "Color"
        self.attr_id_size = 7  # Assuming 7 is for "Talla" (Size)

    def get_or_create_categories(self, shein_categories, dynamic_parent_id, initial_category_ids):
        """
        Fetches existing categories or creates new ones in WooCommerce.
        Returns a list of category ID dictionaries for the product.
        """
        product_category_ids = list(initial_category_ids)  # Start with pre-defined category IDs

        try:
            existing_wc_categories_response = self.wcapi.get("products/categories", params={"per_page": 100, "orderby": "id", "order":"asc"})
            existing_wc_categories_response.raise_for_status() # Check for HTTP errors
            existing_wc_categories = existing_wc_categories_response.json()
        except Exception as e:
            print(f"Error fetching WooCommerce categories: {e}")
            return product_category_ids # Return initial IDs if fetch fails

        wc_categories_map = {cat['name'].lower(): cat['id'] for cat in existing_wc_categories}
        
        last_created_parent_id = dynamic_parent_id

        for shein_cat_name in shein_categories:
            if not shein_cat_name or not shein_cat_name.strip(): # Skip empty category names
                continue

            normalized_shein_cat_name = shein_cat_name.strip().lower()

            if normalized_shein_cat_name in wc_categories_map:
                cat_id = wc_categories_map[normalized_shein_cat_name]
                if {'id': cat_id} not in product_category_ids:
                    product_category_ids.append({'id': cat_id})
                last_created_parent_id = cat_id # Use this existing category as parent for next potential sub-category
            else:
                # Category does not exist, create it
                print(f"Creating category: '{shein_cat_name}' with parent ID: {last_created_parent_id}")
                category_data = {
                    "name": shein_cat_name.strip(),
                    "parent": last_created_parent_id
                }
                try:
                    created_category_response = self.wcapi.post("products/categories", category_data)
                    created_category_response.raise_for_status()
                    created_category = created_category_response.json()
                    new_cat_id = created_category['id']
                    print(f"Successfully created category '{shein_cat_name}' with ID {new_cat_id}.")
                    if {'id': new_cat_id} not in product_category_ids:
                        product_category_ids.append({'id': new_cat_id})
                    wc_categories_map[normalized_shein_cat_name] = new_cat_id # Add to map for future reference
                    last_created_parent_id = new_cat_id # New category becomes parent for the next one in the list
                    time.sleep(1) # Brief pause after creating a category
                except Exception as e:
                    print(f"Error creating category '{shein_cat_name}': {e}")
                    # If creation fails, subsequent categories will use the last known good parent_id
        
        # Remove potential duplicates that might have been added if initial_category_ids contained some overlap
        # Convert list of dicts to list of tuples for set operation, then back to list of dicts
        unique_category_ids_tuples = set(tuple(d.items()) for d in product_category_ids)
        product_category_ids = [dict(t) for t in unique_category_ids_tuples]
        
        return product_category_ids

    def create_variable_product(self, name, short_description, description, category_ids, image_urls, attributes_data):
        """
        Creates a variable product in WooCommerce.
        """
        formatted_images = [{"src": url} for url in image_urls]
        
        variable_product_data = {
            "name": name,
            "type": "variable",
            "short_description": short_description,
            "description": description,
            "categories": category_ids,
            "images": formatted_images,
            "attributes": attributes_data,
            "status": "publish" # Or "draft" if preferred
        }
        
        print(f"Creating variable product: {name}")
        try:
            response = self.wcapi.post("products", variable_product_data)
            response.raise_for_status()
            product_info = response.json()
            print(f"Successfully created product ID: {product_info.get('id')}, Permalink: {product_info.get('permalink')}")
            return product_info
        except Exception as e:
            print(f"Error creating variable product '{name}': {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    print(f"Error details: {e.response.json()}")
                except ValueError: # If response is not JSON
                    print(f"Error details: {e.response.text}")
            return None


    def create_product_variations(self, product_id, base_sku, price, sizes, featured_image_url, color=None):
        """
        Creates variations for a variable product.
        Attribute IDs for color (8) and size (7) are currently hardcoded.
        """
        variations_created_count = 0
        for size_index, size_option in enumerate(sizes):
            if not size_option or not size_option.strip():
                print(f"Skipping variation creation for empty size option.")
                continue

            size_sku_part = size_option.replace(" ", "").upper()[:5] # Max 5 chars for size SKU part
            
            attributes_variation = []
            if color and color.strip():
                color_sku_part = color.replace(" ", "").upper()[:5] # Max 5 chars for color SKU part
                sku_variation = f"{base_sku}-raic-{color_sku_part}{size_sku_part}"
                attributes_variation.append({"id": self.attr_id_color, "option": color.strip()})
            else:
                sku_variation = f"{base_sku}-raic-UNICO{size_sku_part}" # "UNICO" for products without color choice
                # If there's no color, we might not need to add it to attributes,
                # or ensure the global product attribute for color is not set to "Any Color"

            attributes_variation.append({"id": self.attr_id_size, "option": size_option.strip()})
            
            product_variation_data = {
                "sku": sku_variation,
                "regular_price": str(price), # Price should be a string
                "attributes": attributes_variation,
                "image": {"src": featured_image_url} if featured_image_url else {}
            }
            
            print(f"Creating variation for product ID {product_id}: SKU {sku_variation}, Size {size_option}, Color {color if color else 'N/A'}")
            try:
                response = self.wcapi.post(f"products/{product_id}/variations", product_variation_data)
                response.raise_for_status()
                print(f"Successfully created variation: {response.json().get('id')}")
                variations_created_count +=1
                time.sleep(2)  # Sleep to avoid hitting API rate limits
            except Exception as e:
                print(f"Error creating variation with SKU {sku_variation}: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        print(f"Error details: {e.response.json()}")
                    except ValueError:
                         print(f"Error details: {e.response.text}")
        
        return variations_created_count > 0 # Return True if at least one variation was made


    def add_reviews(self, product_id, reviews_text, gender_code):
        """
        Adds reviews to a product.
        Imports fakename and fakemail from utils.py within this method.
        """
        try:
            from utils import fakename, fakemail # Import here to manage dependencies
        except ImportError:
            print("Error: Could not import 'fakename' or 'fakemail' from 'utils.py'. Reviews will not be added.")
            return 0 # Return 0 reviews added

        reviews_added_count = 0
        for review_content in reviews_text:
            if not review_content or not review_content.strip():
                print("Skipping empty review.")
                continue

            reviewer_name = ""
            if gender_code in ['1', '5', '6']: # Assuming these codes are for female
                reviewer_name = fakename.first_name_female()
            elif gender_code == '2': # Assuming this code is for male
                reviewer_name = fakename.first_name_male()
            else: # Default or other codes
                reviewer_name = fakename.first_name()
            
            reviewer_email = fakemail()
            
            datareview = {
                "product_id": product_id,
                "review": review_content.strip(),
                "reviewer": reviewer_name,
                "reviewer_email": reviewer_email,
                "rating": 5 # Defaulting to 5 stars, can be made dynamic
            }
            
            print(f"Adding review for product ID {product_id} by {reviewer_name}")
            try:
                response = self.wcapi.post("products/reviews", datareview)
                response.raise_for_status()
                print(f"Successfully added review: {response.json().get('id')}")
                reviews_added_count += 1
                time.sleep(3)  # Sleep to avoid hitting API rate limits, review posting can be sensitive
            except Exception as e:
                print(f"Error adding review by {reviewer_name}: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        print(f"Error details: {e.response.json()}")
                    except ValueError:
                        print(f"Error details: {e.response.text}")
        
        return reviews_added_count

# Example usage (for testing purposes, normally this would be called from main.py)
if __name__ == '__main__':
    print("WooCommerceManager script started for testing.")
    
    # This example assumes you have a .env file with WC_CONSUMER_KEY and WC_CONSUMER_SECRET
    # and that config.py loads them.
    # It also assumes utils.py with fakename and fakemail is available.
    
    # Initialize the manager
    # Ensure your .env file is in the same directory or PYTHONPATH is set correctly
    # For this test, config.py and utils.py should be in the same directory or accessible
    try:
        import os
        # Adjust path if your .env is not in the current working directory of this script
        # from dotenv import load_dotenv
        # if os.path.exists('.env'):
        #     load_dotenv() 
        # else:
        #     print("Warning: .env file not found. Ensure API keys are set via environment variables.")

        manager = WooCommerceManager()
        print("WooCommerceManager initialized.")

        # 1. Test Category Management
        print("\n--- Testing Category Management ---")
        shein_cats = ["New Arrivals", "Dresses", "Summer Collection"]
        dynamic_parent = 0 # 0 for top-level, or provide an existing category ID
        initial_cats = [{'id': 15}] # Example: 'Uncategorized' or some base category
        
        # category_ids = manager.get_or_create_categories(shein_cats, dynamic_parent, initial_cats)
        # print(f"Final Category IDs for product: {category_ids}")

        # 2. Test Product Creation (requires valid category_ids from above and image_urls)
        print("\n--- Testing Product Creation ---")
        # This part is commented out because it creates a product. Uncomment to test.
        # product_name = "Test Variable Product RAIC"
        # short_desc = "A cool test product from Shein."
        # long_desc = "This is a detailed description of the test variable product. It has many features."
        # images = ["https://img.ltwebstatic.com/images3_pi/2023/03/30/168016324544539358f9534b58022338df01c6f07c_thumbnail_720x.webp"]
        
        # Define attributes for the variable product (Color and Size)
        # Ensure these attributes (ID 7 for Talla/Size, ID 8 for Color) exist in your WooCommerce store
        # attributes = [
        #     {"id": manager.attr_id_color, "name": "Color", "visible": True, "variation": True, "options": ["Red", "Blue"]},
        #     {"id": manager.attr_id_size, "name": "Talla", "visible": True, "variation": True, "options": ["S", "M", "L"]},
        # ]
        
        # created_product = manager.create_variable_product(product_name, short_desc, long_desc, category_ids, images, attributes)
        # if created_product and 'id' in created_product:
        #     product_id_for_variations = created_product['id']
        #     print(f"Product created with ID: {product_id_for_variations}")

            # 3. Test Variation Creation (requires product_id from above)
            # print("\n--- Testing Variation Creation ---")
            # base_s = "TESTSKU123"
            # var_price = "25.99"
            # var_sizes = ["S", "M", "L"] # Must match options in product attributes
            # var_color = "Red" # Must match one of the color options
            # featured_img = images[0]
            
            # variations_ok = manager.create_product_variations(product_id_for_variations, base_s, var_price, var_sizes, featured_img, color=var_color)
            # print(f"Variations creation status: {variations_ok}")

            # 4. Test Review Addition (requires product_id)
            # print("\n--- Testing Review Addition ---")
            # sample_reviews = ["Great product!", "Loved the color.", "Fits perfectly."]
            # gender = '1' # Female names
            # reviews_added = manager.add_reviews(product_id_for_variations, sample_reviews, gender)
            # print(f"Number of reviews added: {reviews_added}")
        # else:
        #     print("Product creation failed, skipping variation and review tests.")

    except ImportError as ie:
        print(f"Import error during testing: {ie}. Make sure all dependencies are installed and accessible.")
    except Exception as e:
        print(f"An error occurred during WooCommerceManager testing: {e}")

    print("\nWooCommerceManager testing script finished.")
