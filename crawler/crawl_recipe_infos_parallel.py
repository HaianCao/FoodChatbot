
"""
Parallel crawler for extracting detailed recipe information from a list of URLs for FoodChatbot.

Features:
    - Multithreading for concurrent crawling
    - Automatic resume capability
    - Saves each recipe as a JSON file

Usage:
    python crawl_recipe_infos_parallel.py

Author: FoodChatbot Team
"""

import os
import time
import logging
import traceback
import random
import threading
import subprocess
import json
import queue
from pathlib import Path
from typing import Set, Optional, Tuple

import undetected_chromedriver as uc
from selenium.common.exceptions import WebDriverException

from packages.utils import combine_files, safe_write_lines, load_url_file
from packages.selenium_handler import (
    create_driver, wait_for_cloudflare, wait_for_element,
    get_summary, get_metadata, get_ingredients, get_instructions,
    get_nutrition, get_comments, will_crawl, fetch_page, restart_driver, close_popups,
    OUTPUT_DIR, SKIP_EXISTING_PAGES,
    POLITENESS_DELAY_MIN, POLITENESS_DELAY_MAX
)
from packages.logging_handler import setup_logging

# ============================================================================
# Configuration: Tunable Constants
# ============================================================================

# Input targets configuration
INPUT_TARGETS_FILE: str = "data/combined.txt"

# Parallel worker configuration
NUM_WORKERS: int = 3
QUEUE_TIMEOUT: int = 60

# Global state for resume capability
CRAWL_FROM_URL: Optional[str] = None  # Set to URL to resume from that point

# Load initial targets and blacklist
TARGETS: Set[str] = load_url_file(INPUT_TARGETS_FILE)
BLACKLIST: Set[str] = load_url_file("data/blacklist.txt")

# Global queue for worker threads
target_queue: queue.Queue = queue.Queue()
results_lock = threading.Lock()
results_count = {"success": 0, "failed": 0, "skipped": 0}

# ============================================================================
# Worker Function
# ============================================================================

def crawl_target(driver: uc.Chrome, target_url: str, headless: bool) -> Tuple[bool, uc.Chrome]:
    """
    Crawl a recipe URL and extract recipe data fields.

    Args:
        driver (uc.Chrome): The current Chrome WebDriver instance.
        target_url (str): The recipe URL to crawl.
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        Tuple[bool, uc.Chrome]:
            - success (bool): True if crawl succeeded or was skipped, False if failed.
            - driver (uc.Chrome): The possibly restarted driver instance.
    """
    try:
        filename = target_url.replace("https://therecipecritic.com/", "").replace("/", "_")
        output_dir = Path(f"{OUTPUT_DIR}/foods")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{filename}.json"
        
        if output_path.exists() and SKIP_EXISTING_PAGES:
            logging.info("Output file exists, skipping: %s", output_path)
            return True, driver
        logging.info("Processing: %s", target_url)
        
        # Fetch the page using robust fetch_page function
        success, driver = fetch_page(driver, target_url, headless)
        if not success:
            logging.error("Failed to fetch page, skipping: %s", target_url)
            return False, driver
        
        # Close popups that might block content
        close_popups(driver)

        # Wait for the main recipe content to load
        if not wait_for_element(driver, ".wprm-recipe-summary", timeout=5):
            logging.warning("Recipe content did not load for %s", target_url)
            return False, driver
        
        # Wait for Cloudflare
        wait_for_cloudflare(driver)
        
        if not will_crawl(driver):
            logging.info("Skipping crawl for %s", target_url)
            return False, driver
        
        logging.info("Crawling target: %s", target_url)
        summary = get_summary(driver)
        metadata = get_metadata(driver)
        ingredients = get_ingredients(driver)
        instructions = get_instructions(driver)
        nutrition = get_nutrition(driver)
        comments = get_comments(driver)
        to_save = {
            "URL": target_url,
            "Summary": summary,
            "Metadata": metadata,
            "Ingredients": ingredients,
            "Instructions": instructions,
            "Nutrition": nutrition,
            "Comments": comments,
        }

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=2, ensure_ascii=False)
        logging.info("Saved crawl data to %s", output_path)
        return True, driver
        
    except Exception as e:
        logging.error("Error crawling target %s: %s", target_url, e)
        logging.debug(traceback.format_exc())
        return False, driver


