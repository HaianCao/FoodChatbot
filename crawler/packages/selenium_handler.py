import time
import random
import logging
import subprocess
import undetected_chromedriver as uc
from pathlib import Path
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Set, Tuple, Optional
import threading
import os

# Optional: detect HTTP read timeout exceptions
try:
    from urllib3.exceptions import ReadTimeoutError as UrllibReadTimeout
except ImportError:
    UrllibReadTimeout = None

try:
    import requests
    RequestsReadTimeout = requests.exceptions.ReadTimeout
except ImportError:
    RequestsReadTimeout = None

# ============================================================================
# Configuration: Tunable Constants
# ============================================================================
PAGE_LOAD_TIMEOUT: int = 7  # Selenium page load timeout in seconds
WINDOW_WIDTH: int = 1024
WINDOW_HEIGHT: int = 768

CLOUDFLARE_CHECK_TIMEOUT: int = 30  # Wait for Cloudflare challenge in seconds
CLOUDFLARE_CHECK_POLL_INTERVAL: float = 1.0  # Poll page_source every 1s

# GUI window configuration (for manual Cloudflare solve)
GUI_WINDOW_WIDTH: int = 1200
GUI_WINDOW_HEIGHT: int = 900

# Fetch page configuration
MAX_FETCH_ATTEMPTS: int = 3  # Retry attempts per page (before skipping)
WATCHDOG_TIMEOUT: int = 7  # Seconds before timeout (will restart driver on Selenium timeout)
DRIVER_RESTART_DELAY: float = 0.5  # Wait before creating new driver
CLOUDFLARE_MANUAL_SOLVE_TIMEOUT: int = 600  # 10 minutes for user to solve

OUTPUT_DIR: str = "data"  # Directory to save per-page results

PER_PAGE_RESULTS: bool = True  # Save each page to separate file (file{page}.txt)
SKIP_EXISTING_PAGES: bool = True  # If True, skip pages that already have file{page}.txt saved

POLITENESS_DELAY_MIN: float = 0.5  # Minimum delay between page requests
POLITENESS_DELAY_MAX: float = 1.5  # Maximum delay between page requests

#==========================================================================
# Selenium WebDriver Helper Functions
#==========================================================================

def create_driver(headless: bool = False) -> uc.Chrome:
    """Create and configure an undetected ChromeDriver instance."""
    try:
        options = uc.ChromeOptions()
        # Disabling "none" strategy as it can be unreliable.
        # The fetch_page function will manage timeouts.
        # options.page_load_strategy = "none"
        driver = uc.Chrome(
            options=options, headless=headless, use_subprocess=False
        )
    except Exception as e:
        logging.debug("Failed to create Chrome with options, fallback: %s", e)
        driver = uc.Chrome(headless=headless, use_subprocess=False)

    try:
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    except Exception as e:
        logging.debug("Could not set page_load_timeout: %s", e)

    try:
        driver.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
    except Exception:
        pass

    return driver

def wait_for_cloudflare(driver: uc.Chrome, timeout: int = None) -> bool:
    """Wait until Cloudflare challenge disappears or timeout."""
    if timeout is None:
        timeout = CLOUDFLARE_CHECK_TIMEOUT
    logging.debug("Waiting for Cloudflare check (timeout=%s)...", timeout)
    start = time.time()
    while True:
        try:
            if "Just a moment..." not in driver.page_source:
                logging.debug("Cloudflare check passed.")
                return True
        except WebDriverException:
            logging.debug("Transient error reading page_source.")

        if time.time() - start > timeout:
            logging.warning("Cloudflare wait timed out after %s seconds.", timeout)
            return False

        time.sleep(CLOUDFLARE_CHECK_POLL_INTERVAL)


def safe_driver_get(driver: uc.Chrome, url: str, timeout_sec: int) -> Tuple[bool, Optional[Exception]]:
    """
    Execute driver.get(url) with a timeout using threading.
    Returns (success, exception_if_any).
    If timeout expires, returns (False, TimeoutException).
    """
    result = {"success": False, "exception": None}

    def do_get():
        try:
            driver.get(url)
            result["success"] = True
        except Exception as e:
            result["exception"] = e

    thread = threading.Thread(target=do_get, daemon=True)
    thread.start()
    thread.join(timeout=timeout_sec)

    if thread.is_alive():
        # The thread is still running, so it timed out
        result["exception"] = TimeoutException(f"driver.get timed out after {timeout_sec} seconds for url {url}")

    if result["exception"]:
        logging.debug("safe_driver_get failed: %s", result["exception"])

    return result["success"], result["exception"]


