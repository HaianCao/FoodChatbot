from packages.selenium_handler import extract_links_01
from packages.utils import filter_blacklist, load_url_file

if __name__ == "__main__":
    test_url = "https://therecipecritic.com/recipe-box/"
    extract_links_01(test_url)
    filter_blacklist(load_url_file("data/links.txt"), load_url_file("data/blacklist.txt"), "data/links.txt")