def worker_thread(worker_id: int, headless: bool) -> None:
    """
    Worker thread that processes URLs from the queue for parallel crawling.

    Args:
        worker_id (int): The worker's ID (starting from 1).
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        None
    """
    logging.info("Worker %d started", worker_id)
    driver = None
    
    try:
        driver = create_driver(headless)
        
        while True:
            try:
                # Get target from queue with timeout
                target_url = target_queue.get(timeout=QUEUE_TIMEOUT)
                
                if target_url is None:  # Sentinel value to stop worker
                    logging.info("Worker %d received stop signal", worker_id)
                    break
                
                # Process target
                success, driver = crawl_target(driver, target_url, headless)
                
                # Update results
                with results_lock:
                    if success:
                        results_count["success"] += 1
                    else:
                        results_count["failed"] += 1
                
                # Polite delay
                time.sleep(random.uniform(POLITENESS_DELAY_MIN, POLITENESS_DELAY_MAX))
                
                target_queue.task_done()
                
            except queue.Empty:
                logging.info("Worker %d queue timeout, exiting", worker_id)
                break
            except Exception as e:
                logging.error("Worker %d error: %s", worker_id, e)
                logging.debug(traceback.format_exc())
                
                with results_lock:
                    results_count["failed"] += 1
                
                try:
                    target_queue.task_done()
                except Exception:
                    pass

                # Restart driver on any unexpected error
                try:
                    driver = restart_driver(driver, headless)
                except Exception as e2:
                    logging.critical("Worker %d failed to restart driver: %s", worker_id, e2)
                    break
    
    except Exception as e:
        logging.critical("Worker %d initialization failed: %s", worker_id, e)
    finally:
        if driver is not None:
            try:
                # Delete all cookies first
                driver.delete_all_cookies()
            except Exception:
                pass
            
            try:
                # Then close all windows
                for window_handle in driver.window_handles:
                    try:
                        driver.switch_to.window(window_handle)
                        driver.close()
                    except Exception:
                        pass
            except Exception:
                pass
            
            try:
                # Finally quit the driver
                driver.quit()
            except Exception:
                pass
        
        logging.info("Worker %d stopped", worker_id)


# ============================================================================
# Main Function
# ============================================================================

def crawl() -> None:
    """
    Main function to start the parallel crawler, manage the queue and workers, and summarize results.

    - Combines input files and sets up logging.
    - Initializes the queue and worker threads.
    - Waits for all crawling tasks to complete and prints a summary.
    - Cleans up Chrome processes after crawling.

    Returns:
        None
    """
    combine_files("data", "data/combined.txt")
    setup_logging()
    
    headless_mode = os.environ.get("HEADLESS", "0") in ("1", "true", "True")
    logging.info("Starting parallel crawler: %d targets, %d workers, headless=%s", 
                 len(TARGETS), NUM_WORKERS, headless_mode)
    
    # Populate queue with targets
    target_list = sorted(TARGETS)
    
    # Filter targets to start from CRAWL_FROM_URL if specified
    if CRAWL_FROM_URL:
        try:
            start_index = target_list.index(CRAWL_FROM_URL)
            target_list = target_list[start_index:]
            logging.info("Resuming from: %s", CRAWL_FROM_URL)
        except ValueError:
            logging.warning("CRAWL_FROM_URL %s not found in targets, starting from beginning", CRAWL_FROM_URL)
    
    logging.info("Crawling %d targets", len(target_list))
    
    for target in target_list:
        target_queue.put(target)
    
    # Create and start worker threads
    workers = []
    for i in range(NUM_WORKERS):
        worker = threading.Thread(
            target=worker_thread,
            args=(i + 1, headless_mode),
            name=f"Worker-{i+1}",
            daemon=False
        )
        worker.start()
        workers.append(worker)
    
    # Wait for all tasks to be processed
    target_queue.join()
    
    # Send stop signals
    for _ in range(NUM_WORKERS):
        target_queue.put(None)
    
    # Wait for workers to finish
    for worker in workers:
        worker.join(timeout=30)
    
    # Print final results
    with results_lock:
        total = results_count["success"] + results_count["failed"] + results_count["skipped"]
        logging.info(
            "Crawl complete: %d success, %d failed, %d skipped (total: %d)",
            results_count["success"],
            results_count["failed"],
            results_count["skipped"],
            total
        )
    
    # Final cleanup
    time.sleep(2)  # Wait for workers to fully exit
    try:
        subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                     capture_output=True, timeout=5)
        subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], 
                     capture_output=True, timeout=5)
        logging.info("Cleanup: Killed remaining Chrome processes")
    except Exception as e:
        logging.debug("Cleanup: Could not kill Chrome processes: %s", e)


if __name__ == "__main__":
    crawl()
