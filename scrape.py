"""
CSE and Stockwatch Time & Sales Data Scraper

Scrapes publicly available delayed time & sales data from:
- CSE website: extracts broker attribution, outputs structured JSON and CSV files
- Stockwatch website: extracts trade data with authentication, outputs JSON files
"""

import json
import csv
import os
import argparse
from datetime import datetime
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from auth import load_stockwatch_auth


# Placeholder broker code mapping
# Format: broker_code -> broker_name
BROKER_MAP = {
    '085': 'Canaccord',
    '080': 'RBC',
    # Add more broker codes as needed
}


def scrape_cse_trades(symbol: str = "DOCT") -> List[Dict]:
    """ 
    Scrape time & sales data from CSE website for the given symbol.
    
    Args:
        symbol: Stock ticker symbol (default: "DOCT")
    
    Returns:
        List of trade dictionaries with timestamp, price, volume, broker codes
    """
    # Construct URL - for DOCT, it's republic-technologies-inc
    # For other symbols, this would need to be mapped or constructed differently
    if symbol.upper() == "DOCT":
        url = "https://thecse.com/listings/republic-technologies-inc/"
    else:
        # Generic URL pattern - may need adjustment for other symbols
        url = f"https://thecse.com/listings/{symbol.lower()}/"
    
    trades = []
    
    try:
        with sync_playwright() as p:
            # Launch browser (headless mode)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to the page
            print(f"Loading page for {symbol}...")
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait a bit for JavaScript to fully render
            page.wait_for_timeout(2000)
            
            print(f"\n=== DEBUG: Looking for 'Depth Display' section ===")
            
            # Find the section with h2 containing "Depth Display"
            table_found = False
            table_html = None
            found_selector = None
            
            try:
                # Method 1: Find h2 with "Depth Display" text, then find table in same section
                print("  Method 1: Searching for h2 with 'Depth Display' text...")
                h2_elements = page.query_selector_all('h2')
                print(f"  Found {len(h2_elements)} h2 element(s)")
                
                for h2_idx, h2 in enumerate(h2_elements):
                    h2_text = h2.inner_text().strip()
                    print(f"    H2 {h2_idx + 1}: '{h2_text}'")
                    
                    if 'depth display' in h2_text.lower():
                        print(f"  ✓ Found 'Depth Display' h2!")
                        
                        # Use JavaScript to find the section and table
                        try:
                            result = page.evaluate('''(h2) => {
                                const section = h2.closest("section");
                                if (!section) return null;
                                const table = section.querySelector("table");
                                return table ? table.outerHTML : null;
                            }''', h2)
                            
                            if result:
                                table_html = result
                                table_found = True
                                found_selector = "section[h2='Depth Display'] > table"
                                print(f"  ✓ Found table in Depth Display section using JavaScript")
                                break
                        except Exception as e:
                            print(f"    Error using JavaScript method: {e}")
                
                # Method 2: If JavaScript method didn't work, find all sections and check manually
                if not table_found:
                    print(f"\n  Method 2: Searching all sections manually...")
                    all_sections = page.query_selector_all('section')
                    print(f"  Found {len(all_sections)} section(s)")
                    
                    for section_idx, section in enumerate(all_sections):
                        h2_elements_in_section = section.query_selector_all('h2')
                        for h2 in h2_elements_in_section:
                            h2_text = h2.inner_text().strip()
                            if 'depth display' in h2_text.lower():
                                print(f"    Section {section_idx + 1}: Found 'Depth Display' h2")
                                table_elem = section.query_selector('table')
                                if table_elem:
                                    table_html = table_elem.inner_html()
                                    table_found = True
                                    found_selector = f"section[{section_idx}] > table"
                                    print(f"  ✓ Found table in section {section_idx + 1}")
                                    break
                        if table_found:
                            break
                
                # Method 3: Fallback - find table by structure (Bid Broker, Ask Broker)
                if not table_found:
                    print(f"\n  Method 3: Fallback - searching all tables for Depth Display structure...")
                    all_tables = page.query_selector_all('table')
                    print(f"  Found {len(all_tables)} total table(s) on page")
                    
                    for idx, table_elem in enumerate(all_tables):
                        table_html_candidate = table_elem.inner_html()
                        html_lower = table_html_candidate.lower()
                        
                        # Check if this table has the Depth Display structure
                        if 'bid broker' in html_lower and 'ask broker' in html_lower:
                            print(f"    Table {idx + 1}: Matches Depth Display structure")
                            table_found = True
                            table_html = table_html_candidate
                            found_selector = f"table[{idx}] (by structure)"
                            break
                
            except Exception as e:
                print(f"  Error searching for Depth Display section: {e}")
                import traceback
                traceback.print_exc()
            
            # Save HTML to file for inspection
            debug_html_file = f"{symbol.lower()}_debug_table.html"
            with open(debug_html_file, 'w', encoding='utf-8') as f:
                f.write(table_html if table_html else "No HTML captured")
            print(f"\n=== DEBUG: Saved captured HTML to {debug_html_file} ===")
            
            browser.close()
            
            if not table_found or not table_html:
                print(f"\n✗ Error: Time & Sales table not found on page for {symbol}")
                print("The page structure may have changed or the data may not be available.")
                print(f"Check {debug_html_file} to see what was captured.")
                return trades
            
            print(f"\n=== DEBUG: Parsing table HTML ===")
            print(f"Using selector: {found_selector}")
            print(f"HTML length: {len(table_html)} characters")
            
            # Parse the HTML table
            soup = BeautifulSoup(table_html, 'html.parser')
            table = soup.find('table')
            
            if not table:
                print(f"✗ Error: BeautifulSoup could not find <table> tag in HTML")
                print(f"HTML structure preview:")
                print(f"  First 500 chars: {table_html[:500]}")
                print(f"  Last 500 chars: {table_html[-500:]}")
                print(f"\nPlease check {debug_html_file} and provide:")
                print(f"  - The exact class or ID of the table")
                print(f"  - The structure of the table (is it nested?)")
                return trades
            
            print(f"✓ Found <table> tag")
            
            # Log table attributes
            table_class = table.get('class', [])
            table_id = table.get('id', '')
            print(f"  Table class: {table_class}")
            print(f"  Table id: {table_id}")
            
            # Find header row to identify column positions
            print(f"\n=== DEBUG: Analyzing table structure ===")
            all_rows = table.find_all('tr')
            print(f"Total <tr> elements found: {len(all_rows)}")
            
            header_row = table.find('tr')
            if not header_row:
                print(f"✗ Error: No <tr> elements found in table")
                print(f"Table HTML structure:")
                print(f"  {str(table)[:500]}...")
                return trades
            
            print(f"✓ Found header row")
            
            # Check for th vs td in header
            th_elements = header_row.find_all('th')
            td_elements = header_row.find_all('td')
            print(f"  <th> elements in header: {len(th_elements)}")
            print(f"  <td> elements in header: {len(td_elements)}")
            
            headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
            print(f"  Headers found: {headers}")
            print(f"  Header count: {len(headers)}")
            
            # Map column names to indices
            print(f"\n=== DEBUG: Mapping columns ===")
            col_indices = {}
            is_depth_display = False  # Track if this is Depth Display (Bid/Ask) table
            
            # Check if this is a Depth Display table (has Bid/Ask columns)
            headers_lower = [h.lower() for h in headers]
            if 'bid' in ' '.join(headers_lower) and 'ask' in ' '.join(headers_lower):
                is_depth_display = True
                print("  Detected: Depth Display table (Bid/Ask structure)")
            
            for idx, header in enumerate(headers):
                header_clean = header.strip().lower()
                print(f"  Column {idx}: '{header}'", end="")
                
                if 'time' in header_clean or 'timestamp' in header_clean:
                    col_indices['timestamp'] = idx
                    print(f" → timestamp")
                elif 'bid broker' in header_clean:
                    col_indices['buyer'] = idx  # Map Bid Broker to buyer_broker
                    print(f" → buyer_broker (from Bid Broker)")
                elif 'ask broker' in header_clean:
                    col_indices['seller'] = idx  # Map Ask Broker to seller_broker
                    print(f" → seller_broker (from Ask Broker)")
                elif 'buyer' in header_clean and 'broker' in header_clean:
                    col_indices['buyer'] = idx
                    print(f" → buyer_broker")
                elif 'seller' in header_clean and 'broker' in header_clean:
                    col_indices['seller'] = idx
                    print(f" → seller_broker")
                elif 'price' in header_clean:
                    if 'bid price' in header_clean:
                        col_indices['bid_price'] = idx
                        # Also use bid price as primary price if no other price found
                        if 'price' not in col_indices:
                            col_indices['price'] = idx
                        print(f" → bid_price (and price)")
                    elif 'ask price' in header_clean:
                        col_indices['ask_price'] = idx
                        # Use ask price as price if bid price not available
                        if 'price' not in col_indices:
                            col_indices['price'] = idx
                        print(f" → ask_price (and price)")
                    elif 'bid' not in header_clean and 'ask' not in header_clean:
                        col_indices['price'] = idx
                        print(f" → price")
                elif 'volume' in header_clean or 'size' in header_clean:
                    if 'bid size' in header_clean:
                        col_indices['bid_size'] = idx
                        # Also use bid size as volume if no other volume found
                        if 'volume' not in col_indices:
                            col_indices['volume'] = idx
                        print(f" → bid_size (and volume)")
                    elif 'ask size' in header_clean:
                        col_indices['ask_size'] = idx
                        # Use ask size as volume if bid size not available
                        if 'volume' not in col_indices:
                            col_indices['volume'] = idx
                        print(f" → ask_size (and volume)")
                    elif 'bid' not in header_clean and 'ask' not in header_clean:
                        col_indices['volume'] = idx
                        print(f" → volume")
                elif 'trade' in header_clean and 'id' in header_clean:
                    col_indices['trade_id'] = idx
                    print(f" → trade_id")
                else:
                    print(f" → (unmapped)")
            
            print(f"\nColumn mapping result: {col_indices}")
            
            # If we couldn't find columns by name, assume standard order
            if not col_indices:
                print("⚠ Warning: Could not identify columns by header names, using default order")
                col_indices = {
                    'timestamp': 0,
                    'price': 1,
                    'volume': 2,
                    'buyer': 3,
                    'seller': 4
                }
                print(f"  Using default mapping: {col_indices}")
            
            # Parse data rows
            rows = table.find_all('tr')[1:]  # Skip header row
            print(f"\n=== DEBUG: Processing data rows ===")
            print(f"Found {len(rows)} data row(s) (excluding header)")
            
            if len(rows) == 0:
                print("⚠ Warning: No data rows found")
                print("Sample of first row HTML:")
                if all_rows:
                    print(f"  {str(all_rows[0])[:300]}...")
            
            for row_idx, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:  # Need at least timestamp, price, volume
                    print(f"  Row {row_idx + 1}: Skipped - only {len(cells)} cells found")
                    continue
                
                print(f"  Row {row_idx + 1}: Processing {len(cells)} cells", end="")
                
                try:
                    # Extract timestamp (may be empty for Depth Display tables)
                    timestamp = ""
                    if 'timestamp' in col_indices and col_indices['timestamp'] < len(cells):
                        timestamp = cells[col_indices['timestamp']].get_text(strip=True)
                    
                    # Extract price (use bid price, ask price, or general price)
                    price = None
                    if 'price' in col_indices and col_indices['price'] < len(cells):
                        price_str = cells[col_indices['price']].get_text(strip=True)
                        # Remove currency symbols and commas
                        price_str = price_str.replace('$', '').replace(',', '').strip()
                        try:
                            price = float(price_str)
                        except ValueError:
                            pass  # Don't fail, just skip price
                    
                    # Extract volume (use bid size, ask size, or general volume)
                    volume = None
                    if 'volume' in col_indices and col_indices['volume'] < len(cells):
                        volume_str = cells[col_indices['volume']].get_text(strip=True)
                        # Remove commas
                        volume_str = volume_str.replace(',', '').strip()
                        try:
                            volume = int(volume_str)
                        except ValueError:
                            pass  # Don't fail, just skip volume
                    
                    # Extract buyer broker (from Bid Broker or Buyer Broker)
                    buyer_broker = ""
                    if 'buyer' in col_indices and col_indices['buyer'] < len(cells):
                        buyer_broker = cells[col_indices['buyer']].get_text(strip=True)
                    
                    # Extract seller broker (from Ask Broker or Seller Broker)
                    seller_broker = ""
                    if 'seller' in col_indices and col_indices['seller'] < len(cells):
                        seller_broker = cells[col_indices['seller']].get_text(strip=True)
                    
                    # Extract trade ID (optional)
                    trade_id = None
                    if 'trade_id' in col_indices and col_indices['trade_id'] < len(cells):
                        trade_id = cells[col_indices['trade_id']].get_text(strip=True)
                    
                    # For Depth Display tables, we might not have all required fields
                    # Still create the record if we have at least broker information
                    if not buyer_broker and not seller_broker and not price:
                        print(f" ✗ Skipped - no extractable data")
                        continue
                    
                    # Get current date for timestamp (YYYY-MM-DD format)
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    
                    # Create trade dictionary
                    trade = {
                        "timestamp": current_date,  # Use current date as timestamp
                        "price": price,
                        "volume": volume,
                        "buyer_broker": buyer_broker,
                        "seller_broker": seller_broker
                    }
                    
                    # Add trade_id if available
                    if trade_id:
                        trade["trade_id"] = trade_id
                    
                    # Add bid/ask specific fields if this is a Depth Display table
                    if is_depth_display:
                        if 'bid_price' in col_indices and col_indices['bid_price'] < len(cells):
                            bid_price_str = cells[col_indices['bid_price']].get_text(strip=True).replace('$', '').replace(',', '').strip()
                            try:
                                trade["bid_price"] = float(bid_price_str)
                            except:
                                pass
                        if 'ask_price' in col_indices and col_indices['ask_price'] < len(cells):
                            ask_price_str = cells[col_indices['ask_price']].get_text(strip=True).replace('$', '').replace(',', '').strip()
                            try:
                                trade["ask_price"] = float(ask_price_str)
                            except:
                                pass
                        if 'bid_size' in col_indices and col_indices['bid_size'] < len(cells):
                            bid_size_str = cells[col_indices['bid_size']].get_text(strip=True).replace(',', '').strip()
                            try:
                                trade["bid_size"] = int(bid_size_str)
                            except:
                                pass
                        if 'ask_size' in col_indices and col_indices['ask_size'] < len(cells):
                            ask_size_str = cells[col_indices['ask_size']].get_text(strip=True).replace(',', '').strip()
                            try:
                                trade["ask_size"] = int(ask_size_str)
                            except:
                                pass
                    
                    trades.append(trade)
                    print(f" ✓")
                    
                except Exception as e:
                    print(f" ✗ Error: {e}")
                    print(f"    Row HTML: {str(row)[:200]}...")
                    continue
            
            print(f"Successfully extracted {len(trades)} trades")
            
    except PlaywrightTimeoutError:
        print(f"Error: Timeout while loading page for {symbol}")
    except Exception as e:
        print(f"Error: Failed to scrape data for {symbol}: {e}")
        import traceback
        traceback.print_exc()
    
    return trades


