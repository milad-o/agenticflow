#!/usr/bin/env python3
"""
AgenticFlow UI Launcher - Multi-Interface Dashboard
=================================================

Launch all AgenticFlow UI interfaces with one command.
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def print_banner():
    """Print launch banner."""
    print("=" * 80)
    print("🚀 AGENTICFLOW UI LAUNCHER - Multi-Interface Dashboard")
    print("=" * 80)
    print("Available interfaces:")
    print("1. 💬 Chat Interface         - http://localhost:8502")
    print("2. 📈 Progress Monitor       - http://localhost:8503")
    print("-" * 80)


def launch_ui(ui_name, port, script_name):
    """Launch a specific UI."""
    try:
        print(f"🚀 Launching {ui_name} on port {port}...")
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", script_name,
            "--server.port", str(port),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ])
        time.sleep(2)  # Give it time to start
        print(f"✅ {ui_name} launched successfully!")
        return process
    except Exception as e:
        print(f"❌ Failed to launch {ui_name}: {e}")
        return None


def main():
    """Main launcher."""
    print_banner()

    # Check if we have the required files
    required_files = [
        "chat_ui.py",
        "progress_ui.py"
    ]

    missing_files = [f for f in required_files if not Path(f).exists()]
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return

    # Launch specialized interfaces
    processes = []

    uis = [
        ("Chat Interface", 8502, "chat_ui.py"),
        ("Progress Monitor", 8503, "progress_ui.py")
    ]

    for ui_name, port, script in uis:
        process = launch_ui(ui_name, port, script)
        if process:
            processes.append((ui_name, port, process))

    if processes:
        print("\n" + "=" * 80)
        print("🎉 ALL INTERFACES LAUNCHED SUCCESSFULLY!")
        print("=" * 80)
        print("Available dashboards:")

        for ui_name, port, _ in processes:
            print(f"• {ui_name:20} - http://localhost:{port}")

        print("\n💡 Tips:")
        print("• Use Chat Interface for interactive agent conversations")
        print("• Use Progress Monitor for real-time execution tracking")
        print("• For general monitoring, use: uv run streamlit run ../../agenticflow/ui.py")

        print("\n🔧 To test the system:")
        print("1. Open any of the URLs above")
        print("2. Click the demo buttons or enter custom tasks")
        print("3. Watch real-time multi-agent coordination!")

        # Optionally open browser
        try:
            print("\n🌐 Opening default interface in browser...")
            webbrowser.open("http://localhost:8503")  # Progress monitor as default
        except:
            pass

        print("\n⏸️  UIs are running. Press Ctrl+C to stop all interfaces.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down all interfaces...")
            for ui_name, port, process in processes:
                try:
                    process.terminate()
                    print(f"✅ Stopped {ui_name}")
                except:
                    print(f"❌ Error stopping {ui_name}")

            print("👋 All interfaces stopped. Thank you!")

    else:
        print("❌ Failed to launch any interfaces")


if __name__ == "__main__":
    main()