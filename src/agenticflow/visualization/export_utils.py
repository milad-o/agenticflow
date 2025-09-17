"""
Export utilities for Mermaid diagrams to various formats.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Optional, Union, Dict, Any
import subprocess
import os

try:
    from mermaid import Mermaid
    MERMAID_PY_AVAILABLE = True
except ImportError:
    MERMAID_PY_AVAILABLE = False
    Mermaid = None

try:
    from pyppeteer import launch
    PYPPETEER_AVAILABLE = True
except ImportError:
    PYPPETEER_AVAILABLE = False
    launch = None


class MermaidExporter:
    """
    Export Mermaid diagrams to various formats (SVG, PNG, PDF).
    
    Supports multiple backends:
    - mermaid-py package (recommended)
    - Mermaid CLI via subprocess
    - Pyppeteer for browser-based rendering
    """
    
    def __init__(self, preferred_backend: str = "auto"):
        """
        Initialize the exporter.
        
        Args:
            preferred_backend: "auto", "mermaid-py", "cli", or "pyppeteer"
        """
        self.preferred_backend = preferred_backend
        self._available_backends = self._detect_available_backends()
        
    def _detect_available_backends(self) -> Dict[str, bool]:
        """Detect which export backends are available."""
        backends = {
            "mermaid-py": MERMAID_PY_AVAILABLE,
            "pyppeteer": PYPPETEER_AVAILABLE,
            "cli": self._check_mermaid_cli()
        }
        return backends
        
    def _check_mermaid_cli(self) -> bool:
        """Check if mermaid CLI is available."""
        try:
            subprocess.run(["mmdc", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Try alternate command name
                subprocess.run(["mermaid", "--version"], capture_output=True, check=True)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False
                
    def get_available_backends(self) -> Dict[str, bool]:
        """Get information about available export backends."""
        return self._available_backends.copy()
        
    def export_to_svg(
        self,
        mermaid_code: str,
        output_path: Union[str, Path],
        backend: Optional[str] = None
    ) -> bool:
        """
        Export Mermaid diagram to SVG format.
        
        Args:
            mermaid_code: Mermaid diagram code
            output_path: Output file path
            backend: Specific backend to use (optional)
            
        Returns:
            True if export successful, False otherwise
        """
        return self._export(mermaid_code, output_path, "svg", backend)
        
    def export_to_png(
        self,
        mermaid_code: str,
        output_path: Union[str, Path],
        backend: Optional[str] = None,
        width: int = 1200,
        height: int = 800
    ) -> bool:
        """
        Export Mermaid diagram to PNG format.
        
        Args:
            mermaid_code: Mermaid diagram code
            output_path: Output file path
            backend: Specific backend to use (optional)
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            True if export successful, False otherwise
        """
        return self._export(mermaid_code, output_path, "png", backend, width=width, height=height)
        
    def export_to_pdf(
        self,
        mermaid_code: str,
        output_path: Union[str, Path],
        backend: Optional[str] = None
    ) -> bool:
        """
        Export Mermaid diagram to PDF format.
        
        Args:
            mermaid_code: Mermaid diagram code
            output_path: Output file path
            backend: Specific backend to use (optional)
            
        Returns:
            True if export successful, False otherwise
        """
        return self._export(mermaid_code, output_path, "pdf", backend)
        
    def _export(
        self,
        mermaid_code: str,
        output_path: Union[str, Path],
        format: str,
        backend: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Internal export method."""
        backend = self._select_backend(backend, format)
        
        if not backend:
            print(f"No suitable backend found for {format} export")
            return False
            
        try:
            if backend == "mermaid-py":
                return self._export_mermaid_py(mermaid_code, output_path, format, **kwargs)
            elif backend == "cli":
                return self._export_cli(mermaid_code, output_path, format, **kwargs)
            elif backend == "pyppeteer":
                return asyncio.run(self._export_pyppeteer(mermaid_code, output_path, format, **kwargs))
            else:
                return False
        except Exception as e:
            print(f"Export failed with backend {backend}: {e}")
            return False
            
    def _select_backend(self, preferred: Optional[str], format: str) -> Optional[str]:
        """Select the best available backend for the given format."""
        if preferred and preferred != "auto":
            if self._available_backends.get(preferred, False):
                return preferred
            else:
                print(f"Preferred backend '{preferred}' not available")
                
        # Auto-select based on availability and format
        if format == "svg" and self._available_backends.get("mermaid-py"):
            return "mermaid-py"
        elif self._available_backends.get("cli"):
            return "cli"
        elif self._available_backends.get("pyppeteer"):
            return "pyppeteer"
        elif self._available_backends.get("mermaid-py"):
            return "mermaid-py"
            
        return None
        
    def _export_mermaid_py(
        self,
        mermaid_code: str,
        output_path: Union[str, Path],
        format: str,
        **kwargs
    ) -> bool:
        """Export using mermaid-py package."""
        if not MERMAID_PY_AVAILABLE:
            return False
            
        try:
            # mermaid-py expects the graph code in the constructor
            mermaid = Mermaid(mermaid_code)
            
            if format == "svg":
                # For SVG, we can get the content from svg_response
                svg_content = mermaid.svg_response.text
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                return True
            else:
                # For other formats, we might need to use CLI or browser rendering
                # Fall back to other methods
                return False
                
        except Exception as e:
            print(f"mermaid-py export failed: {e}")
            return False
            
    def _export_cli(
        self,
        mermaid_code: str,
        output_path: Union[str, Path],
        format: str,
        **kwargs
    ) -> bool:
        """Export using Mermaid CLI."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as tmp:
            tmp.write(mermaid_code)
            tmp.flush()
            
            try:
                cmd = ["mmdc", "-i", tmp.name, "-o", str(output_path)]
                
                if format == "svg":
                    cmd.extend(["-f", "svg"])
                elif format == "png":
                    cmd.extend(["-f", "png"])
                    if "width" in kwargs:
                        cmd.extend(["-w", str(kwargs["width"])])
                    if "height" in kwargs:
                        cmd.extend(["-H", str(kwargs["height"])])
                elif format == "pdf":
                    cmd.extend(["-f", "pdf"])
                    
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return True
                else:
                    print(f"CLI export failed: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"CLI export error: {e}")
                return False
            finally:
                os.unlink(tmp.name)
                
    async def _export_pyppeteer(
        self,
        mermaid_code: str,
        output_path: Union[str, Path],
        format: str,
        **kwargs
    ) -> bool:
        """Export using Pyppeteer (browser-based rendering)."""
        if not PYPPETEER_AVAILABLE:
            return False
            
        browser = None
        try:
            browser = await launch(headless=True, args=['--no-sandbox'])
            page = await browser.newPage()
            
            # Set viewport if dimensions provided
            if "width" in kwargs and "height" in kwargs:
                await page.setViewport({
                    'width': kwargs["width"],
                    'height': kwargs["height"]
                })
            
            # Create HTML with Mermaid
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
            </head>
            <body>
                <div class="mermaid" id="diagram">
{mermaid_code}
                </div>
                <script>
                    mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
                </script>
            </body>
            </html>
            """
            
            await page.setContent(html_content)
            import asyncio
            await asyncio.sleep(3)  # Wait for mermaid to render
            await page.waitForSelector('#diagram svg', timeout=10000)
            
            if format == "png":
                await page.screenshot({'path': str(output_path), 'fullPage': True})
            elif format == "pdf":
                await page.pdf({'path': str(output_path), 'format': 'A4'})
            elif format == "svg":
                # Get the SVG content
                svg_content = await page.evaluate('''
                    () => {
                        const svg = document.querySelector('#diagram svg');
                        return svg ? svg.outerHTML : null;
                    }
                ''')
                
                if svg_content:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(svg_content)
                else:
                    return False
                    
            return True
            
        except Exception as e:
            print(f"Pyppeteer export failed: {e}")
            return False
        finally:
            if browser:
                await browser.close()