def login_stockwatch(page, username: str, password: str) -> bool:
    """
    Log in to Stockwatch using username and password.
    
    Uses specific element IDs from Stockwatch homepage:
    - Username: id="PowerUserName"
    - Password: id="PowerPassword"
    - Login button: id="Login"
    
    Args:
        page: Playwright page object
        username: Stockwatch username
        password: Stockwatch password
    
    Returns:
        True if login successful, False otherwise
    """
    try:
        # Navigate to Stockwatch homepage (login form is on homepage)
        homepage_url = "https://www.stockwatch.com/"
        print(f"  Navigating to Stockwatch homepage...")
        # Use domcontentloaded instead of networkidle - more reliable
        page.goto(homepage_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)  # Give page time to fully render
        
        # Find username input field by ID
        username_input_id = "PowerUserName"
        print(f"  Looking for username field (id={username_input_id})...")
        username_input = page.query_selector(f"#{username_input_id}")
        if not username_input:
            raise ValueError(f"Could not find username input field with id '{username_input_id}'")
        print(f"  ✓ Found username field")
        
        # Find password input field by ID
        password_input_id = "PowerPassword"
        print(f"  Looking for password field (id={password_input_id})...")
        password_input = page.query_selector(f"#{password_input_id}")
        if not password_input:
            raise ValueError(f"Could not find password input field with id '{password_input_id}'")
        print(f"  ✓ Found password field")
        
        # Find login button by ID
        login_button_id = "Login"
        print(f"  Looking for login button (id={login_button_id})...")
        login_button = page.query_selector(f"#{login_button_id}")
        if not login_button:
            raise ValueError(f"Could not find login button with id '{login_button_id}'")
        print(f"  ✓ Found login button")
        
        # Fill in credentials
        print(f"  Entering credentials...")
        print(f"    Username value: '{username[:10]}...' (length: {len(username)})")
        print(f"    Password value: {'*' * min(len(password), 10)}... (length: {len(password)})")
        username_input.fill(username)
        password_input.fill(password)
        
        # Verify what was actually entered (for debugging)
        entered_username = username_input.input_value()
        print(f"    Verified username in field: '{entered_username[:10]}...'")
        
        # Click login button
        print(f"  Clicking login button...")
        login_button.click()
        
        # Wait for navigation/redirect after login
        page.wait_for_timeout(3000)
        
        # Check if login was successful
        current_url = page.url
        page_content = page.content().lower()
        
        # Check for error messages
        error_indicators = ["invalid", "incorrect", "error", "failed", "wrong", "trouble logging"]
        for indicator in error_indicators:
            if indicator in page_content:
                print(f"  ✗ Login failed - found '{indicator}' in page content")
                return False
        
        # If we're still on homepage but no errors, might be logged in
        # Or if redirected away, definitely logged in
        if "login" not in current_url.lower() or "stockwatch.com" in current_url:
            print(f"  ✓ Login successful! Current URL: {current_url}")
            return True
        else:
            print(f"  ⚠ Login status unclear - still on: {current_url}")
            return True  # Assume success if no errors found
    
    except Exception as e:
        print(f"  ✗ Error during login: {e}")
        import traceback
        traceback.print_exc()
        return False


