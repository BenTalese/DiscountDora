import pathlib
from datetime import datetime
import tempfile

from jinja2 import Environment, PackageLoader, select_autoescape
from rich.console import Console
from rich.table import Table

# from framework.web_scraper.types import ProductOffers

_SCRIPT_DIR = pathlib.Path(__file__).parent.absolute()
_TEMPLATE_DIR = _SCRIPT_DIR / 'templates'


def generate_email_body(product_offers, out_path: str = None) -> str:
    """
    Returns a Mailersend email template populated from product_offers & save to out_path.
    :param product_offers: ProductOffers used for populating email template.
    :param out_path: optional, save destination for output email template.
    :return:
    """
    # Import HTML templates & snippets
    with open(_TEMPLATE_DIR / 'weekly.html', 'r', encoding="utf-8") as f:
        html_template = f.read()
    with open(_TEMPLATE_DIR / 'snippets/table.html', 'r', encoding="utf-8") as f:
        html_table = f.read()
    with open(_TEMPLATE_DIR / 'snippets/table_row.html', 'r', encoding="utf-8") as f:
        html_table_row: str = f.read()

    # Replace template variables
    rows = []
    green = '#008000'
    light_grey = '#afafaf'
    for product in product_offers:
        row_ = html_table_row
        row_ = row_.replace('{{ product }}', product_name)
        lowest_price = min(offers).price
        is_sales = any((offer.is_on_special for offer in offers))
        for offer in offers:
            merchant = offer.merchant
            price = offer.price if offer.price is not None else 'n/a'
            colour = green if is_sales and price == lowest_price else light_grey
            row_ = row_.replace('{{ %(merchant)s_price }}' % {"merchant": merchant},
                                f'<a href="{offer.link}" style="color:{colour};text-decoration:inherit;">${price}</a>')

        rows.append(row_)

    html_table = html_table.replace('{{ rows }}', ''.join(rows))
    html_template = html_template.replace('{{ table }}', html_table)

    # Add time
    year, week, weekday = datetime.now().isocalendar()
    week_start, week_fin = (week - 1, week) if weekday < 3 else (week, week + 1)
    #start = datetime.datetime.fromisocalendar(year, week_start, 3)
    #fin = datetime.datetime.fromisocalendar(year, week_fin, 2)
    #html_template = html_template.replace('{{ intro }}',
    #                                      f"Deals from {start.strftime('%a %d/%m')} till {fin.strftime('%a %d/%m')}")

    # Output formatted template
    if out_path:
        pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding="utf-8") as f:
            f.write(html_template)

    return html_template

def generate_html():
    stock_items = [
        {
            "name": "Apples",
            "products": [
                {"name": "Product 1", "brand": "Brand A", "current_offer": {"price_now": 19.99, "price_was": 29.99}, "availability": "In Stock", "seller": "Seller X", "size": "Medium", "image": None},
                {"name": "Product 2", "brand": "Brand B", "current_offer": {"price_now": 29.99, "price_was": 39.99}, "availability": "Out of Stock", "seller": "Seller Y", "size": "Large", "image": None},
                {"name": "Product 3", "brand": "Brand C", "current_offer": {"price_now": 14.99, "price_was": 29.99}, "availability": "In Stock", "seller": "Seller Z", "size": "Small", "image": None},
                {"name": "Product 4", "brand": "Brand D", "current_offer": {"price_now": 24.99, "price_was": 49.99}, "availability": "In Stock", "seller": "Seller W", "size": "Large", "image": None},
            ]
        },
        {
            "name": "Oranges",
            "products": [
                {"name": "Product 3", "brand": "Brand C", "current_offer": {"price_now": 14.99, "price_was": 29.99}, "availability": "In Stock", "seller": "Seller Z", "size": "Small", "image": None},
                {"name": "Product 4", "brand": "Brand D", "current_offer": {"price_now": 24.99, "price_was": 49.99}, "availability": "In Stock", "seller": "Seller W", "size": "Large", "image": None},
            ]
        },
        {
            "name": "Bananas",
            "products": [
                {"name": "Product 1", "brand": "Brand A", "current_offer": {"price_now": 19.99, "price_was": 29.99}, "availability": "In Stock", "seller": "Seller X", "size": "Medium", "image": None},
                {"name": "Product 2", "brand": "Brand B", "current_offer": {"price_now": 29.99, "price_was": 39.99}, "availability": "Out of Stock", "seller": "Seller Y", "size": "Large", "image": None},
                {"name": "Product 3", "brand": "Brand C", "current_offer": {"price_now": 14.99, "price_was": 29.99}, "availability": "In Stock", "seller": "Seller Z", "size": "Small", "image": None},
            ]
        },
        {
            "name": "Grapes",
            "products": [
                {"name": "Product 3", "brand": "Brand C", "current_offer": {"price_now": 14.99, "price_was": 29.99}, "availability": "In Stock", "seller": "Seller Z", "size": "Small", "image": None},
                {"name": "Product 4", "brand": "Brand D", "current_offer": {"price_now": 24.99, "price_was": 49.99}, "availability": "In Stock", "seller": "Seller W", "size": "Large", "image": None},
            ]
        },
    ]
    # env = Environment(
    #     loader=PackageLoader('framework.emailer'),
    #     autoescape=select_autoescape(['html', 'xml'])
    # )

    # # Load the HTML template
    # template = env.get_template('draft_email_template.html')

    # # Render the template with stock item data
    # html_content = template.render(stock_items=stock_items)

    email_template_path = 'framework/emailer/templates/mjml_test.mjml'

    html_content = compile_mjml_from_file(email_template_path)

    return html_content



import subprocess

def compile_mjml_from_file(file_path):
    try:
        mjml_cli_command = ["mjml", file_path]

        process = subprocess.Popen(mjml_cli_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output, error = process.communicate(timeout=10)

        if process.returncode != 0:
            print(f"Error compiling MJML: {error}") # FIXME: Logging
            return None

        html_start = output.find("<!doctype html>")
        html_end = output.find("</html>") + len("</html>")
        html_content = output[html_start:html_end]

        return html_content

    except Exception as e:
        print(f"An error occurred: {e}") # FIXME: Logging
        return None
















import subprocess

def compile_heml_from_file(file_path):
    try:
        # Create a temporary file to store the HTML output
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.html') as temp_file:
            temp_file_path = temp_file.name

            # HEML CLI command
            heml_command = ["heml", "build", file_path, "-o", temp_file_path]

            # Run the HEML CLI as a subprocess
            process = subprocess.Popen(heml_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            _, error = process.communicate(timeout=10)

            # Check for errors
            if process.returncode != 0:
                print(f"Error compiling HEML: {error}")
                return None

            # Read the HTML content from the temporary file
            with open(temp_file_path, 'r') as html_file:
                html_content = html_file.read()

            return html_content

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def heml_test():
    # Specify the path to your HEML file
    heml_file_path = 'framework/emailer/templates/heml_test.heml'

    # Compile HEML to HTML
    html_output = compile_heml_from_file(heml_file_path)

    # Print or use the HTML output as needed
    return html_output


