#!/usr/bin/env python3
"""
Enhanced PWNsubGhz Plugin with Hacking-themed Animated UI
Compatible with Waveshare 1.3" OLED HAT on Pi Zero W
Runs FM Radio functionality even without CC1101
"""

import os
import time
import threading
import random
from datetime import datetime
try:
    import luma.core.interface.serial
    import luma.core.render
    import luma.oled.device
    from luma.core.render import canvas
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Please install: pip install luma.oled pillow")

# Try to import CC1101 modules (optional)
try:
    import core.cc1101.ccrf as ccrf
    import core.cc1101.binary as binTranslate
    import core.cc1101.flipsub as fsub
    CC1101_AVAILABLE = True
except ImportError:
    CC1101_AVAILABLE = False
    print("[!] CC1101 modules not available - FM mode only")

# Try to import rpitx (optional)
try:
    import core.rpitx.rpitx as rpitx
    RPITX_AVAILABLE = True
except ImportError:
    RPITX_AVAILABLE = False
    print("[!] rpitx not available - using simulation mode")

class HackingUI:
    """Animated hacking-themed UI for OLED display"""
    
    def __init__(self):
        # Initialize OLED display
        try:
            serial = luma.core.interface.serial.i2c(port=1, address=0x3C)
            self.device = luma.oled.device.sh1106(serial, rotate=0)
            self.width = self.device.width
            self.height = self.device.height
        except Exception as e:
            print(f"[!] Display init failed: {e}")
            self.device = None
            self.width, self.height = 128, 64
            
        # Animation variables
        self.matrix_drops = []
        self.scan_lines = []
        self.glitch_timer = 0
        self.blink_state = False
        self.running = True
        
        # Initialize matrix rain
        for i in range(0, self.width, 8):
            self.matrix_drops.append({
                'x': i,
                'y': random.randint(-20, 0),
                'speed': random.randint(1, 3),
                'char': chr(random.randint(33, 126))
            })
            
        # Initialize scan lines
        for i in range(3):
            self.scan_lines.append(random.randint(0, self.height))
    
    def draw_matrix_rain(self, draw):
        """Draw matrix-style falling characters"""
        for drop in self.matrix_drops:
            # Draw character
            try:
                draw.text((drop['x'], drop['y']), drop['char'], fill="white")
            except:
                pass
                
            # Update position
            drop['y'] += drop['speed']
            
            # Reset if off screen
            if drop['y'] > self.height:
                drop['y'] = random.randint(-20, -5)
                drop['char'] = chr(random.randint(33, 126))
                drop['speed'] = random.randint(1, 3)
    
    def draw_scan_lines(self, draw):
        """Draw moving scan lines"""
        for i, y in enumerate(self.scan_lines):
            draw.line([(0, y), (self.width, y)], fill="white")
            self.scan_lines[i] = (y + 2) % (self.height + 10)
    
    def draw_glitch_effect(self, draw):
        """Random glitch effect"""
        if random.randint(0, 50) == 0:
            for _ in range(random.randint(1, 5)):
                x = random.randint(0, self.width-20)
                y = random.randint(0, self.height-5)
                w = random.randint(5, 20)
                h = random.randint(1, 3)
                draw.rectangle([(x, y), (x+w, y+h)], fill="white")
    
    def draw_status_bar(self, draw, status="READY"):
        """Draw top status bar"""
        # Status bar background
        draw.rectangle([(0, 0), (self.width, 12)], fill="white")
        
        # Status text
        draw.text((2, 2), f"PWN > {status}", fill="black")
        
        # Time
        time_str = datetime.now().strftime("%H:%M")
        draw.text((self.width-30, 2), time_str, fill="black")
        
        # Blinking cursor
        if self.blink_state:
            draw.rectangle([(self.width-8, 2), (self.width-6, 10)], fill="black")
    
    def draw_menu(self, draw, items, selected=0, title="MENU"):
        """Draw animated menu"""
        # Clear area
        draw.rectangle([(0, 15), (self.width, self.height)], fill="black")
        
        # Title with effect
        title_y = 18
        draw.text((5, title_y), f">> {title} <<", fill="white")
        
        # Menu items
        start_y = 32
        for i, item in enumerate(items):
            y = start_y + (i * 10)
            if y > self.height - 10:
                break
                
            prefix = "[>]" if i == selected else "[ ]"
            text = f"{prefix} {item}"
            
            # Highlight selected
            if i == selected:
                draw.rectangle([(0, y-1), (self.width, y+9)], fill="white")
                draw.text((2, y), text, fill="black")
            else:
                draw.text((2, y), text, fill="white")
    
    def draw_console(self, draw, lines, title="CONSOLE"):
        """Draw console output"""
        # Clear screen
        draw.rectangle([(0, 0), (self.width, self.height)], fill="black")
        
        # Console header
        draw.rectangle([(0, 0), (self.width, 12)], fill="white")
        draw.text((2, 2), f"[{title}]", fill="black")
        
        # Console lines
        y_pos = 15
        for line in lines[-4:]:  # Show last 4 lines
            if y_pos < self.height - 10:
                draw.text((2, y_pos), str(line)[:20], fill="white")
                y_pos += 12
        
        # Cursor
        if self.blink_state:
            draw.text((2, y_pos), "_", fill="white")
    
    def draw_progress_bar(self, draw, progress, title="PROGRESS"):
        """Draw animated progress bar"""
        # Background
        draw.rectangle([(10, 25), (self.width-10, 35)], outline="white")
        
        # Progress fill
        fill_width = int((self.width-22) * (progress / 100))
        draw.rectangle([(11, 26), (11 + fill_width, 34)], fill="white")
        
        # Title and percentage
        draw.text((5, 15), title, fill="white")
        draw.text((5, 40), f"{progress}%", fill="white")
        
        # Animated scanner line
        scanner_x = 11 + (fill_width % 20)
        draw.line([(scanner_x, 26), (scanner_x, 34)], fill="black")
    
    def update_display(self, draw_func):
        """Update display with animation"""
        if not self.device:
            return
            
        with canvas(self.device) as draw:
            # Background animations
            if random.randint(0, 10) == 0:
                self.draw_matrix_rain(draw)
            
            if random.randint(0, 20) == 0:
                self.draw_glitch_effect(draw)
            
            # Main content
            draw_func(draw)
            
            # Update blink state
            self.blink_state = not self.blink_state

