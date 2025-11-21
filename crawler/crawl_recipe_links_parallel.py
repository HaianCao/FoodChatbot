import os
import time
import traceback
import random
from pathlib import Path
from typing import Set, Optional
import concurrent.futures
import logging

import undetected_chromedriver as uc
from selenium.common.exceptions import WebDriverException

from packages.utils import safe_write_lines
from packages.selenium_handler import (
    create_driver, extract_links, wait_for_cloudflare, 
    no_more_links_found, skip_page_if_exists, fetch_page, close_popups,
    OUTPUT_DIR, PER_PAGE_RESULTS,
    POLITENESS_DELAY_MIN, POLITENESS_DELAY_MAX
)
from packages.logging_handler import setup_logging

# ============================================================================
# Configuration: Tunable Constants
# ============================================================================

MAX_PAGE_NUMBER: int = 2000  # Safety limit for pagination
MAX_CONSECUTIVE_ERRORS: int = 3  # Stop target if this many pages have no links

# Parallel configuration
DEFAULT_WORKERS: int = 3  # Number of worker processes

# Resume capability
CRAWL_FROM_URL: Optional[str] = None  # Resume from specific target URL
CRAWL_FROM_PAGE: Optional[int] = None  # Resume from specific page number


# ============================================================================
# Parallel Worker (Per-Target Crawl)
# ============================================================================

def crawl_one_target(
    target: str,
    blacklist: Set[str],
    headless: bool = True,
    start_page: int = 1,
) -> int:
    """
    Crawl a single target and save found links to disk.
    This function runs in a separate process via ProcessPoolExecutor.
    
    Args:
        target: Target URL to crawl (e.g., "https://example.com/recipes/")
        blacklist: Set of URLs to skip
        headless: Whether to run browser in headless mode
        start_page: Start crawling from this page number (for resume)
    
    Returns:
        Number of links found and saved for this target.
    """
    setup_logging()
    logging.info("Worker started for target: %s (starting from page %d)", target, start_page)
    
    driver = None
    result = set()
    
    try:
        driver = create_driver(headless)
        curr_page = start_page
        consecutive_errors = 0

        while curr_page <= MAX_PAGE_NUMBER:
            url_to_get = f"{target}page/{curr_page}/"
            logging.info("Crawling page %d: %s", curr_page, url_to_get)
            
            # Check if page already crawled (skip if SKIP_EXISTING_PAGES enabled)
            if skip_page_if_exists(target, curr_page):
                curr_page += 1
                time.sleep(random.uniform(POLITENESS_DELAY_MIN, POLITENESS_DELAY_MAX))
                continue

            # Fetch page robustly
            success, driver = fetch_page(driver, url_to_get, headless)
            if not success:
                logging.error("Failed to fetch page %s, stopping target.", url_to_get)
                break # Stop processing this target if a page fails to load

            # Close popups that might block content
            close_popups(driver)

            # Wait for Cloudflare (already handled in fetch_page, but can be a fallback)
            wait_for_cloudflare(driver)

            # Check for "Nothing Found"
            if no_more_links_found(driver):
                break

            # Extract links
            internal, external = extract_links(driver, target)
            if not external:
                logging.debug("No external links found on this page.")
                consecutive_errors += 1
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    logging.error("Too many consecutive errors, stopping.")
                    break
            else:
                consecutive_errors = 0
                result.update(external)
                
                # Save this page's results immediately if PER_PAGE_RESULTS enabled
                if PER_PAGE_RESULTS:
                    dir_to_create = (
                        target.replace("https://", "")
                        .replace("http://", "")
                        .replace("/", "_")
                    )
                    page_file_path = Path(OUTPUT_DIR) / dir_to_create / f"file{curr_page}.txt"
                    safe_write_lines(page_file_path, sorted(external))
                    logging.info("Saved page %d to %s (%d links)", curr_page, page_file_path, len(external))

            curr_page += 1
            time.sleep(random.uniform(POLITENESS_DELAY_MIN, POLITENESS_DELAY_MAX))

    except Exception as e:
        logging.error("Unhandled exception in worker for %s: %s", target, e)
        logging.debug(traceback.format_exc())
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception as e:
                logging.debug("Error quitting driver: %s", e)
            finally:
                driver = None

    # Save results
    if result:
        logging.info(
            "Finished crawling %s. Found %d links. Saving...",
            target,
            len(result),
        )
        dir_to_create = (
            target.replace("https://", "")
            .replace("http://", "")
            .replace("/", "_")
        )
        out_path = Path("data") / dir_to_create / "links.txt"
        try:
            safe_write_lines(out_path, sorted(result))
            logging.info("Saved to %s", out_path)
        except Exception as e:
            logging.error("Failed to save links for %s: %s", target, e)
    else:
        logging.info("No links found for %s", target)

    return len(result)


