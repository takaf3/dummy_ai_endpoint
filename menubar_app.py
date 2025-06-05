#!/usr/bin/env python3
"""
macOS Menu Bar App for Dummy AI Endpoint
Provides easy control of the dummy AI endpoint server from the menu bar
"""

import rumps
import subprocess
import threading
import webbrowser
import os
import sys
import signal
import time
from pathlib import Path

class DummyAIEndpointApp(rumps.App):
    def __init__(self):
        super(DummyAIEndpointApp, self).__init__("AI Mock")
        self.server_process = None
        self.server_mode = "web"  # Default to web mode
        self.server_port = 8000
        self.server_host = "0.0.0.0"
        self.log_file_path = Path(__file__).parent / "dummy_ai_endpoint_requests.log"
        
        # Create menu items
        self.menu = [
            None,  # Separator
        ]
        
        # Update status periodically
        self.timer = rumps.Timer(self.update_status, 2)
        self.timer.start()
        
    def update_status(self, _):
        """Update the server status in the menu"""
        if self.is_server_running():
            self.title = "AI Mock ✅"
            self.menu["Start Server"].title = "Stop Server"
        else:
            self.title = "AI Mock 🔴"
            self.menu["Start Server"].title = "Start Server"
    
    def is_server_running(self):
        """Check if the server process is running"""
        if self.server_process and self.server_process.poll() is None:
            return True
        return False
    
    @rumps.clicked("Start Server")
    def start_stop_server(self, sender):
        """Start or stop the server based on current state"""
        if self.is_server_running():
            self.stop_server()
        else:
            self.start_server()
    
    def start_server(self):
        """Start the dummy AI endpoint server"""
        if self.is_server_running():
            rumps.notification("Dummy AI Endpoint", "Server Already Running", 
                             f"Server is already running on port {self.server_port}")
            return
        
        # Prepare the command
        script_dir = Path(__file__).parent
        server_script = script_dir / "dummy_ai_endpoint.py"
        
        cmd = [
            sys.executable,
            str(server_script),
            "--mode", self.server_mode,
            "--port", str(self.server_port),
            "--host", self.server_host
        ]
        
        # Start the server process
        try:
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(script_dir)
            )
            
            # Give it a moment to start
            time.sleep(1)
            
            if self.is_server_running():
                rumps.notification("Dummy AI Endpoint", "Server Started", 
                                 f"Server running in {self.server_mode} mode on port {self.server_port}")
                
                # Open web UI automatically if in web mode
                if self.server_mode == "web":
                    time.sleep(1)  # Give server time to fully start
                    self.open_web_ui(None)
            else:
                rumps.notification("Dummy AI Endpoint", "Server Failed to Start", 
                                 "Check the console for error details")
        except Exception as e:
            rumps.notification("Dummy AI Endpoint", "Error", str(e))
    
    def stop_server(self):
        """Stop the dummy AI endpoint server"""
        if not self.is_server_running():
            rumps.notification("Dummy AI Endpoint", "Server Not Running", 
                             "No server process to stop")
            return
        
        try:
            # Send SIGTERM for graceful shutdown
            self.server_process.terminate()
            
            # Wait up to 5 seconds for graceful shutdown
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop gracefully
                self.server_process.kill()
                self.server_process.wait()
            
            self.server_process = None
            rumps.notification("Dummy AI Endpoint", "Server Stopped", 
                             "Server has been stopped successfully")
        except Exception as e:
            rumps.notification("Dummy AI Endpoint", "Error", str(e))
    
    @rumps.clicked("Server Mode")
    def server_mode_menu(self, _):
        """Submenu for server mode selection"""
        pass
    
    @rumps.clicked("Server Mode", "Web UI Mode")
    def set_web_mode(self, sender):
        """Set server to web UI mode"""
        if self.server_mode != "web":
            self.server_mode = "web"
            rumps.notification("Dummy AI Endpoint", "Mode Changed", 
                             "Server will run in Web UI mode")
            if self.is_server_running():
                rumps.notification("Dummy AI Endpoint", "Restart Required", 
                                 "Please restart the server for changes to take effect")
    
    @rumps.clicked("Server Mode", "CLI Mode")
    def set_cli_mode(self, sender):
        """Set server to CLI mode"""
        if self.server_mode != "cli":
            self.server_mode = "cli"
            rumps.notification("Dummy AI Endpoint", "Mode Changed", 
                             "Server will run in CLI mode")
            if self.is_server_running():
                rumps.notification("Dummy AI Endpoint", "Restart Required", 
                                 "Please restart the server for changes to take effect")
    
    @rumps.clicked("Open Web UI")
    def open_web_ui(self, _):
        """Open the web UI in the default browser"""
        if not self.is_server_running():
            rumps.notification("Dummy AI Endpoint", "Server Not Running", 
                             "Please start the server first")
            return
        
        if self.server_mode != "web":
            rumps.notification("Dummy AI Endpoint", "Wrong Mode", 
                             "Server is running in CLI mode. Switch to Web UI mode to use the web interface.")
            return
        
        url = f"http://localhost:{self.server_port}"
        webbrowser.open(url)
    
    @rumps.clicked("View Recent Logs")
    def view_logs(self, _):
        """Show recent log entries in a notification"""
        if not self.log_file_path.exists():
            rumps.notification("Dummy AI Endpoint", "No Logs", 
                             "No log file found. Start the server to generate logs.")
            return
        
        try:
            # Read last 10 lines of the log file
            with open(self.log_file_path, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-10:] if len(lines) >= 10 else lines
                
            if recent_lines:
                # Show a summary in notification
                log_summary = f"Last {len(recent_lines)} log entries. Check console for details."
                rumps.notification("Dummy AI Endpoint", "Recent Logs", log_summary)
                
                # Print to console for detailed view
                print("\n=== Recent Log Entries ===")
                for line in recent_lines:
                    print(line.strip())
                print("========================\n")
            else:
                rumps.notification("Dummy AI Endpoint", "No Logs", "Log file is empty")
        except Exception as e:
            rumps.notification("Dummy AI Endpoint", "Error Reading Logs", str(e))
    
    @rumps.clicked("Open Logs in Console")
    def open_logs_console(self, _):
        """Open the log file in Console.app"""
        if not self.log_file_path.exists():
            rumps.notification("Dummy AI Endpoint", "No Logs", 
                             "No log file found. Start the server to generate logs.")
            return
        
        subprocess.run(["open", "-a", "Console", str(self.log_file_path)])
    
    @rumps.clicked("Settings")
    def settings_menu(self, _):
        """Submenu for settings"""
        pass
    
    @rumps.clicked("Settings", "Port: 8000")
    def change_port(self, sender):
        """Change the server port"""
        window = rumps.Window(
            message='Enter the port number for the server:',
            title='Change Port',
            default_text=str(self.server_port),
            ok='Set',
            cancel='Cancel',
            dimensions=(200, 24)
        )
        
        response = window.run()
        if response.clicked:
            try:
                new_port = int(response.text)
                if 1 <= new_port <= 65535:
                    self.server_port = new_port
                    sender.title = f"Port: {self.server_port}"
                    rumps.notification("Dummy AI Endpoint", "Port Changed", 
                                     f"Server will use port {self.server_port}")
                    if self.is_server_running():
                        rumps.notification("Dummy AI Endpoint", "Restart Required", 
                                         "Please restart the server for changes to take effect")
                else:
                    rumps.alert("Invalid Port", "Port must be between 1 and 65535")
            except ValueError:
                rumps.alert("Invalid Port", "Please enter a valid number")
    
    @rumps.clicked("About")
    def about(self, _):
        """Show about information"""
        rumps.alert(
            title="Dummy AI Endpoint",
            message="A mock OpenAI API server for testing and debugging.\n\n"
                    "Control the server from your menu bar:\n"
                    "• Start/stop the server\n"
                    "• Switch between CLI and Web UI modes\n"
                    "• View logs and open the web interface\n\n"
                    "Version 1.0"
        )
    
    def quit_application(self, _):
        """Handle application quit - this is called automatically by rumps"""
        # Stop server if running
        if self.is_server_running():
            self.stop_server()
        
        # Stop the timer
        self.timer.stop()

if __name__ == "__main__":
    app = DummyAIEndpointApp()
    app.run()