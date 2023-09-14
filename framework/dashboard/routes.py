from flask import render_template, request

#TODO: Look into Blueprint
def index():
    return render_template("index.html")


# @app.route('/search', methods=['POST'])
# def search_products():
#     search_term = request.form['search_term']
#     max_page_search = 1  # Set your desired max page search
#     # products = search(search_term, max_page_search)

#     # for product in products:
#     #     # Save the scraped data to the database
#     #     db_product = Product(
#     #         Stockcode=product.Stockcode,
#     #         DisplayName=product.DisplayName,
#     #         # Map other attributes...
#     #     )
#     #     db.session.add(db_product)
#     #     db.session.commit()

#     return render_template('index.html', products=["Hello"])