# Global exporter instance
_global_exporter = None


def get_exporter() -> MermaidExporter:
    """Get the global MermaidExporter instance."""
    global _global_exporter
    if _global_exporter is None:
        _global_exporter = MermaidExporter()
    return _global_exporter


# Convenience functions
def export_to_svg(
    mermaid_code: str,
    output_path: Union[str, Path],
    backend: Optional[str] = None
) -> bool:
    """Export Mermaid diagram to SVG format."""
    return get_exporter().export_to_svg(mermaid_code, output_path, backend)


def export_to_png(
    mermaid_code: str,
    output_path: Union[str, Path],
    backend: Optional[str] = None,
    width: int = 1200,
    height: int = 800
) -> bool:
    """Export Mermaid diagram to PNG format."""
    return get_exporter().export_to_png(mermaid_code, output_path, backend, width, height)


def export_to_pdf(
    mermaid_code: str,
    output_path: Union[str, Path],
    backend: Optional[str] = None
) -> bool:
    """Export Mermaid diagram to PDF format."""
    return get_exporter().export_to_pdf(mermaid_code, output_path, backend)


def check_export_capabilities() -> Dict[str, Any]:
    """
    Check what export capabilities are available.
    
    Returns:
        Dictionary with available backends and supported formats
    """
    exporter = get_exporter()
    backends = exporter.get_available_backends()
    
    capabilities = {
        "backends": backends,
        "formats": {
            "svg": any(backends.values()),
            "png": backends.get("cli", False) or backends.get("pyppeteer", False),
            "pdf": backends.get("cli", False) or backends.get("pyppeteer", False)
        },
        "recommendations": []
    }
    
    # Add recommendations
    if not any(backends.values()):
        capabilities["recommendations"].append(
            "Install mermaid-cli: npm install -g @mermaid-js/mermaid-cli"
        )
    elif not backends.get("cli"):
        capabilities["recommendations"].append(
            "For best PNG/PDF support, install mermaid-cli: npm install -g @mermaid-js/mermaid-cli"
        )
        
    return capabilities


# Installation helpers
def print_installation_guide():
    """Print installation guide for export dependencies."""
    capabilities = check_export_capabilities()
    
    print("🎨 AgenticFlow Visualization Export Guide")
    print("=" * 50)
    print()
    
    print("📊 Current Capabilities:")
    for backend, available in capabilities["backends"].items():
        status = "✅ Available" if available else "❌ Not Available"
        print(f"  {backend}: {status}")
        
    print()
    print("📁 Supported Formats:")
    for format, supported in capabilities["formats"].items():
        status = "✅ Supported" if supported else "❌ Not Supported"
        print(f"  {format.upper()}: {status}")
        
    if capabilities["recommendations"]:
        print()
        print("💡 Recommendations:")
        for rec in capabilities["recommendations"]:
            print(f"  • {rec}")
            
    print()
    print("🚀 Quick Setup:")
    print("  # For full export capabilities:")
    print("  npm install -g @mermaid-js/mermaid-cli")
    print()
    print("  # Or use browser-based rendering (already installed):")
    print("  # Pyppeteer is included for PNG/PDF export")
    print()


if __name__ == "__main__":
    print_installation_guide()