def restart_driver(current_driver: Optional[uc.Chrome], headless: bool) -> uc.Chrome:
    """Safely quit current driver and create a new one."""
    if current_driver is not None:
        logging.warning("Restarting driver...")
        try:
            current_driver.quit()
        except Exception:
            pass

    # Wait for ports to clear
    time.sleep(DRIVER_RESTART_DELAY + 1.0)

    # Try to create new driver with retries
    for attempt in range(1, 4):
        try:
            logging.info("Creating new driver (attempt %d)...", attempt)
            driver = create_driver(headless)
            logging.info("New driver created successfully.")
            return driver
        except Exception as e:
            logging.error("Failed to create driver on attempt %d: %s", attempt, e)
            time.sleep(2**attempt)  # Exponential backoff

    # Last resort
    logging.info("Creating new driver (last attempt)...")
    driver = create_driver(headless)
    return driver


def fetch_page(
    driver: uc.Chrome, url: str, headless: bool, max_attempts: int = None, watchdog_timeout: int = None
) -> Tuple[bool, uc.Chrome]:
    """
    Fetch a page with retries, timeout handling, and robust error recovery.
    Returns (success, updated_driver).
    """
    if max_attempts is None:
        max_attempts = MAX_FETCH_ATTEMPTS
    if watchdog_timeout is None:
        watchdog_timeout = WATCHDOG_TIMEOUT

    for attempt in range(1, max_attempts + 1):
        logging.info("Fetching URL (attempt %d/%d): %s", attempt, max_attempts, url)

        try:
            success, exception = safe_driver_get(driver, url, watchdog_timeout)

            if not success:
                if isinstance(exception, TimeoutException):
                    logging.error("Driver timed out after %d sec, restarting: %s", watchdog_timeout, url)
                    driver = restart_driver(driver, headless)
                    continue

                if UrllibReadTimeout and isinstance(exception, UrllibReadTimeout):
                    logging.warning("HTTP read timeout, retrying...")
                    time.sleep(2**attempt)
                    continue

                if isinstance(exception, WebDriverException):
                    logging.error("WebDriverException, restarting driver: %s", exception)
                    driver = restart_driver(driver, headless)
                    continue

                logging.error("Failed to get page (will retry): %s", exception)
                time.sleep(2**attempt)
                continue

            if "Checking if the site connection is secure" in driver.page_source:
                logging.warning("Cloudflare challenge detected...")

                if wait_for_cloudflare(driver):
                    logging.info("Cloudflare challenge solved automatically.")
                    return True, driver

                if not headless:
                    logging.info("Attempting manual Cloudflare solve...")
                    if manual_solve_cloudflare(driver, url):
                        logging.info("Cloudflare manually solved.")
                        return True, driver
                    else:
                        logging.error("Manual Cloudflare solve failed or timed out.")
                        driver = restart_driver(driver, headless)
                        continue
                else:
                    logging.error("Cloudflare challenge requires manual solve, but in headless mode. Restarting driver.")
                    driver = restart_driver(driver, headless)
                    continue

            logging.debug("Page fetched successfully: %s", url)
            return True, driver

        except WebDriverException as e:
            logging.error("Unhandled WebDriverException on attempt %d: %s", attempt, e)
            if "net::ERR_CONNECTION_RESET" in str(e):
                logging.warning("Connection reset, retrying with backoff...")
                time.sleep(2**attempt)
                continue

            logging.info("Restarting driver due to WebDriverException...")
            driver = restart_driver(driver, headless)

        except Exception as e:
            logging.error("Generic exception on attempt %d for %s: %s", attempt, url, e)
            time.sleep(2**attempt)

    logging.critical("Failed to fetch page after %d attempts: %s", max_attempts, url)
    return False, driver


