# TheRecipeCritic.com Crawler

This is a robust, multi-stage web crawler designed to scrape recipe data from `therecipecritic.com`. It is built with Python and utilizes Selenium with `undetected-chromedriver` to handle dynamic web content and bypass bot detection.

The crawler is designed for resilience and performance, featuring parallel processing, automatic error recovery, and a modular architecture.

## Features

- **Multi-Stage Pipeline**: The crawling process is broken down into logical, sequential steps.
- **Parallel Execution**: Utilizes both multiprocessing (`concurrent.futures`) and multithreading to significantly speed up the crawling process.
- **Robust Error Handling**:
    - **Watchdog Timers**: Prevents the crawler from hanging on unresponsive pages by restarting the browser driver if a page load exceeds a timeout.
    - **Automatic Driver Restarts**: Automatically restarts the WebDriver in worker threads upon encountering unexpected errors.
    - **Retry Logic**: The underlying page fetching mechanism includes retries for transient network issues.
- **Cloudflare Bypass**: Integrates `undetected-chromedriver` to navigate Cloudflare's anti-bot measures.
- **Resume Capability**: The crawler can be stopped and resumed from a specific URL or page number, preventing the need to restart from scratch.
- **Modular & Clean Code**: The codebase is organized into a `packages` directory with handlers for Selenium logic, logging, and utilities, promoting code reuse and maintainability.
- **Configurable**: Key parameters like the number of workers, headless mode, and politeness delays can be configured via environment variables or constants.
- **Data Persistence**: Saves extracted recipe links and detailed recipe information to the `data/` directory. Recipe details are stored as individual JSON files.

## Structure

```
.
├── packages/
│   ├── selenium_handler.py # Core Selenium logic, driver creation, data extraction
│   ├── logging_handler.py  # Centralized logging configuration
│   └── utils.py            # Utility functions (file I/O, etc.)
│
├── crawl_category_links.py       # Stage 1: Fetches main category links.
├── crawl_recipe_links_parallel.py  # Stage 2: Crawls categories for recipe links (parallel).
├── crawl_recipe_infos_parallel.py  # Stage 3: Crawls recipes for details (parallel).
│
├── requirements.txt        # dependencies.
├── data/                   # Output directory for scraped data.
│   ├── links.txt           # Initial category links.
│   ├── combined.txt        # All individual recipe links.
│   └── foods/              # JSON files for each scraped recipe.
└── readme.md               # This file.
```

## Pipeline and How to Run

### 1. Installation

First, install the required Python packages:

```bash
pip install -r requirements.txt
```

### 2. Execution Pipeline

The crawler operates in three distinct stages. Run them in the following order:

**Stage 1: Crawl Category Links**

This script fetches the initial list of recipe categories from the main site and saves them to `data/links.txt`.

```bash
python crawl_category_links.py
```

**Stage 2: Crawl Recipe Links from Categories (Parallel)**

This script reads the category URLs from `data/links.txt` and crawls each one in parallel to find all individual recipe links. The results are saved in `data/combined.txt`.

```bash
python crawl_recipe_links_parallel.py
```

**Stage 3: Crawl Recipe Information (Parallel)**

This is the final stage. The script reads the individual recipe URLs from `data/combined.txt` and crawls each one in parallel to extract detailed information (summary, ingredients, instructions, etc.). The data for each recipe is saved as a separate JSON file in the `data/foods/` directory.

```bash
python crawl_recipe_infos_parallel.py
```

## Configuration

You can control the crawler's behavior using environment variables:

- **`WORKERS`**: Sets the number of parallel workers (processes or threads) to use.
  - Example: `set WORKERS=4` (Windows CMD)
  - Example: `export WORKERS=4` (Linux/macOS)
  - Defaults to `3` if not set.

- **`HEADLESS`**: Runs the browser in headless mode (no visible UI). Set to `1` or `true`.
  - Example: `set HEADLESS=1`
  - Defaults to `0` (visible browser) if not set.

- **`SKIP_EXISTING_PAGES`**: If set to `true`, the crawler will skip crawling pages for which an output file already exists. This is useful for resuming an interrupted crawl.
  - This is configured as a constant in the scripts themselves.

- **`CRAWL_FROM_URL` / `CRAWL_FROM_PAGE`**: Constants within the scripts that can be set to resume a crawl from a specific point.
