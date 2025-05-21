from scraper import SheinScraper
from woocommerce_manager import WooCommerceManager
# No other imports like os, load_dotenv, time, API, selenium, GoogleTranslator, Faker, or utils are needed here.

def crear_producto(tallas_list, product_url_shein, markup_percentage_str, gender_code_str):
    """
    Orchestrates the creation of a product by scraping data from Shein and adding it to WooCommerce.

    Args:
        tallas_list (list): List of available sizes for the product (e.g., ['S', 'M']).
        product_url_shein (str): URL of the Shein product page.
        markup_percentage_str (str): Markup percentage string (e.g., "20" for 20%).
        gender_code_str (str): Gender code for product categorization.
    """
    initial_category_ids = []
    parent_category_id_for_shein_cats = 0

    # Define initial WooCommerce categories and parent for Shein categories based on gender_code_str
    if gender_code_str == "2":  # Hombre
        print(f"Processing for 'Hombre' (Men): {gender_code_str}")
        initial_category_ids = [{"id": 184}, {"id": 200}]  # Ropa, Ropa Hombre
        parent_category_id_for_shein_cats = 200
    elif gender_code_str == "1":  # Mujer
        print(f"Processing for 'Mujer' (Women): {gender_code_str}")
        initial_category_ids = [{"id": 183}, {"id": 145}]  # Ropa, Ropa Mujer
        parent_category_id_for_shein_cats = 145
    elif gender_code_str == "5":  # Mujer Joyas
        print(f"Processing for 'Mujer Joyas' (Women's Jewelry): {gender_code_str}")
        initial_category_ids = [{"id": 183}, {"id": 298}]  # Ropa, Joyeria y Bisuteria
        parent_category_id_for_shein_cats = 298
    elif gender_code_str == "6":  # Mujer Calzado
        print(f"Processing for 'Mujer Calzado' (Women's Footwear): {gender_code_str}")
        initial_category_ids = [{"id": 183}, {"id": 243}]  # Ropa, Zapatos Mujer
        parent_category_id_for_shein_cats = 243
    else:
        print(f"Warning: Gender code {gender_code_str} not recognized. Using default 'Uncategorized'.")
        initial_category_ids = [{"id": 15}] # 'Uncategorized'
        parent_category_id_for_shein_cats = 0 # No parent

    scraper_instance = SheinScraper()
    woo_commerce_manager_instance = WooCommerceManager()

    try:
        print("####################### \n  INITIALIZING SCRAPER    \n#######################")
        scraper_instance.load_page(product_url_shein)
        scraper_instance.close_popup_if_present()
        
        scraped_product_data = scraper_instance.extract_product_details()

        if not scraped_product_data or not scraped_product_data.get("product_name") or scraped_product_data.get("shein_price") is None:
            print("Error: Could not extract essential product data from Shein. Aborting process.")
            return

        product_name_shein = scraped_product_data["product_name"]
        print(f"Successfully scraped product: {product_name_shein}")

        # Calculate final product price with markup
        try:
            markup_percentage = int(markup_percentage_str)
            shein_base_price = float(scraped_product_data["shein_price"])
            # The term "discount" in the original script was actually used as a markup.
            # If discount_percentage is e.g. 20, it means 20% markup.
            final_product_price_calculated = shein_base_price * (1 + markup_percentage / 100)
            final_product_price_str = str(round(final_product_price_calculated, 2))
            print(f"Shein Price: {shein_base_price}, Markup: {markup_percentage}%, Final Store Price: {final_product_price_str}")
        except ValueError:
            print(f"Error: Invalid markup percentage '{markup_percentage_str}'. Using Shein price without changes.")
            final_product_price_str = str(scraped_product_data["shein_price"])

        translated_product_reviews = scraper_instance.extract_and_translate_reviews()
        print(f"Extracted and translated {len(translated_product_reviews)} reviews.")

        print("\n####################### \n  PROCESSING WOOCOMMERCE    \n#######################")
        
        # Get or create product categories in WooCommerce
        product_category_ids_wc = woo_commerce_manager_instance.get_or_create_categories(
            shein_categories=scraped_product_data.get('shein_categories', []), 
            dynamic_parent_id=parent_category_id_for_shein_cats, 
            initial_category_ids=initial_category_ids
        )
        print(f"Final category IDs for WooCommerce product: {product_category_ids_wc}")

        # Prepare product attributes for WooCommerce
        product_attributes_wc = [
            {
                "id": woo_commerce_manager_instance.attr_id_size, # Using ID from WooCommerceManager
                "name": "Talla", # Name of the attribute as it should appear in WC
                "visible": True,
                "variation": True,
                "options": tallas_list,
            },
        ]
        product_color_shein = scraped_product_data.get("color")
        if product_color_shein:
            product_attributes_wc.append(
                {
                    "id": woo_commerce_manager_instance.attr_id_color, # Using ID from WooCommerceManager
                    "name": "Color", # Name of the attribute
                    "visible": True,
                    "variation": True,
                    "options": [product_color_shein],
                }
            )
        
        # Create the variable product in WooCommerce
        created_wc_product_info = woo_commerce_manager_instance.create_variable_product(
            name=product_name_shein,
            short_description=scraped_product_data.get("description", ""), # Using full description as short as well
            description=scraped_product_data.get("description", ""),
            category_ids=product_category_ids_wc,
            image_urls=scraped_product_data.get("image_urls", []),
            attributes_data=product_attributes_wc
        )

        if not created_wc_product_info or "id" not in created_wc_product_info:
            print("Error: Failed to create variable product in WooCommerce. Aborting.")
            return
        
        wc_product_id = created_wc_product_info["id"]
        wc_product_url = created_wc_product_info.get("permalink", "N/A")
        print(f"Variable product created successfully in WooCommerce. ID: {wc_product_id}, URL: {wc_product_url}")

        # Create product variations in WooCommerce
        base_product_sku = scraped_product_data.get("sku", "RAICSKU") # Default SKU if not found
        # Use the first image as the featured image for variations, if available
        featured_product_image = None
        if scraped_product_data.get("image_urls"):
            featured_product_image = scraped_product_data["image_urls"][0]
        
        variations_successfully_created = woo_commerce_manager_instance.create_product_variations(
            product_id=wc_product_id,
            base_sku=base_product_sku,
            price=final_product_price_str,
            sizes=tallas_list,
            featured_image_url=featured_product_image,
            color=product_color_shein
        )
        if variations_successfully_created:
            print("Product variations created successfully.")
        else:
            print("Warning: No product variations were created, or an error occurred during variation creation.")

        # Add reviews to the product in WooCommerce
        if translated_product_reviews:
            reviews_added_count = woo_commerce_manager_instance.add_reviews(
                product_id=wc_product_id,
                reviews_text=translated_product_reviews,
                gender_code=gender_code_str # Pass gender_code for fake name generation
            )
            print(f"{reviews_added_count} reviews added to the product in WooCommerce.")
        else:
            print("No reviews to add for this product.")

        print(f"\nProduct creation process complete! View product at: {wc_product_url}")

    except Exception as e:
        print(f"An unexpected error occurred in the main product creation process: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging

    finally:
        if 'scraper_instance' in locals() and scraper_instance: # Ensure scraper_instance was initialized
            scraper_instance.quit_driver()
        print("####################### \n  PROCESS FINISHED    \n#######################")


if __name__ == "__main__":
    print("--- Shein to WooCommerce Product Importer ---")
    
    shein_url_input = input("Ingresa la URL de Shein: ")
    
    # Get Tallas (Sizes)
    while True:
        sizes_input_str = input("Ingrese las tallas separadas por comas, sin espacios (ej: S,M,XL o M si es única): ")
        if sizes_input_str.strip(): # Check if input is not empty
            product_sizes_list = [size.strip().upper() for size in sizes_input_str.split(",")]
            break
        else:
            print("Error: Las tallas no pueden estar vacías. Por favor, ingrese al menos una talla.")
            
    # Get Markup Percentage (formerly discount)
    while True:
        markup_input_str = input("Ingresa el porcentaje de GANANCIA deseado sobre el precio de Shein (ej: 20 para 20%): ")
        if markup_input_str.strip().isdigit(): # Basic validation for digits
            break
        else:
            print("Error: El porcentaje de ganancia debe ser un número entero positivo (ej: 20).")
            
    # Get Gender Code
    gender_category_options = {
        "1": "Mujer", "2": "Hombre", "3": "Niños (No implementado completamente)", 
        "4": "Belleza (No implementado completamente)", "5": "Mujer Joyas", "6": "Mujer Calzado", 
        "7": "Hombre Joyas (No implementado completamente)", "8": "Hombre Calzado (No implementado completamente)"
    }
    print("\nSeleccione el género/categoría principal del producto:")
    for code, description in gender_category_options.items():
        print(f"{code}: {description}")
    
    while True:
        gender_selection_str = input(f"Opción ({'/'.join(gender_category_options.keys())}): ")
        if gender_selection_str in gender_category_options:
            break
        else:
            print("Error: Opción no válida. Por favor, elija un número de la lista.")

    print(f"\n--- Iniciando Creación de Producto ---")
    print(f"URL: {shein_url_input}")
    print(f"Tallas: {product_sizes_list}")
    print(f"Ganancia: {markup_input_str}%") # Changed from "Descuento" to "Ganancia"
    print(f"Categoría Principal (Código): {gender_selection_str}")
    
    # Call the main orchestrator function
    crear_producto(
        tallas_list=product_sizes_list, 
        product_url_shein=shein_url_input, 
        markup_percentage_str=markup_input_str, # Pass as string, convert inside function
        gender_code_str=gender_selection_str
    )