def scrape_stockwatch_trades(symbol: str = "DOCT", date: str = None) -> List[Dict]:
    """
    Scrape trades data from Stockwatch website for the given symbol and date.
    
    Args:
        symbol: Stock ticker symbol (default: "DOCT")
        date: Date in yyyymmdd format (optional - defaults to today)
    
    Returns:
        List of trade dictionaries with Time ET, Exchange, Price, Change, Volume, Buyer, Seller, Markers
    """
    # Default to today's date if not provided
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    # Validate date format
    try:
        datetime.strptime(date, "%Y%m%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date}. Expected format: yyyymmdd (e.g., 20240115)")
    
    trades = []
    
    try:
        # Load authentication data
        print(f"Loading Stockwatch authentication...")
        auth_data = load_stockwatch_auth()
        
        username = auth_data["username"].strip()
        password = auth_data["password"].strip()
        
        # Validate that credentials are not placeholders
        placeholder_values = ["your_username_here", "your_password_here", ""]
        if username in placeholder_values or password in placeholder_values:
            raise ValueError(
                f"❌ ERROR: Placeholder credentials found in secrets.json!\n"
                f"  Current username: '{username}'\n"
                f"  Current password: '{'*' * len(password) if password else '(empty)'}'\n"
                f"  Please update secrets.json with your actual Stockwatch username and password."
            )
        
        # Debug: Show what credentials were loaded (mask password)
        username_preview = username[:3] + "..." if len(username) > 3 else username
        password_preview = "*" * min(len(password), 10)
        print(f"  Loaded credentials - Username: {username_preview}, Password: {password_preview}")
        
        with sync_playwright() as p:
            # Launch browser in visible mode for debugging
            browser = p.chromium.launch(headless=False, slow_mo=500)
            context = browser.new_context()
            page = context.new_page()
            
            # Login with username and password
            print(f"  Logging in with username: {username}")
            login_success = login_stockwatch(page, username, password)
            if not login_success:
                print(f"  ⚠ Warning: Login may have failed, continuing anyway...")
                print(f"  You can check the browser window to see what happened")
            
            # Navigate to Stockwatch homepage to search for symbol
            homepage_url = "https://www.stockwatch.com/"
            print(f"Navigating to Stockwatch homepage...")
            # Use domcontentloaded instead of networkidle for faster/more reliable loading
            page.goto(homepage_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)  # Give page time to fully render
            
            # Search for symbol using search box
            search_input_id = "TextSymbol2"
            search_button_id = "GoButton2"
            print(f"Searching for symbol {symbol}...")
            try:
                search_input = page.query_selector(f"#{search_input_id}")
                if not search_input:
                    raise ValueError(f"Search input with id '{search_input_id}' not found on page")
                search_input.fill(symbol)
                print(f"  ✓ Entered symbol in search box")
                
                search_button = page.query_selector(f"#{search_button_id}")
                if not search_button:
                    raise ValueError(f"Search button with id '{search_button_id}' not found on page")
                search_button.click()
                print(f"  ✓ Clicked search button")
                
                # Wait for search results to load
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"Error searching for symbol: {e}")
                raise ValueError(f"Failed to search for symbol: {e}")
            
            # Find and click "More trades..." link
            print(f"Looking for 'More trades...' link...")
            try:
                # Try to find link by text content
                more_trades_link = page.query_selector('a:has-text("More trades")')
                if not more_trades_link:
                    # Try alternative text variations
                    more_trades_link = page.query_selector('a:has-text("More Trades")')
                if not more_trades_link:
                    more_trades_link = page.query_selector('a[href*="Trades"]')
                
                if not more_trades_link:
                    raise ValueError("Could not find 'More trades...' link on page")
                
                print(f"  ✓ Found 'More trades...' link")
                more_trades_link.click()
                print(f"  ✓ Clicked 'More trades...' link")
                
                # Wait for trades page to load
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"Error clicking 'More trades...' link: {e}")
                raise ValueError(f"Failed to navigate to trades page: {e}")
            
            # Fill date input
            date_input_id = "MainContent_TradesDate"
            print(f"Setting date to {date}...")
            try:
                date_input = page.query_selector(f"#{date_input_id}")
                if not date_input:
                    raise ValueError(f"Date input with id '{date_input_id}' not found on page")
                date_input.fill(date)
                print(f"  ✓ Entered date")
                
                # Press Enter to close the calendar popup
                print(f"  Pressing Enter to close calendar popup...")
                date_input.press("Enter")
                page.wait_for_timeout(1000)  # Wait for calendar to close
                print(f"  ✓ Calendar closed")
            except Exception as e:
                print(f"Error filling date input: {e}")
                raise ValueError(f"Failed to set date: {e}")
            
            # Click submit button
            submit_button_id = "MainContent_TradesSubmit"
            print(f"Clicking submit button...")
            try:
                submit_button = page.query_selector(f"#{submit_button_id}")
                if not submit_button:
                    raise ValueError(f"Submit button with id '{submit_button_id}' not found on page")
                submit_button.click()
                print(f"  ✓ Clicked submit button")
            except Exception as e:
                print(f"Error clicking submit button: {e}")
                raise ValueError(f"Failed to submit form: {e}")
            
            # Wait for table to load - give it more time and wait for it to be visible
            table_id = "MainContent_TradeList_Table1_Table1"
            print(f"Waiting for trades table to load...")
            try:
                # Wait for the table to appear and be visible (increased timeout to 30 seconds)
                page.wait_for_selector(f"#{table_id}", state="visible", timeout=30000)
                print(f"  ✓ Table found, waiting for it to fully render...")
                
                # Wait additional time for table content to load
                page.wait_for_timeout(3000)
                
                # Verify table has content (has rows)
                table_element = page.query_selector(f"#{table_id}")
                if table_element:
                    # Check if table has rows
                    rows = table_element.query_selector_all("tr")
                    if len(rows) > 0:
                        print(f"  ✓ Table loaded with {len(rows)} row(s)")
                    else:
                        print(f"  ⚠ Table found but appears to be empty")
                else:
                    raise ValueError(f"Table element not found after waiting")
                    
            except PlaywrightTimeoutError:
                print(f"  ✗ Warning: Table with id '{table_id}' did not appear within 30 seconds")
                # Check if there's a message indicating no trades
                page_content = page.content()
                if "no trades" in page_content.lower() or "no data" in page_content.lower():
                    print(f"  No trades found for {symbol} on {date}")
                    browser.close()
                    return trades
                else:
                    # Try to get the page HTML for debugging
                    print(f"  Page URL: {page.url}")
                    print(f"  Attempting to find table anyway...")
                    # Don't raise error yet, try to find it one more time
            
            # Get table HTML
            table_html = page.query_selector(f"#{table_id}")
            if not table_html:
                print(f"  ✗ Error: Could not find table element with id '{table_id}'")
                # Debug: show what tables are on the page
                all_tables = page.query_selector_all("table")
                print(f"  Found {len(all_tables)} table(s) on page")
                for idx, tbl in enumerate(all_tables):
                    tbl_id = tbl.get_attribute("id") or "no-id"
                    print(f"    Table {idx + 1}: id='{tbl_id}'")
                browser.close()
                return trades
            
            # Get outer HTML to include the table tag itself
            try:
                table_html_content = table_html.evaluate("el => el.outerHTML")
            except:
                # Fallback: get inner HTML and wrap it
                inner_html = table_html.inner_html()
                table_html_content = f'<table id="{table_id}">{inner_html}</table>'
            
            print(f"  ✓ Retrieved table HTML ({len(table_html_content)} characters)")
            
            browser.close()
            
            # Parse table HTML with BeautifulSoup
            print(f"Parsing trades table...")
            soup = BeautifulSoup(table_html_content, 'html.parser')
            table = soup.find('table', id=table_id)
            
            # If not found by ID, try finding any table
            if not table:
                table = soup.find('table')
            
            if not table:
                print(f"Error: Could not find <table> tag in HTML")
                print(f"HTML preview (first 500 chars): {table_html_content[:500]}")
                return trades
            
            print(f"  ✓ Found table tag")
            
            # Find header row - look in thead first, then in tbody
            header_row = None
            thead = table.find('thead')
            if thead:
                header_row = thead.find('tr')
            
            if not header_row:
                # Fallback: find first tr in table
                header_row = table.find('tr')
            if not header_row:
                print(f"Error: No header row found in table")
                return trades
            
            # Extract column headers
            headers = []
            for th in header_row.find_all(['th', 'td']):
                header_text = th.get_text(strip=True)
                headers.append(header_text)
            
            print(f"  Found {len(headers)} columns: {headers}")
            
            # Map column headers to field names
            col_indices = {}
            for idx, header in enumerate(headers):
                header_lower = header.lower()
                if 'time' in header_lower and 'et' in header_lower:
                    col_indices['time_et'] = idx
                elif 'exchange' in header_lower or 'ex' in header_lower:
                    col_indices['exchange'] = idx
                elif 'price' in header_lower:
                    col_indices['price'] = idx
                elif 'change' in header_lower:
                    col_indices['change'] = idx
                elif 'volume' in header_lower:
                    col_indices['volume'] = idx
                elif 'buyer' in header_lower:
                    col_indices['buyer'] = idx
                elif 'seller' in header_lower:
                    col_indices['seller'] = idx
                elif 'marker' in header_lower or 'markers' in header_lower:
                    col_indices['markers'] = idx
            
            print(f"  Column mapping: {col_indices}")
            
            # Parse data rows - look in tbody
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
            else:
                # Fallback: get all rows except header
                all_rows = table.find_all('tr')
                rows = all_rows[1:] if len(all_rows) > 1 else []
            
            print(f"  Found {len(rows)} trade row(s)")
            
            for row_idx, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:  # Need at least a few columns
                    continue
                
                try:
                    trade = {}
                    
                    # Extract Time ET
                    if 'time_et' in col_indices and col_indices['time_et'] < len(cells):
                        trade['time_et'] = cells[col_indices['time_et']].get_text(strip=True)
                    
                    # Extract Exchange
                    if 'exchange' in col_indices and col_indices['exchange'] < len(cells):
                        trade['exchange'] = cells[col_indices['exchange']].get_text(strip=True)
                    
                    # Extract Price (convert to float)
                    if 'price' in col_indices and col_indices['price'] < len(cells):
                        price_str = cells[col_indices['price']].get_text(strip=True)
                        price_str = price_str.replace('$', '').replace(',', '').strip()
                        try:
                            trade['price'] = float(price_str)
                        except ValueError:
                            trade['price'] = None
                    
                    # Extract Change (convert to float)
                    if 'change' in col_indices and col_indices['change'] < len(cells):
                        change_str = cells[col_indices['change']].get_text(strip=True)
                        change_str = change_str.replace('$', '').replace(',', '').replace('+', '').strip()
                        try:
                            trade['change'] = float(change_str)
                        except ValueError:
                            trade['change'] = None
                    
                    # Extract Volume (convert to int)
                    if 'volume' in col_indices and col_indices['volume'] < len(cells):
                        volume_str = cells[col_indices['volume']].get_text(strip=True)
                        volume_str = volume_str.replace(',', '').strip()
                        try:
                            trade['volume'] = int(volume_str)
                        except ValueError:
                            trade['volume'] = None
                    
                    # Extract Buyer
                    if 'buyer' in col_indices and col_indices['buyer'] < len(cells):
                        trade['buyer'] = cells[col_indices['buyer']].get_text(strip=True)
                    
                    # Extract Seller
                    if 'seller' in col_indices and col_indices['seller'] < len(cells):
                        trade['seller'] = cells[col_indices['seller']].get_text(strip=True)
                    
                    # Extract Markers
                    if 'markers' in col_indices and col_indices['markers'] < len(cells):
                        trade['markers'] = cells[col_indices['markers']].get_text(strip=True)
                    
                    # Add symbol and date to trade record
                    trade['symbol'] = symbol.upper()
                    trade['date'] = date
                    
                    # Only add trade if it has at least some data
                    if trade.get('price') is not None or trade.get('volume') is not None:
                        trades.append(trade)
                
                except Exception as e:
                    print(f"  Error parsing row {row_idx + 1}: {e}")
                    continue
            
            print(f"Successfully extracted {len(trades)} trades")
    
    except FileNotFoundError as e:
        print(f"Authentication error: {e}")
        raise
    except ValueError as e:
        print(f"Error: {e}")
        raise
    except PlaywrightTimeoutError:
        print(f"Error: Timeout while loading Stockwatch page for {symbol}")
    except Exception as e:
        print(f"Error: Failed to scrape Stockwatch data for {symbol}: {e}")
        import traceback
        traceback.print_exc()
    
    return trades