class PWNsubGhzEnhanced:
    """Enhanced PWNsubGhz with animated UI"""
    
    def __init__(self):
        self.ui = HackingUI()
        self.console_lines = []
        
        # Initialize hardware
        self.init_hardware()
        
        # Menu items
        self.main_menu = [
            "FM Radio Transmit",
            "RF Scanner" if CC1101_AVAILABLE else "RF Scanner [DISABLED]",
            "Replay Attack" if CC1101_AVAILABLE else "Replay Attack [DISABLED]",
            "Set RF Power" if CC1101_AVAILABLE else "Set RF Power [DISABLED]",
            "Set Frequency" if CC1101_AVAILABLE else "Set Frequency [DISABLED]",
            "Exit"
        ]
        
        self.selected_item = 0
        self.current_screen = "menu"
        
    def init_hardware(self):
        """Initialize hardware components"""
        self.log("Initializing PWNsubGhz...")
        
        # Initialize FM transmitter
        if RPITX_AVAILABLE:
            try:
                self.fm = rpitx.PiFMRds()
                self.log("FM transmitter ready")
            except Exception as e:
                self.log(f"FM init failed: {e}")
                self.fm = None
        else:
            self.fm = None
            self.log("FM transmitter simulation mode")
        
        # Initialize CC1101 if available
        if CC1101_AVAILABLE:
            try:
                self.transceiver = ccrf.pCC1101()
                self.freq = self.transceiver.currentFreq
                self.log(f"CC1101 ready @ {self.freq}Hz")
            except Exception as e:
                self.log(f"CC1101 failed: {e}")
                self.transceiver = None
        else:
            self.transceiver = None
            self.log("CC1101 not available")
    
    def log(self, message):
        """Add message to console log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_lines.append(f"{timestamp} {message}")
        if len(self.console_lines) > 50:
            self.console_lines = self.console_lines[-50:]
        print(f"[LOG] {message}")
    
    def show_splash(self):
        """Show animated splash screen"""
        splash_frames = [
            "PWNsubGhz v2.0",
            "Initializing...",
            "Loading modules...",
            "Ready to hack!"
        ]
        
        for frame in splash_frames:
            def draw_splash(draw):
                self.ui.draw_status_bar(draw, "BOOT")
                # Center text with animation
                text_width = len(frame) * 6
                x = (self.ui.width - text_width) // 2
                draw.text((x, 30), frame, fill="white")
                
                # Loading animation
                for i in range(5):
                    if random.randint(0, 1):
                        draw.rectangle([(20 + i*20, 50), (25 + i*20, 55)], fill="white")
            
            self.ui.update_display(draw_splash)
            time.sleep(0.8)
    
    def handle_input(self, key):
        """Handle key input"""
        if self.current_screen == "menu":
            if key == "up":
                self.selected_item = (self.selected_item - 1) % len(self.main_menu)
            elif key == "down":
                self.selected_item = (self.selected_item + 1) % len(self.main_menu)
            elif key == "select":
                self.execute_menu_item()
        
    def execute_menu_item(self):
        """Execute selected menu item"""
        item = self.main_menu[self.selected_item]
        
        if "FM Radio" in item:
            self.fm_radio_menu()
        elif "RF Scanner" in item and CC1101_AVAILABLE:
            self.rf_scanner()
        elif "Replay Attack" in item and CC1101_AVAILABLE:
            self.replay_attack()
        elif "Set RF Power" in item and CC1101_AVAILABLE:
            self.set_rf_power()
        elif "Set Frequency" in item and CC1101_AVAILABLE:
            self.set_frequency()
        elif "Exit" in item:
            self.ui.running = False
    
    def fm_radio_menu(self):
        """FM Radio transmitter interface"""
        self.log("Starting FM Radio mode")
        
        # Get audio files
        audio_dir = "./fm_audio"
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)
            
        audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
        
        if not audio_files:
            self.show_message("No .wav files found in ./fm_audio/")
            return
        
        # File selection
        selected_file = 0
        
        while True:
            def draw_file_menu(draw):
                self.ui.draw_status_bar(draw, "FM SELECT")
                self.ui.draw_menu(draw, audio_files, selected_file, "AUDIO FILES")
            
            self.ui.update_display(draw_file_menu)
            
            # Simulate key input (replace with actual GPIO handling)
            key = self.get_key_input()
            
            if key == "up":
                selected_file = (selected_file - 1) % len(audio_files)
            elif key == "down":
                selected_file = (selected_file + 1) % len(audio_files)
            elif key == "select":
                self.fm_transmit(audio_files[selected_file])
                break
            elif key == "back":
                break
            
            time.sleep(0.1)
    
    def fm_transmit(self, audio_file):
        """Transmit FM radio"""
        self.log(f"Transmitting: {audio_file}")
        
        # Frequency selection (simulate slider)
        frequency = 102.5
        
        for i in range(100):
            def draw_transmit(draw):
                self.ui.draw_status_bar(draw, "TX")
                self.ui.draw_progress_bar(draw, i, f"FM @ {frequency}MHz")
                
                # Waveform visualization
                y_center = 45
                for x in range(0, self.ui.width, 2):
                    y_offset = int(10 * random.random() - 5)
                    draw.rectangle([(x, y_center + y_offset), (x+1, y_center + y_offset + 2)], fill="white")
            
            self.ui.update_display(draw_transmit)
            
            # Actual FM transmission
            if self.fm:
                try:
                    if i == 0:
                        self.fm.freq = frequency
                        self.fm.play(os.path.join("./fm_audio", audio_file))
                except Exception as e:
                    self.log(f"FM TX error: {e}")
            
            time.sleep(0.1)
            
            # Check for stop key
            if self.get_key_input() == "back":
                break
        
        if self.fm:
            try:
                self.fm.stop()
            except:
                pass
        
        self.log("FM transmission stopped")
    
    def rf_scanner(self):
        """RF Scanner interface"""
        if not self.transceiver:
            self.show_message("CC1101 not available")
            return
        
        self.log("Starting RF scanner")
        
        try:
            self.transceiver.rst()
            self.transceiver.setupRawRecieve()
            
            scan_data = []
            
            for i in range(200):
                def draw_scanner(draw):
                    self.ui.draw_status_bar(draw, "SCAN")
                    
                    # Frequency display
                    draw.text((5, 20), f"Freq: {self.freq/1e6:.2f}MHz", fill="white")
                    
                    # Signal strength bars
                    for j in range(10):
                        height = random.randint(2, 20) if random.randint(0, 3) == 0 else 2
                        x = 10 + j * 10
                        draw.rectangle([(x, 50-height), (x+6, 50)], fill="white")
                    
                    # Progress
                    self.ui.draw_progress_bar(draw, i//2, "SCANNING")
                
                self.ui.update_display(draw_scanner)
                
                # Actual scanning
                try:
                    data = self.transceiver.rawRecv(10)
                    if data:
                        scan_data.extend(data)
                except:
                    pass
                
                time.sleep(0.05)
                
                if self.get_key_input() == "back":
                    break
            
            self.log(f"Scan complete: {len(scan_data)} bits captured")
            
        except Exception as e:
            self.log(f"Scanner error: {e}")
    
    def show_message(self, message):
        """Show message dialog"""
        lines = [message]
        
        for _ in range(30):
            def draw_message(draw):
                self.ui.draw_console(draw, lines, "MESSAGE")
            
            self.ui.update_display(draw_message)
            time.sleep(0.1)
    
    def get_key_input(self):
        """Simulate key input - replace with actual GPIO handling"""
        # This should be replaced with actual GPIO key reading
        # For now, simulate random input for demo
        keys = ["up", "down", "select", "back", None]
        return random.choice(keys) if random.randint(0, 50) == 0 else None
    
    def run(self):
        """Main application loop"""
        self.show_splash()
        
        while self.ui.running:
            def draw_main_menu(draw):
                self.ui.draw_status_bar(draw, "READY")
                self.ui.draw_menu(draw, self.main_menu, self.selected_item, "PWNsubGhz")
            
            self.ui.update_display(draw_main_menu)
            
            # Handle input
            key = self.get_key_input()
            if key:
                self.handle_input(key)
            
            time.sleep(0.1)
        
        self.log("Shutting down...")

# GPIO Key Handler (implement based on your specific setup)
class GPIOKeyHandler:
    """Handle GPIO keys for Waveshare OLED HAT"""
    
    def __init__(self):
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            
            # Waveshare 1.3" OLED HAT key pins
            self.KEY_UP_PIN = 6
            self.KEY_DOWN_PIN = 19
            self.KEY_LEFT_PIN = 5
            self.KEY_RIGHT_PIN = 26
            self.KEY_PRESS_PIN = 13
            
            self.KEY1_PIN = 21
            self.KEY2_PIN = 20
            self.KEY3_PIN = 16
            
            # Setup GPIO
            self.GPIO.setmode(GPIO.BCM)
            pins = [self.KEY_UP_PIN, self.KEY_DOWN_PIN, self.KEY_LEFT_PIN, 
                   self.KEY_RIGHT_PIN, self.KEY_PRESS_PIN, self.KEY1_PIN, 
                   self.KEY2_PIN, self.KEY3_PIN]
            
            for pin in pins:
                self.GPIO.setup(pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
                
        except ImportError:
            print("RPi.GPIO not available - using simulation mode")
            self.GPIO = None
    
    def read_keys(self):
        """Read current key states"""
        if not self.GPIO:
            return {}
            
        return {
            'up': not self.GPIO.input(self.KEY_UP_PIN),
            'down': not self.GPIO.input(self.KEY_DOWN_PIN),
            'left': not self.GPIO.input(self.KEY_LEFT_PIN),
            'right': not self.GPIO.input(self.KEY_RIGHT_PIN),
            'press': not self.GPIO.input(self.KEY_PRESS_PIN),
            'key1': not self.GPIO.input(self.KEY1_PIN),
            'key2': not self.GPIO.input(self.KEY2_PIN),
            'key3': not self.GPIO.input(self.KEY3_PIN),
        }

def main():
    """Main entry point"""
    print("Starting PWNsubGhz Enhanced...")
    
    try:
        app = PWNsubGhzEnhanced()
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()