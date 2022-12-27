import time
from woocommerce import API
from dotenv import load_dotenv
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service



from deep_translator import GoogleTranslator
from faker import Faker

load_dotenv()

fake = Faker()
fakename = Faker('es_CO')


list_of_domains = (
    'com',
    'com.br',
    'net',
    'net.br',
    'org',
    'org.br',
    'gov',
    'gov.br'
)

def fakemail():

    first_name = fake.first_name()    
    last_name = fake.last_name()    
    company = fake.company().split()[0].strip(',')

    dns_org = fake.random_choices(
        elements=list_of_domains,
        length=1
    )[0]
    
    email = f"{first_name}.{last_name}@{company}.{dns_org}".lower()
    
    return email


def crear_producto(tallas, url, discount, gender):
    
    if gender == "2": #
        print(f"El gender es Hombre: {gender}")
        dynamicat_list = [{"id": 184},{"id": 200},]
        dynamic_parent = 200
    elif gender == "1":
        print(f"El gender es Mujer: {gender}")
        dynamicat_list = [{"id": 183},{"id": 145}]
        dynamic_parent = 145
    elif gender == "5":
        print(f"El gender es Mujer Joyas: {gender}")
        dynamicat_list = [{"id": 183},{"id": 145}]
        dynamic_parent = 145
    elif gender == "6":
        print(f"El gender es Mujer Calzado: {gender}")
        dynamicat_list = [{"id": 183},{"id": 243}]
        dynamic_parent = 234
        

    print("####################### \n  INITIALIZED SCRAPER    \n#######################")

    time.sleep(5)

    wcapi = API(
    url="https://pjwaterfilters.com/",
    consumer_key=os.environ["CONSUMER_KEY"],
    consumer_secret=os.environ["CONSUMER_SECRET"],
    wp_api=True,
    version="wc/v3",
    timeout=60
)

    options = webdriver.ChromeOptions()


    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument("--start-maximized")
    
    options.add_argument("--lang=es")

    options.add_argument('log-level=3')
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    options.add_argument('--start-maximized')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)



    driver.set_page_load_timeout(120)

    driver.get(url)
    print("Going into:", url) 
    time.sleep(2)

   
    time.sleep(2)
    try:
        print("Cerrando Pop Up")
        time.sleep(2)
        
        popup = driver.find_elements("xpath", '//div[@class="c-coupon-box"]//i')
        
        
        if popup: 
            popup.click()
             
        time.sleep(2)

        product_name = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@class="product-intro__info"]//h1'))).text
        print(f"Nombre del producto: {product_name}")
        time.sleep(2)
        sku = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@class="product-intro__head-sku"]'))).text    

        sku = sku.strip()

        sku = sku.split("SKU: ")[1]

        raicsku = f"{sku}-raic-"

        precioshein = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@class="product-intro__head-price j-expose__product-intro__head-price"]/div[1]//span'))).text
        precioshein = float(precioshein.replace('$', ''))
        print(f"Precio Shein: {precioshein}")
        porcentaje_descuento = int(discount) / 100
        precio = str(precioshein - (precioshein * porcentaje_descuento))
        print(f"Precio tienda: {precio}")
        time.sleep(2)


        categoriashein = driver.find_elements("xpath", '//div[@class="bread-crumb__inner"]//div[@class="bread-crumb__item"][a or span]')
        
        sheincat = []

        for cat in categoriashein:
            categoria = cat.text
            categoria = categoria.replace("&", "&amp;")
            sheincat.append(categoria)
        
        sheincat = sheincat[1:-1]

        categories_to_remove = ['Hombre', 'Ropa de Mujer', 'Zapatos', 'Zapatos de Mujer']
        for category in categories_to_remove:
            if category in sheincat and category in categories_to_remove:
                sheincat.remove(category)
                print(f"Removido -> {category}")               
            else:
                pass


       
        raic_storecats = []

        imagenes = driver.find_element("xpath", '//div[@class="product-intro__thumbs-inner"]')

        divimgages = imagenes.find_elements("xpath", './/div[@class="product-intro__thumbs-item" or "product-intro__thumbs-inner"]')

        images = []
        
        for i in divimgages:   
            imagenen = i.find_element("xpath", './/img')        
            img_url = imagenen.get_attribute('src')
            img_url = img_url.split('_thumbnail_')[0]
            img_url = f"https:{img_url}.webp"
            images.append(img_url)
            time.sleep(2)            

        featuredimg = images[0]    
       
        url_imgs = []

        for url in images:
            if ".webp.webp" in url:
                url_imgs.remove(url)
                print("He removido una url de la lista porque tenia webp repetido")
        
        print(f"Lista de URL de imagenes: {images}")

        for link in images:
            url_imgs.append({"src": link})

        elicono = driver.find_element("xpath", '//div[@class="product-intro__description"]//i')
        elicono.click() 


        time.sleep(5)
        
        descriptions = driver.find_element("xpath", '//div[@class="product-intro__description"]//div[@class="product-intro__description-table"]')
        
        description = descriptions.find_elements("xpath", './/div[@class="product-intro__description-table-item"]')

        string_description = ""  

        last_iteration = False

        for i, desc in enumerate(description):
            if i == len(description) - 1:
                last_iteration = True
            key = desc.find_element("xpath", './/div[@class="key"]')
            value =  desc.find_element("xpath", './/div[@class="val"]')
            key = key.text
            value = value.text
            string_description += key + " " 
            string_description += value
            if not last_iteration:
                string_description += "\n"
                
        print(f"Descripcion: {string_description}")
        time.sleep(1)

        try:
            color = driver.find_element("xpath", '//div[@class="product-intro__color j-expose__product-intro__color"]/div/span/span').text
            print(f"Color: {color}") 
        except:
            color = False
            print(f"Color: {color}")
         
            
        reviews = driver.find_element("xpath", '//div[@class="common-reviews__list j-expose__common-reviews__list"]')

        review = reviews.find_elements("xpath", './/div[@class="j-expose__common-reviews__list-item"]')
        
        time.sleep(2)

        review_shein_esp = []
        
        for rev in review:
            print("Leyendo cada review")                   
            rate_desc = rev.find_element("xpath", './/div[@class="rate-des"]')
            rate_desc = rate_desc.text
            print(f"Texto Original: {rate_desc}")
            print("Traduciendo....")
            time.sleep(5)
            review_translated = GoogleTranslator(source='auto', target='es').translate(rate_desc)
            review_shein_esp.append(review_translated)
            print(f"Traducida: {review_translated}")
            time.sleep(5)
        
        cat_list = dynamicat_list
        
        categories = wcapi.get("products/categories", params={"per_page": 100}).json()

        for category in categories:
            name = category["name"]
            raic_storecats.append(name)

            if name in sheincat:                
                print(f"{name} - Si esta")
                catid = int(category["id"])
                cat_list.append({"id": catid})
                 
        for i, item in enumerate(sheincat):
            categories_for = wcapi.get("products/categories", params={"per_page": 100}).json()
            if item not in raic_storecats:                
                print(f"{item} no está en raic_storecats, posicion {i}.")

                if i != 0:
                    position_in_sheincat = i-1
                    
                    parent_name = sheincat[position_in_sheincat]

                    for category in categories_for:                               
                        if category["name"] == parent_name:  
                            parent = category['id']
                            print(f"El id de {parent_name} es: {parent}")
                            
                            data = {
                                'name': item,
                                'parent': parent
                            }

                            create_cat = wcapi.post("products/categories", data).json()

                            cat_created_id = create_cat["id"]
                            cat_list.append({"id": cat_created_id})
                            print(f"- Creada la categoria {item}")
                            time.sleep(3)
                            break  
                else: 
                    data = {
                            'name': item,
                            'parent': dynamic_parent
                        }
                    create_cat = wcapi.post("products/categories", data).json()
                    cat_created_id = create_cat["id"]

                    cat_list.append({"id": cat_created_id})
                    print(f"- Creada la categoria {item}")
                    time.sleep(3)
        
        print(f'IDs categorias a agregar al JSON: {cat_list}')

        attributes = [
            {
                "id": 7,
                "visible": True,
                "variation": True,
                "options": tallas,
            },
        ]

        if color:
            attributes.append(
                {
                    "id": 8,
                    "visible": True,
                    "variation": True,
                    "options": [color],
                }
            )

        variable_product_data = {
            "name": product_name,
            "type": "variable",
            "short_description": string_description,
            "description": string_description,
            "categories": categories,
            "images": url_imgs,
            "attributes": attributes,
        }

        print("Creando el producto, esto puede tardar unos 60 segundos...")
        response = wcapi.post("products", variable_product_data).json()
        id = response["id"]
        product_url = response["permalink"]

        print("Creando las variaciones talla/color")
        for talla in tallas:
            print(f"Talla a crear: {talla}")
            time.sleep(3)

            talla_sku = talla.replace(" ", "").lower()
            if color:
                color_sku = color.replace(" ", "").lower()
                sku_variation = f"{raicsku}{color_sku}{talla_sku}"
                attributes_variation = [
                    {"id": 8, "option": color},
                    {"id": 7, "option": talla},
                ]
            else:
                sku_variation = f"{raicsku}colorunico{talla_sku}"
                attributes_variation = [
                    {"id": 7, "option": talla},
                ]

            product_variation_data = {
                "regular_price": precio,
                "stock_quantity": 10,
                "sku": sku_variation,
                "image": {"src": featuredimg},
                "attributes": attributes_variation,
            }

            print(product_variation_data)
            response = wcapi.post(f"products/{id}/variations", product_variation_data)
   
        print("Agregando Reviews")
        for review in review_shein_esp:
            if gender == "1" or "4" or "6": # female or beauty or calzado de mujer
                reviewername = fakename.first_name_female()
            elif gender == "2": # male
                reviewername = fakename.first_name_male()
            elif gender == "3": # kids
                reviewername = fakename.first_name()

            datareview = {
            "product_id": id,
            "review": review,
            "reviewer":reviewername,
            "reviewer_email": fakemail(),
            "rating": 5,
            }
            
            wcapi.post("products/reviews", datareview).json()
            time.sleep(2)
        
        print(product_url)
        print("Done, producto agregado a la tienda")

    except Exception as e:
        print(e)
        driver.quit()    

    driver.quit()
    print("####################### \n  SCRAPER FINISHED    \n#######################")


url = input("Ingresa la URL de shein: ")
tallas = input("Ingrese las tallas separadas por comas sin espacios (ej: S,M,XL ej dos: M): ").split(",")
discount = input("Ingresa el descuento del producto sin el simbolo ej 20: ")
gender = input("Es Mujer(1), Hombre(2), Niños(3), Belleza(4),  Mujer Joyas (5), Mujer Calazado(6), Hombre Joyas(7), Hombre Calzado(8): ")

crear_producto(tallas, url, discount, gender)