def save_stockwatch_trades(trades: List[Dict], filename: str = "trades.json") -> None:
    """
    Save Stockwatch trades data to JSON file.
    
    Uses append mode to accumulate data over time. Handles existing file gracefully.
    
    Args:
        trades: List of trade dictionaries
        filename: Output JSON filename (default: "trades.json")
    """
    try:
        existing_trades = []
        if os.path.isfile(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_trades = json.load(f)
                print(f"  Loaded {len(existing_trades)} existing records from {filename}")
            except (json.JSONDecodeError, FileNotFoundError):
                # File exists but is empty or invalid, start fresh
                existing_trades = []
        
        # Combine existing and new trades
        all_trades = existing_trades + trades
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_trades, f, indent=2, ensure_ascii=False)
        
        action = "Appended" if existing_trades else "Saved"
        print(f"{action} {len(trades)} trades to {filename} (total: {len(all_trades)})")
    except Exception as e:
        print(f"Error saving Stockwatch trades to {filename}: {e}")


def save_to_json(trades: List[Dict], filename: str, append: bool = True) -> None:
    """
    Save trades data to JSON file.
    
    Args:
        trades: List of trade dictionaries
        filename: Output JSON filename
        append: If True, append to existing file; if False, overwrite
    """
    try:
        existing_trades = []
        if append and os.path.isfile(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_trades = json.load(f)
                print(f"  Loaded {len(existing_trades)} existing records from {filename}")
            except (json.JSONDecodeError, FileNotFoundError):
                # File exists but is empty or invalid, start fresh
                existing_trades = []
        
        # Combine existing and new trades
        all_trades = existing_trades + trades
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_trades, f, indent=2, ensure_ascii=False)
        
        action = "Appended" if existing_trades else "Saved"
        print(f"{action} {len(trades)} trades to {filename} (total: {len(all_trades)})")
    except Exception as e:
        print(f"Error saving JSON file {filename}: {e}")


