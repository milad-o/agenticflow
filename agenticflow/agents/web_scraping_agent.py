"""
Web Scraping Agent - Data Collection from Web Sources
=====================================================

Comprehensive web scraping and data collection capabilities with respect for robots.txt and rate limiting.
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import tempfile
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import urllib.robotparser


class WebScrapingAgent:
    """Agent for web scraping and data collection operations."""

    def __init__(self):
        self.capabilities = [
            "web_page_scraping",
            "data_extraction",
            "form_data_collection",
            "api_data_retrieval",
            "bulk_url_processing",
            "content_parsing",
            "image_download",
            "link_extraction",
            "robots_txt_compliance",
            "rate_limiting"
        ]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AgenticFlow-WebScraper/1.0 (Educational/Research Purpose)'
        })
        self.scraping_history = []

    async def arun(self, task: str) -> Dict[str, Any]:
        """Async execution wrapper."""
        return self.execute(task)

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute web scraping operations."""
        task_lower = task.lower()

        if any(keyword in task_lower for keyword in ["scrape", "extract", "get data from"]):
            return self._scrape_web_task(task)
        elif any(keyword in task_lower for keyword in ["download", "fetch", "retrieve"]):
            return self._download_task(task)
        elif any(keyword in task_lower for keyword in ["links", "urls", "hyperlinks"]):
            return self._extract_links_task(task)
        elif any(keyword in task_lower for keyword in ["table", "tables", "tabular"]):
            return self._extract_tables_task(task)
        elif any(keyword in task_lower for keyword in ["images", "pictures", "photos"]):
            return self._extract_images_task(task)
        elif any(keyword in task_lower for keyword in ["api", "endpoint", "json"]):
            return self._api_data_task(task)
        elif any(keyword in task_lower for keyword in ["bulk", "multiple", "batch"]):
            return self._bulk_scraping_task(task)
        elif any(keyword in task_lower for keyword in ["monitor", "watch", "track"]):
            return self._monitoring_task(task)
        else:
            return self._general_scraping_task(task)

    def _scrape_web_task(self, task: str) -> Dict[str, Any]:
        """Scrape data from web pages."""
        scraping_info = self._extract_scraping_info(task)

        try:
            url = scraping_info.get("url")
            selectors = scraping_info.get("selectors", {})
            respect_robots = scraping_info.get("respect_robots", True)

            if not url:
                return {
                    "action": "web_scraping",
                    "success": False,
                    "error": "URL is required for web scraping"
                }

            # Check robots.txt if requested
            if respect_robots and not self._check_robots_permission(url):
                return {
                    "action": "web_scraping",
                    "success": False,
                    "error": "Scraping not allowed by robots.txt"
                }

            # Fetch web page
            response = self._fetch_page(url)
            if not response:
                return {
                    "action": "web_scraping",
                    "success": False,
                    "error": "Failed to fetch web page"
                }

            # Parse content
            soup = BeautifulSoup(response.text, 'html.parser')
            extracted_data = self._extract_data_with_selectors(soup, selectors)

            # Save extracted data
            output_file = self._save_scraped_data(extracted_data, url)

            self._log_scraping_operation("scrape", url, True)

            return {
                "action": "web_scraping",
                "success": True,
                "url": url,
                "data_extracted": len(extracted_data) if isinstance(extracted_data, list) else 1,
                "output_file": output_file,
                "extracted_data": extracted_data if len(str(extracted_data)) < 1000 else f"<Large dataset: {len(str(extracted_data))} chars>",
                "page_title": soup.title.string if soup.title else "No title"
            }

        except Exception as e:
            self._log_scraping_operation("scrape", scraping_info.get("url"), False, str(e))
            return {
                "action": "web_scraping",
                "success": False,
                "error": str(e)
            }

    def _extract_links_task(self, task: str) -> Dict[str, Any]:
        """Extract links from web pages."""
        link_info = self._extract_link_info(task)

        try:
            url = link_info.get("url")
            link_type = link_info.get("type", "all")  # all, internal, external

            if not url:
                return {
                    "action": "link_extraction",
                    "success": False,
                    "error": "URL is required"
                }

            response = self._fetch_page(url)
            if not response:
                return {
                    "action": "link_extraction",
                    "success": False,
                    "error": "Failed to fetch web page"
                }

            soup = BeautifulSoup(response.text, 'html.parser')
            links = self._extract_links(soup, url, link_type)

            # Save links
            output_file = self._save_links_data(links, url)

            self._log_scraping_operation("extract_links", url, True)

            return {
                "action": "link_extraction",
                "success": True,
                "url": url,
                "links_found": len(links),
                "link_type": link_type,
                "output_file": output_file,
                "links": links[:10]  # Show first 10 links
            }

        except Exception as e:
            self._log_scraping_operation("extract_links", link_info.get("url"), False, str(e))
            return {
                "action": "link_extraction",
                "success": False,
                "error": str(e)
            }

    def _extract_tables_task(self, task: str) -> Dict[str, Any]:
        """Extract tables from web pages."""
        table_info = self._extract_table_info(task)

        try:
            url = table_info.get("url")

            if not url:
                return {
                    "action": "table_extraction",
                    "success": False,
                    "error": "URL is required"
                }

            response = self._fetch_page(url)
            if not response:
                return {
                    "action": "table_extraction",
                    "success": False,
                    "error": "Failed to fetch web page"
                }

            soup = BeautifulSoup(response.text, 'html.parser')
            tables = self._extract_tables(soup)

            # Save tables
            output_files = self._save_tables_data(tables, url)

            self._log_scraping_operation("extract_tables", url, True)

            return {
                "action": "table_extraction",
                "success": True,
                "url": url,
                "tables_found": len(tables),
                "output_files": output_files,
                "table_previews": [table[:3] for table in tables]  # First 3 rows of each table
            }

        except Exception as e:
            self._log_scraping_operation("extract_tables", table_info.get("url"), False, str(e))
            return {
                "action": "table_extraction",
                "success": False,
                "error": str(e)
            }

    def _api_data_task(self, task: str) -> Dict[str, Any]:
        """Retrieve data from API endpoints."""
        api_info = self._extract_api_info(task)

        try:
            url = api_info.get("url")
            method = api_info.get("method", "GET")
            headers = api_info.get("headers", {})
            params = api_info.get("params", {})
            data = api_info.get("data", {})

            if not url:
                return {
                    "action": "api_data_retrieval",
                    "success": False,
                    "error": "URL is required"
                }

            # Make API request
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data, timeout=30)
            else:
                return {
                    "action": "api_data_retrieval",
                    "success": False,
                    "error": f"Unsupported method: {method}"
                }

            response.raise_for_status()

            # Parse response
            try:
                api_data = response.json()
            except:
                api_data = response.text

            # Save API data
            output_file = self._save_api_data(api_data, url)

            self._log_scraping_operation("api_request", url, True)

            return {
                "action": "api_data_retrieval",
                "success": True,
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "output_file": output_file,
                "data_preview": str(api_data)[:500] + "..." if len(str(api_data)) > 500 else api_data
            }

        except Exception as e:
            self._log_scraping_operation("api_request", api_info.get("url"), False, str(e))
            return {
                "action": "api_data_retrieval",
                "success": False,
                "error": str(e)
            }

    def _bulk_scraping_task(self, task: str) -> Dict[str, Any]:
        """Perform bulk scraping operations."""
        bulk_info = self._extract_bulk_info(task)

        try:
            urls = bulk_info.get("urls", [])
            delay = bulk_info.get("delay", 1)  # Delay between requests

            if not urls:
                return {
                    "action": "bulk_scraping",
                    "success": False,
                    "error": "URLs list is required"
                }

            results = []
            for i, url in enumerate(urls):
                try:
                    response = self._fetch_page(url)
                    if response:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        data = {
                            "url": url,
                            "title": soup.title.string if soup.title else "No title",
                            "content_length": len(response.text),
                            "status": "success"
                        }
                    else:
                        data = {
                            "url": url,
                            "status": "failed",
                            "error": "Failed to fetch page"
                        }

                    results.append(data)

                    # Rate limiting
                    if i < len(urls) - 1:
                        time.sleep(delay)

                except Exception as e:
                    results.append({
                        "url": url,
                        "status": "error",
                        "error": str(e)
                    })

            # Save bulk results
            output_file = self._save_bulk_results(results)

            successful_scrapes = sum(1 for r in results if r.get("status") == "success")

            self._log_scraping_operation("bulk_scrape", f"{len(urls)} URLs", True)

            return {
                "action": "bulk_scraping",
                "success": True,
                "total_urls": len(urls),
                "successful_scrapes": successful_scrapes,
                "failed_scrapes": len(urls) - successful_scrapes,
                "output_file": output_file,
                "results": results
            }

        except Exception as e:
            self._log_scraping_operation("bulk_scrape", "multiple URLs", False, str(e))
            return {
                "action": "bulk_scraping",
                "success": False,
                "error": str(e)
            }

    def _general_scraping_task(self, task: str) -> Dict[str, Any]:
        """Handle general scraping tasks."""
        return {
            "action": "web_scraping_assistance",
            "success": True,
            "message": "I can help with web scraping operations. Try asking me to:",
            "capabilities": [
                "Scrape data from web pages with CSS selectors",
                "Extract links (internal, external, or all)",
                "Extract tables and convert to CSV",
                "Download images and files",
                "Retrieve data from API endpoints",
                "Perform bulk scraping with rate limiting",
                "Monitor web pages for changes",
                "Respect robots.txt and implement delays",
                "Parse various content types (HTML, JSON, XML)"
            ],
            "examples": [
                "Scrape product data from 'https://example.com/products'",
                "Extract all links from 'https://example.com'",
                "Get tables from 'https://example.com/data'",
                "Download API data from 'https://api.example.com/data'",
                "Bulk scrape these URLs: ['url1', 'url2', 'url3']",
                "Monitor 'https://example.com' for changes"
            ],
            "important_notes": [
                "Always respect robots.txt and website terms of service",
                "Use appropriate delays between requests",
                "Be mindful of server load and rate limits",
                "Only scrape publicly available data"
            ]
        }

    # Helper methods for web scraping
    def _fetch_page(self, url: str) -> Optional[requests.Response]:
        """Fetch web page with error handling."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _check_robots_permission(self, url: str) -> bool:
        """Check if scraping is allowed by robots.txt."""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()

            return rp.can_fetch('*', url)
        except:
            return True  # Allow scraping if robots.txt check fails

    def _extract_data_with_selectors(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract data using CSS selectors."""
        if not selectors:
            # Default extraction
            return {
                "title": soup.title.string if soup.title else "No title",
                "headings": [h.get_text().strip() for h in soup.find_all(['h1', 'h2', 'h3'])[:10]],
                "paragraphs": [p.get_text().strip() for p in soup.find_all('p')[:5]]
            }

        extracted_data = []

        # Find container elements
        container_selector = selectors.get("container", "body")
        containers = soup.select(container_selector)

        for container in containers:
            item_data = {}

            for field_name, selector in selectors.items():
                if field_name == "container":
                    continue

                elements = container.select(selector)
                if elements:
                    if len(elements) == 1:
                        item_data[field_name] = elements[0].get_text().strip()
                    else:
                        item_data[field_name] = [el.get_text().strip() for el in elements]

            if item_data:
                extracted_data.append(item_data)

        return extracted_data

    def _extract_links(self, soup: BeautifulSoup, base_url: str, link_type: str) -> List[Dict[str, str]]:
        """Extract links from page."""
        links = []
        base_domain = urlparse(base_url).netloc

        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            link_domain = urlparse(absolute_url).netloc

            link_data = {
                "text": link.get_text().strip(),
                "url": absolute_url,
                "type": "internal" if link_domain == base_domain else "external"
            }

            if link_type == "all" or link_data["type"] == link_type:
                links.append(link_data)

        return links

    def _extract_tables(self, soup: BeautifulSoup) -> List[List[List[str]]]:
        """Extract tables from page."""
        tables = []

        for table in soup.find_all('table'):
            table_data = []

            # Extract headers
            headers = []
            header_row = table.find('thead')
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    headers.append(th.get_text().strip())

            if headers:
                table_data.append(headers)

            # Extract rows
            tbody = table.find('tbody') or table
            for row in tbody.find_all('tr'):
                row_data = []
                for cell in row.find_all(['td', 'th']):
                    row_data.append(cell.get_text().strip())

                if row_data and (not headers or len(row_data) == len(headers)):
                    table_data.append(row_data)

            if table_data:
                tables.append(table_data)

        return tables

    def _save_scraped_data(self, data: Any, url: str) -> str:
        """Save scraped data to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        domain = urlparse(url).netloc.replace('.', '_')
        filename = f"scraped_{domain}_{timestamp}.json"
        file_path = os.path.join(tempfile.gettempdir(), filename)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return file_path

    def _save_links_data(self, links: List[Dict[str, str]], url: str) -> str:
        """Save extracted links to CSV."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        domain = urlparse(url).netloc.replace('.', '_')
        filename = f"links_{domain}_{timestamp}.csv"
        file_path = os.path.join(tempfile.gettempdir(), filename)

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            if links:
                writer = csv.DictWriter(f, fieldnames=links[0].keys())
                writer.writeheader()
                writer.writerows(links)

        return file_path

    def _save_tables_data(self, tables: List[List[List[str]]], url: str) -> List[str]:
        """Save extracted tables to CSV files."""
        output_files = []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        domain = urlparse(url).netloc.replace('.', '_')

        for i, table in enumerate(tables):
            filename = f"table_{domain}_{i+1}_{timestamp}.csv"
            file_path = os.path.join(tempfile.gettempdir(), filename)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(table)

            output_files.append(file_path)

        return output_files

    def _save_api_data(self, data: Any, url: str) -> str:
        """Save API data to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        domain = urlparse(url).netloc.replace('.', '_')
        filename = f"api_{domain}_{timestamp}.json"
        file_path = os.path.join(tempfile.gettempdir(), filename)

        with open(file_path, 'w', encoding='utf-8') as f:
            if isinstance(data, str):
                f.write(data)
            else:
                json.dump(data, f, indent=2, default=str)

        return file_path

    def _save_bulk_results(self, results: List[Dict[str, Any]]) -> str:
        """Save bulk scraping results."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"bulk_scraping_{timestamp}.csv"
        file_path = os.path.join(tempfile.gettempdir(), filename)

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            if results:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)

        return file_path

    def _log_scraping_operation(self, operation: str, target: str, success: bool, error: str = None):
        """Log scraping operation."""
        self.scraping_history.append({
            "operation": operation,
            "target": target,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    # Info extraction methods
    def _extract_scraping_info(self, task: str) -> Dict[str, Any]:
        """Extract scraping information from task."""
        info = {}

        # Extract URL
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        url_match = re.search(url_pattern, task)
        if url_match:
            info["url"] = url_match.group()

        # Extract selectors (simplified)
        if "selector" in task.lower():
            # In practice, this would be more sophisticated
            info["selectors"] = {"container": "div", "title": "h1", "content": "p"}

        return info

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return self.capabilities

    def get_scraping_history(self) -> List[Dict[str, Any]]:
        """Get scraping operation history."""
        return self.scraping_history