# ============================================================================
# Entry Point
# ============================================================================

def crawl() -> None:
    """Main parallel crawler entry point."""
    global CRAWL_FROM_URL, CRAWL_FROM_PAGE
    
    setup_logging()
    
    # Load targets and blacklist
    targets: Set[str] = set()
    blacklist: Set[str] = set()
    
    if Path("data/links.txt").exists():
        with open("data/links.txt", "r", encoding="utf-8") as f:
            for line in f:
                url = line.strip()
                if url:
                    targets.add(url)
    
    if Path("data/blacklist.txt").exists():
        with open("data/blacklist.txt", "r", encoding="utf-8") as f:
            for line in f:
                url = line.strip()
                if url:
                    blacklist.add(url)
    
    if not targets:
        logging.error("No targets found in data/links.txt")
        return
    
    # Determine number of workers
    num_workers = int(os.environ.get("WORKERS", str(DEFAULT_WORKERS)))
    num_workers = max(1, min(num_workers, os.cpu_count() or 2))
    
    headless_mode = os.environ.get("HEADLESS", "0") in ("1", "true", "True")
    
    logging.info("Starting parallel crawler: %d targets, %d workers, headless=%s", 
                 len(targets), num_workers, headless_mode)
    
    target_list = sorted(targets)
    
    # Handle resume: find starting point
    start_idx = 0
    start_page = 1
    
    if CRAWL_FROM_URL:
        if CRAWL_FROM_URL in target_list:
            start_idx = target_list.index(CRAWL_FROM_URL)
            start_page = CRAWL_FROM_PAGE if CRAWL_FROM_PAGE else 1
            logging.info("Resuming from URL: %s, page: %d", CRAWL_FROM_URL, start_page)
        else:
            logging.warning("Resume URL not found in targets, starting from beginning")
            CRAWL_FROM_URL = None
    
    # Process remaining targets
    remaining_targets = target_list[start_idx:]
    
    if not remaining_targets:
        logging.error("No targets to process")
        return
    
    logging.info("Processing %d targets (starting from index %d)", len(remaining_targets), start_idx)
    
    if num_workers == 1:
        # Single-worker mode (useful for debugging)
        logging.info("Running in single-worker mode")
        for i, target in enumerate(remaining_targets):
            # Use start_page only for first target
            page = start_page if i == 0 else 1
            crawl_one_target(target, blacklist, headless=headless_mode, start_page=page)
    else:
        # Multi-worker mode using ProcessPoolExecutor
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {}
            for i, target in enumerate(remaining_targets):
                # Use start_page only for first target
                page = start_page if i == 0 else 1
                future = executor.submit(
                    crawl_one_target,
                    target,
                    blacklist,
                    headless_mode,
                    page,
                )
                futures[future] = target
            
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                target = futures[future]
                try:
                    num_links = future.result()
                    logging.info("Completed %s -> %d links found", target, num_links)
                    completed += 1
                except Exception as e:
                    logging.error("Worker crashed for %s: %s", target, e)
                    logging.debug(traceback.format_exc())
            
            logging.info("Parallel crawl complete: %d/%d targets finished", completed, len(remaining_targets))


if __name__ == "__main__":
    crawl()

