from flask import Flask, request
import os

app = Flask(__name__)
app.config["DEBUG"] = False

####-----------URL CONFIGURATION-------------####
apiHostIP = "localhost"
apiHostPort = 7020
####-----------URL CONFIGURATION-------------####

@app.route('/', methods=['GET'])
def home():
    with open('search_items.txt', 'r', encoding="utf-8") as file:   groceries = file.read().splitlines()
    with open('index.html', 'r', encoding="utf-8") as file:         html_page = file.read()
    with open('table.html', 'r', encoding="utf-8") as file:         html_table = file.read()
    with open('table_row.html', 'r', encoding="utf-8") as file:     html_table_row: str = file.read()

    products = [product.split("<->") for product in groceries]
    print(products)
    rows = []
    for product in products:
        row = html_table_row
        row = row.replace('{{ product_id }}', product[0])
        row = row.replace('{{ product_name }}', product[1])
        rows.append(row)

    next_id = int(products[-1][0])+1
    html_table = html_table.replace('{{ rows }}', ''.join(rows))
    html_page = html_page.replace('{{ grocery_table }}', html_table)

    return html_page

@app.route('/create', methods=['GET'])
def get_create_page():
    with open('create.html', 'r', encoding="utf-8") as file:
        return file.read()

@app.route('/update/<product_id>', methods=['GET'])
def get_update_page(product_id):
    with open('update.html', 'r', encoding="utf-8") as file:
        return file.read()

@app.route('/delete/<product_id>', methods=['GET'])
def get_delete_page(product_id):
    with open('delete.html', 'r', encoding="utf-8") as file:
        return file.read()

@app.route('/create', methods=['POST'])
def create():
    product_name = request.form.get("product_name")

    # TODO: find out if these could be combined by changing r and a into one of: r+, rb+ or a+
    with open('search_items.txt', 'r', encoding="utf-8") as file:
        next_available_id = int([product.split("<->") for product in file.read().splitlines()][-1][0])+1 # this looks complex, but it's just a combination of above lines of code
    
    with open('search_items.txt', 'a', encoding="utf-8") as file:
        file.write(f"{next_available_id}<->{product_name}\n")

    return home()

@app.route('/update/<product_id>', methods=['POST'])
def update(product_id):
    return home()

@app.route('/delete/<product_id>', methods=['POST'])
def delete(product_id):
    return home()

app.run (host = apiHostIP, port = apiHostPort)