def manual_solve_cloudflare(
    headless_driver: uc.Chrome, url: str, timeout: int = None
) -> bool:
    """
    Spawn a visible browser to let user manually solve Cloudflare challenge.
    Copy cookies back to headless driver on success.
    """
    if timeout is None:
        timeout = CLOUDFLARE_MANUAL_SOLVE_TIMEOUT
    logging.info("Spawning visible browser for manual Cloudflare solve: %s", url)
    gui = None
    try:
        opts = uc.ChromeOptions()
        opts.add_argument(f"--window-size={GUI_WINDOW_WIDTH},{GUI_WINDOW_HEIGHT}")
        gui = uc.Chrome(options=opts, headless=False)
        gui.get(url)

        logging.info("Waiting for user to solve Cloudflare (up to %d seconds)...", timeout)
        start_time = time.time()
        solved = False
        while time.time() - start_time < timeout:
            if "Checking if the site connection is secure" not in gui.page_source:
                logging.info("Cloudflare challenge appears to be solved in GUI browser.")
                solved = True
                break
            time.sleep(2)

        if solved:
            logging.info("Copying cookies from GUI to headless driver...")
            all_cookies = gui.get_cookies()

            headless_driver.get(url)

            for cookie in all_cookies:
                try:
                    headless_driver.add_cookie(cookie)
                except Exception as e:
                    logging.warning("Could not add cookie: %s -> %s", cookie.get("name"), e)

            logging.info("Cookies copied. Reloading page in headless driver.")
            headless_driver.refresh()
            return True
        else:
            logging.error("Cloudflare manual solve timed out.")
            return False

    except Exception as e:
        logging.error("Error during manual Cloudflare solve: %s", e)
        return False
    finally:
        if gui:
            try:
                gui.quit()
            except Exception:
                pass


def close_popups(driver: uc.Chrome) -> None:
    """Close any modal popups or overlays that might be blocking the page."""
    try:
        # This will need to be adapted for the specific site's popups
        close_buttons = driver.find_elements(By.CSS_SELECTOR, "button.close, [aria-label='Close']")
        for button in close_buttons:
            try:
                if button.is_displayed() and button.is_enabled():
                    logging.info("Closing a popup...")
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(1)
            except Exception as e:
                logging.debug("Could not click popup close button: %s", e)

        # Fallback: press ESC key
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            logging.info("Sent ESC key to close potential popups.")
        except Exception as e:
            logging.debug("Could not send ESC key: %s", e)

    except Exception as e:
        logging.debug("No popups found or error closing them: %s", e)


def wait_for_element(driver: uc.Chrome, selector: str, timeout: int = 10) -> bool:
    """
    Wait for an element to be present and visible on the page.
    
    Args:
        driver: The Chrome WebDriver instance
        selector: CSS selector for the element to wait for
        timeout: Maximum seconds to wait
    
    Returns:
        True if element found and visible, False if timeout
    """
    try:
        logging.debug("Waiting for element '%s' (timeout %ds)...", selector, timeout)
        wait = WebDriverWait(driver, timeout)
        element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        logging.debug("Element '%s' found and visible", selector)
        return True
    except Exception as e:
        logging.debug("Timeout waiting for element '%s': %s", selector, e)
        return False
    
# ===========================================================================
# Helper Functions For Crawling Links From Single Page (to get initial category links)
# ===========================================================================

def extract_links_01(target: str):
    driver = uc.Chrome(headless=False,use_subprocess=True)
    driver.get(target)
    result = []
    wait_for_cloudflare(driver)
    wait_for_element(driver, "a", timeout=10)
    links = driver.find_elements("tag name", "a")
    for link in links:
        href = link.get_attribute("href")
        if href:
            result.append(href)
    with open(f"{OUTPUT_DIR}/links.txt", "w", encoding="utf-8") as f:
        f.write("")
    for url in result:
        with open(f"{OUTPUT_DIR}/links.txt", "a", encoding="utf-8") as f:
            f.write(url + "\n")
    driver.quit()
    
# ===========================================================================
# Helper Functions For Crawling Links From Category Pages (to get all recipe links)
# ===========================================================================

def no_more_links_found(driver: uc.Chrome) -> bool:
    wait_for_element(driver, "body", timeout=5)
    try:
        if "Nothing Found" in driver.page_source:
            logging.info("No more pages to crawl.")
            return True
    except WebDriverException:
        pass
    return False