def save_to_csv(trades: List[Dict], filename: str, append: bool = True) -> None:
    """
    Save trades data to CSV file.
    
    Args:
        trades: List of trade dictionaries
        filename: Output CSV filename
        append: If True, append to existing file; if False, overwrite
    """
    if not trades:
        print("No trades to save to CSV")
        return
    
    try:
        # Determine if file exists and if we should write header
        file_exists = os.path.isfile(filename) and append
        write_header = not file_exists
        
        # Get all unique keys from all trades (in case some have trade_id and others don't)
        fieldnames = set()
        for trade in trades:
            fieldnames.update(trade.keys())
        fieldnames = sorted(list(fieldnames))
        
        # Ensure standard order: timestamp, price, volume, buyer_broker, seller_broker, trade_id
        preferred_order = ['timestamp', 'price', 'volume', 'buyer_broker', 'seller_broker', 'trade_id']
        fieldnames = [f for f in preferred_order if f in fieldnames] + [f for f in fieldnames if f not in preferred_order]
        
        mode = 'a' if append and file_exists else 'w'
        with open(filename, mode, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerows(trades)
        
        action = "Appended" if file_exists else "Saved"
        print(f"{action} {len(trades)} trades to {filename}")
    except Exception as e:
        print(f"Error saving CSV file {filename}: {e}")


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Scrape time & sales data from CSE or Stockwatch for a given ticker symbol"
    )
    parser.add_argument(
        '--symbol',
        type=str,
        default='DOCT',
        help='Ticker symbol to scrape (default: DOCT)'
    )
    parser.add_argument(
        '--source',
        type=str,
        choices=['cse', 'stockwatch'],
        default='cse',
        help='Data source: cse (default) or stockwatch'
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Date in yyyymmdd format (required for Stockwatch, optional - defaults to today)'
    )
    
    args = parser.parse_args()
    symbol = args.symbol.upper()
    source = args.source.lower()
    date = args.date
    
    if source == 'cse':
        print(f"Scraping CSE time & sales data for {symbol}...")
        
        # Scrape the data
        trades = scrape_cse_trades(symbol)
        
        if not trades:
            print("No trades found. Exiting.")
            return
        
        # Generate output filenames - use depth_chart for Depth Display data
        json_filename = "depth_chart.json"
        csv_filename = "depth_chart.csv"
        
        # Save to JSON (append mode)
        save_to_json(trades, json_filename, append=True)
        
        # Save to CSV (append mode)
        save_to_csv(trades, csv_filename, append=True)
        
        print(f"\nScraping complete! Found {len(trades)} trades.")
        print(f"Output files: {json_filename}, {csv_filename}")
    
    elif source == 'stockwatch':
        print(f"Scraping Stockwatch trades data for {symbol}...")
        
        # Scrape the data
        try:
            trades = scrape_stockwatch_trades(symbol, date)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            return
        
        if not trades:
            print("No trades found. Exiting.")
            return
        
        # Generate output filenames
        json_filename = "trades.json"
        
        # Save to JSON (append mode)
        save_stockwatch_trades(trades, json_filename)
        
        print(f"\nScraping complete! Found {len(trades)} trades.")
        print(f"Output file: {json_filename}")


if __name__ == "__main__":
    main()