def extract_links(driver: uc.Chrome, target_domain: str) -> Tuple[Set[str], Set[str]]:
    """
    Extract links from page_source.
    Returns (internal_links_for_crawl, external_links_for_result).
    """
    internal_links = set()
    external_links = set()

    try:
        wait_for_element(driver, "a", timeout=10)
        links = driver.find_elements(By.TAG_NAME, "a")
    except WebDriverException as e:
        logging.warning("find_elements failed: %s", e)
        return internal_links, external_links

    for link in links:
        try:
            href = link.get_attribute("href")
        except WebDriverException:
            continue

        if not href or not isinstance(href, str):
            continue

        try:
            if target_domain in href and "#" not in href:
                internal_links.add(href)
        except Exception as e:
            logging.debug("Error checking internal link %r: %s", href, e)

        external_links.add(href)

    return internal_links, external_links

def skip_page_if_exists(target: str, page_number: int) -> bool:
    """Check if page file already exists and should be skipped."""
    if SKIP_EXISTING_PAGES and PER_PAGE_RESULTS:
        dir_to_create = (
            target.replace("https://", "")
            .replace("http://", "")
            .replace("/", "_")
        )
        page_file_path = Path(OUTPUT_DIR) / dir_to_create / f"file{page_number}.txt"
        if page_file_path.exists():
            logging.info("Page %d already crawled (file exists). Skipping.", page_number)
            return True
    return False

# ===========================================================================
# Helper Functions For Crawling Info From Recipe Pages
# ===========================================================================

def get_text_from_all_children(driver: uc.Chrome, element) -> str:
    """Extract text including all child elements using JavaScript."""
    try:
        result = driver.execute_script("""
        if (typeof jQuery === 'undefined') return arguments[0].innerText;
        return jQuery(arguments[0]).text();
        """, element)
        return result or ""
    except Exception as e:
        logging.debug("get_text_from_all_children failed: %s", e)
        try:
            return element.text or ""
        except:
            return ""


def get_text_excluding_children(driver: uc.Chrome, element) -> str:
    """Extract text excluding child elements using JavaScript."""
    try:
        result = driver.execute_script("""
        if (typeof jQuery === 'undefined') return arguments[0].nodeValue;
        return jQuery(arguments[0]).contents().filter(function() {
            return this.nodeType == Node.TEXT_NODE;
        }).text();
        """, element)
        return result or ""
    except Exception as e:
        logging.debug("get_text_excluding_children failed: %s", e)
        try:
            return element.text or ""
        except:
            return ""


def get_text_excluding_classes(driver: uc.Chrome, element, excluded_classes: list) -> str:
    """Extract text excluding elements with certain classes using JavaScript."""
    try:
        result = driver.execute_script("""
        if (typeof jQuery === 'undefined') return arguments[0].innerText;
        function getTextExcludingClasses(element, excludedClasses) {
            let text = "";
            jQuery(element).contents().each(function() {
                if (this.nodeType === Node.TEXT_NODE) {
                    text += this.nodeValue;
                } else if (this.nodeType === Node.ELEMENT_NODE) {
                    let skip = false;
                    for (let cls of excludedClasses) {
                        if (jQuery(this).hasClass(cls)) {
                            skip = true;
                            break;
                        }
                    }
                    if (!skip) {
                        text += getTextExcludingClasses(this, excludedClasses);
                    }
                }
            });
            return text;
        }
        return getTextExcludingClasses(arguments[0], arguments[1]);
        """, element, excluded_classes)
        return result or ""
    except Exception as e:
        logging.debug("get_text_excluding_classes failed: %s", e)
        try:
            return element.text or ""
        except:
            return ""


def get_text_including_children(driver: uc.Chrome, element, depth: int) -> str:
    """Extract text including child elements up to a certain depth using JavaScript."""
    try:
        result = driver.execute_script("""
        if (typeof jQuery === 'undefined') return arguments[0].innerText;
        function getTextWithDepth(element, depth) {
            if (depth === 0) return "";
            let text = jQuery(element).contents().filter(function() {
                return this.nodeType == Node.TEXT_NODE;
            }).text();
            jQuery(element).children().each(function() {
                text += getTextWithDepth(this, depth - 1);
            });
            return text;
        }
        return getTextWithDepth(arguments[0], arguments[1]);
        """, element, depth)
        return result or ""
    except Exception as e:
        logging.debug("get_text_including_children failed: %s", e)
        try:
            return element.text or ""
        except:
            return ""


def get_children_elements(driver: uc.Chrome, element, selector: str) -> list:
    """Get child elements matching selector using JavaScript."""
    try:
        result = driver.execute_script("""
        if (typeof jQuery === 'undefined') return [];
        return jQuery(arguments[0]).find(arguments[1]).toArray();
        """, element, selector)
        return result or []
    except Exception as e:
        logging.debug("get_children_elements failed: %s", e)
        return []
    
def get_summary(driver: uc.Chrome) -> str:
    try:
        if not wait_for_element(driver, ".wprm-recipe-summary", timeout=3):
            logging.debug("Summary element not found")
            return ""
        return get_text_from_all_children(driver=driver, element=driver.find_element(By.CSS_SELECTOR, ".wprm-recipe-summary"))
    except Exception as e:
        logging.debug("Failed to get summary: %s", e)
        return ""


def get_metadata(driver: uc.Chrome) -> list:
    metadatas = []
    try:
        if not wait_for_element(driver, ".wprm-recipe-meta-container", timeout=3):
            logging.debug("Metadata container not found")
            return metadatas
        for div in get_children_elements(driver=driver, element=driver.find_element(By.CSS_SELECTOR, ".wprm-recipe-meta-container"), selector="div"):
            metadatas.append(get_text_including_children(driver=driver, element=div, depth=3))
    except Exception as e:
        logging.debug("Failed to get metadata: %s", e)
    return metadatas


def get_ingredients(driver: uc.Chrome) -> list:
    ingredients = []
    try:
        if not wait_for_element(driver, ".wprm-recipe-ingredient", timeout=3):
            logging.debug("Ingredients not found")
            return ingredients
        for ingredient in driver.find_elements(By.CSS_SELECTOR, ".wprm-recipe-ingredient"):
            ingredients.append(get_text_excluding_classes(driver=driver, element=ingredient, excluded_classes=["wprm-checkbox-container"]).strip())
    except Exception as e:
        logging.debug("Failed to get ingredients: %s", e)
    return ingredients


def get_instructions(driver: uc.Chrome) -> list:
    instructions = []
    try:
        if not wait_for_element(driver, ".wprm-recipe-instruction", timeout=3):
            logging.debug("Instructions not found")
            return instructions
        for instruction in driver.find_elements(By.CSS_SELECTOR, ".wprm-recipe-instruction"):
            instructions.append(get_text_from_all_children(driver=driver, element=instruction).strip())
    except Exception as e:
        logging.debug("Failed to get instructions: %s", e)
    return instructions


def get_nutrition(driver: uc.Chrome) -> list:
    nutritions = []
    try:
        if not wait_for_element(driver, ".wprm-nutrition-label-text-nutrition-container", timeout=3):
            logging.debug("Nutrition data not found")
            return nutritions
        for nutrition in driver.find_elements(By.CSS_SELECTOR, ".wprm-nutrition-label-text-nutrition-container"):
            nutritions.append(get_text_from_all_children(driver=driver, element=nutrition).strip())
    except Exception as e:
        logging.debug("Failed to get nutrition: %s", e)
    return nutritions


def get_comments(driver: uc.Chrome) -> list:
    comments = []
    try:
        if not wait_for_element(driver, ".comment-list li article", timeout=3):
            logging.debug("Comments section not found (may not have comments)")
            return comments
        for comment in driver.find_elements(By.CSS_SELECTOR, ".comment-list li article"):
            comments.append(get_text_excluding_classes(driver=driver, element=comment, excluded_classes=["reply", "comment-metadata"]).strip().replace("\t", "").replace("\n", ""))
    except Exception as e:
        logging.debug("Failed to get comments: %s", e)
    return comments


def will_crawl(driver: uc.Chrome) -> bool:
    page_source = driver.page_source
    if "Cook Mode" in page_source:
        return True
    logging.info("Cook Mode not detected; skipping crawl.")
    return False