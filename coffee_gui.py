#!/usr/bin/env python3
"""
Enhanced Coffee Machine - GUI Interface MIGLIORATA
GUI Tkinter moderna con design migliorato e leggibilità ottimale
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import time
import threading
from datetime import datetime
import paho.mqtt.client as mqtt

class ModernCoffeeGUI:
    """GUI moderna e leggibile per la macchinetta del caffè"""
    
    def __init__(self):
        # === CONFIGURAZIONE MQTT ===
        self.broker = "localhost"
        self.port = 1883
        self.base_topic = "enhanced_coffee_machine"
        self.command_topic = f"{self.base_topic}/commands"
        self.status_topic = f"{self.base_topic}/status"
        self.events_topic = f"{self.base_topic}/events"
        
        # === STATO APPLICAZIONE ===
        self.current_state = "unknown"
        self.selected_beverage = None
        self.resources = {}
        self.events_log = []
        
        # === SETUP GUI ===
        self.setup_modern_gui()
        self.setup_mqtt()
        
        # === AVVIO ===
        self.log_event("🚀 GUI moderna avviata")
        self.update_status_display()
    
    def setup_modern_gui(self):
        """Configura interfaccia grafica moderna"""
        # Finestra principale con dimensioni ottimali
        self.root = tk.Tk()
        self.root.title("☕ Enhanced Coffee Machine - Modern Control Panel")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Colori moderni e leggibili
        self.colors = {
            'bg_primary': '#f8f9fa',      # Bianco/grigio molto chiaro
            'bg_secondary': '#ffffff',     # Bianco puro
            'bg_accent': '#e9ecef',       # Grigio chiaro per accenti
            'text_primary': '#212529',    # Nero/grigio scuro
            'text_secondary': '#6c757d',  # Grigio medio
            'success': '#28a745',         # Verde
            'danger': '#dc3545',          # Rosso
            'warning': '#ffc107',         # Giallo
            'info': '#17a2b8',           # Azzurro
            'primary': '#007bff',        # Blu
            'purple': '#6f42c1'          # Viola
        }
        
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Configurazione font moderni
        self.fonts = {
            'title': ('Helvetica', 24, 'bold'),
            'heading': ('Helvetica', 16, 'bold'),
            'subheading': ('Helvetica', 14, 'bold'),
            'body': ('Helvetica', 12),
            'small': ('Helvetica', 10),
            'mono': ('Monaco', 10)  # O 'Courier' se Monaco non disponibile
        }
        
        # Style moderno per ttk
        self.setup_modern_style()
        
        # === LAYOUT PRINCIPALE ===
        self.create_modern_header()
        self.create_main_content()
        self.create_modern_footer()
    
    def setup_modern_style(self):
        """Configura stili moderni per ttk"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Progress bar moderno
        style.configure('Modern.Horizontal.TProgressbar',
                       troughcolor=self.colors['bg_accent'],
                       background=self.colors['primary'],
                       borderwidth=0,
                       lightcolor=self.colors['primary'],
                       darkcolor=self.colors['primary'])
        
        # Combobox moderno
        style.configure('Modern.TCombobox',
                       fieldbackground=self.colors['bg_secondary'],
                       background=self.colors['bg_secondary'],
                       borderwidth=1,
                       relief='solid')
    
    def create_modern_header(self):
        """Crea header moderno"""
        header_frame = tk.Frame(
            self.root,
            bg=self.colors['bg_secondary'],
            height=100,
            relief='flat',
            bd=0
        )
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Container interno con padding
        header_content = tk.Frame(header_frame, bg=self.colors['bg_secondary'])
        header_content.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Titolo moderno
        title_frame = tk.Frame(header_content, bg=self.colors['bg_secondary'])
        title_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        title_label = tk.Label(
            title_frame,
            text="☕ Enhanced Coffee Machine",
            font=self.fonts['title'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary']
        )
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(
            title_frame,
            text="Modern Control Panel • Event-Driven Architecture",
            font=self.fonts['small'],
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_secondary']
        )
        subtitle_label.pack(anchor='w')
        
        # Status connection con design moderno
        status_frame = tk.Frame(header_content, bg=self.colors['bg_secondary'])
        status_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.connection_status = tk.Frame(
            status_frame,
            bg=self.colors['bg_accent'],
            relief='flat',
            bd=0
        )
        self.connection_status.pack(anchor='e', pady=5)
        
        self.connection_label = tk.Label(
            self.connection_status,
            text="🔴 Disconnesso",
            font=self.fonts['body'],
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_accent'],
            padx=15,
            pady=8
        )
        self.connection_label.pack()
        
        # Separatore sottile
        separator = tk.Frame(self.root, height=1, bg=self.colors['bg_accent'])
        separator.pack(fill=tk.X)
    
    def create_main_content(self):
        """Crea contenuto principale con layout moderno"""
        main_container = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Layout a griglia moderna
        main_container.grid_columnconfigure(0, weight=1, minsize=400)
        main_container.grid_columnconfigure(1, weight=1, minsize=500)
        main_container.grid_rowconfigure(0, weight=1)
        
        # Left Panel - Controls (migliorato)
        self.create_modern_control_panel(main_container)
        
        # Right Panel - Status & Logs (migliorato)
        self.create_modern_status_panel(main_container)
    
    def create_modern_control_panel(self, parent):
        """Crea pannello controlli moderno"""
        # Frame principale con card design
        control_frame = tk.Frame(
            parent,
            bg=self.colors['bg_secondary'],
            relief='flat',
            bd=0
        )
        control_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 15))
        
        # Header del pannello
        header = tk.Frame(control_frame, bg=self.colors['bg_secondary'])
        header.pack(fill=tk.X, padx=25, pady=(25, 15))
        
        tk.Label(
            header,
            text="🎮 Controlli",
            font=self.fonts['heading'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary']
        ).pack(anchor='w')
        
        # === SEZIONE ALIMENTAZIONE ===
        self.create_power_section(control_frame)
        
        # === SEZIONE TAZZA ===
        self.create_cup_section(control_frame)
        
        # === SEZIONE BEVANDE ===
        self.create_beverage_section(control_frame)
        
        # === SEZIONE MANUTENZIONE ===
        self.create_maintenance_section(control_frame)
    
    def create_power_section(self, parent):
        """Crea sezione alimentazione moderna"""
        section = self.create_section_frame(parent, "⚡ Alimentazione")
        
        btn_container = tk.Frame(section, bg=self.colors['bg_secondary'])
        btn_container.pack(fill=tk.X, pady=10)
        
        # Bottoni moderni affiancati
        self.btn_on = self.create_modern_button(
            btn_container, "🔌 Accendi", self.colors['success'], self.turn_on
        )
        self.btn_on.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.btn_off = self.create_modern_button(
            btn_container, "🔌 Spegni", self.colors['danger'], self.turn_off
        )
        self.btn_off.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
    
    def create_cup_section(self, parent):
        """Crea sezione gestione tazza moderna"""
        section = self.create_section_frame(parent, "🥤 Gestione Tazza")
        
        btn_container = tk.Frame(section, bg=self.colors['bg_secondary'])
        btn_container.pack(fill=tk.X, pady=10)
        
        self.btn_place_cup = self.create_modern_button(
            btn_container, "🥤 Posiziona Tazza", self.colors['primary'], self.place_cup
        )
        self.btn_place_cup.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.btn_remove_cup = self.create_modern_button(
            btn_container, "🥤 Rimuovi Tazza", self.colors['warning'], self.remove_cup
        )
        self.btn_remove_cup.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
    
    def create_beverage_section(self, parent):
        """Crea sezione bevande moderna"""
        section = self.create_section_frame(parent, "☕ Selezione Bevande")
        
        # Dropdown moderno
        combo_container = tk.Frame(section, bg=self.colors['bg_secondary'])
        combo_container.pack(fill=tk.X, pady=(10, 15))
        
        tk.Label(
            combo_container,
            text="Scegli la tua bevanda:",
            font=self.fonts['body'],
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_secondary']
        ).pack(anchor='w', pady=(0, 5))
        
        self.beverage_var = tk.StringVar()
        self.beverage_combo = ttk.Combobox(
            combo_container,
            textvariable=self.beverage_var,
            values=["☕ Espresso", "🥛 Cappuccino", "☕ Americano"],
            state="readonly",
            font=self.fonts['body'],
            style='Modern.TCombobox',
            height=8
        )
        self.beverage_combo.pack(fill=tk.X, ipady=8)
        self.beverage_combo.set("Seleziona una bevanda...")
        
        # Bottoni azione
        btn_container = tk.Frame(section, bg=self.colors['bg_secondary'])
        btn_container.pack(fill=tk.X, pady=10)
        
        self.btn_select = self.create_modern_button(
            btn_container, "☕ Seleziona", self.colors['purple'], self.select_beverage
        )
        self.btn_select.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.btn_confirm = self.create_modern_button(
            btn_container, "✅ Prepara Bevanda", self.colors['success'], self.confirm_selection
        )
        self.btn_confirm.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
    
    def create_maintenance_section(self, parent):
        """Crea sezione manutenzione moderna"""
        section = self.create_section_frame(parent, "🔧 Manutenzione")
        
        # Prima riga bottoni
        btn_row1 = tk.Frame(section, bg=self.colors['bg_secondary'])
        btn_row1.pack(fill=tk.X, pady=(10, 5))
        
        self.btn_clean = self.create_modern_button(
            btn_row1, "🧽 Avvia Pulizia", self.colors['info'], self.start_cleaning
        )
        self.btn_clean.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.btn_reset = self.create_modern_button(
            btn_row1, "🔄 Reset Errori", self.colors['text_secondary'], self.reset_error
        )
        self.btn_reset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Seconda riga bottoni
        btn_row2 = tk.Frame(section, bg=self.colors['bg_secondary'])
        btn_row2.pack(fill=tk.X, pady=(5, 10))
        
        self.btn_refill_water = self.create_modern_button(
            btn_row2, "💧 Riempi Acqua", self.colors['primary'], self.refill_water
        )
        self.btn_refill_water.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.btn_refill_coffee = self.create_modern_button(
            btn_row2, "☕ Riempi Caffè", '#8B4513', self.refill_coffee
        )
        self.btn_refill_coffee.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
    
    def create_modern_status_panel(self, parent):
        """Crea pannello status moderno"""
        # Frame principale
        status_frame = tk.Frame(
            parent,
            bg=self.colors['bg_secondary'],
            relief='flat',
            bd=0
        )
        status_frame.grid(row=0, column=1, sticky='nsew')
        
        # Header
        header = tk.Frame(status_frame, bg=self.colors['bg_secondary'])
        header.pack(fill=tk.X, padx=25, pady=(25, 15))
        
        tk.Label(
            header,
            text="📊 Status & Monitor",
            font=self.fonts['heading'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary']
        ).pack(anchor='w')
        
        # === STATUS MACCHINA ===
        self.create_machine_status_section(status_frame)
        
        # === RISORSE ===
        self.create_resources_section(status_frame)
        
        # === LOG EVENTI ===
        self.create_log_section(status_frame)
    
    def create_machine_status_section(self, parent):
        """Crea sezione status macchina"""
        section = self.create_section_frame(parent, "🤖 Stato Macchina")
        
        # Stato principale con card design
        status_card = tk.Frame(
            section,
            bg=self.colors['bg_accent'],
            relief='flat',
            bd=0
        )
        status_card.pack(fill=tk.X, pady=10, ipady=20)
        
        self.state_label = tk.Label(
            status_card,
            text="STATO: UNKNOWN",
            font=self.fonts['subheading'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_accent']
        )
        self.state_label.pack()
        
        self.beverage_label = tk.Label(
            status_card,
            text="Bevanda: Nessuna",
            font=self.fonts['body'],
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_accent']
        )
        self.beverage_label.pack(pady=(5, 0))
    
    def create_resources_section(self, parent):
        """Crea sezione risorse moderna"""
        section = self.create_section_frame(parent, "📦 Risorse")
        
        res_container = tk.Frame(section, bg=self.colors['bg_secondary'])
        res_container.pack(fill=tk.X, pady=10)
        
        # Griglia 2x2 per risorse
        res_container.grid_columnconfigure(0, weight=1)
        res_container.grid_columnconfigure(1, weight=1)
        
        # Acqua
        self.create_resource_item(res_container, "💧 Acqua", 0, 0)
        self.water_progress = ttk.Progressbar(
            res_container,
            length=150,
            mode='determinate',
            style='Modern.Horizontal.TProgressbar'
        )
        self.water_progress.grid(row=0, column=1, sticky='ew', padx=(10, 20), pady=2)
        self.water_label = tk.Label(
            res_container, text="100%", font=self.fonts['small'],
            fg=self.colors['text_secondary'], bg=self.colors['bg_secondary']
        )
        self.water_label.grid(row=0, column=2, padx=(0, 10))
        
        # Caffè
        self.create_resource_item(res_container, "☕ Caffè", 1, 0)
        self.coffee_progress = ttk.Progressbar(
            res_container,
            length=150,
            mode='determinate',
            style='Modern.Horizontal.TProgressbar'
        )
        self.coffee_progress.grid(row=1, column=1, sticky='ew', padx=(10, 20), pady=2)
        self.coffee_label = tk.Label(
            res_container, text="100%", font=self.fonts['small'],
            fg=self.colors['text_secondary'], bg=self.colors['bg_secondary']
        )
        self.coffee_label.grid(row=1, column=2, padx=(0, 10))
        
        # Temperatura e Tazza
        info_row = tk.Frame(res_container, bg=self.colors['bg_secondary'])
        info_row.grid(row=2, column=0, columnspan=3, sticky='ew', pady=(15, 5))
        
        temp_frame = tk.Frame(info_row, bg=self.colors['bg_secondary'])
        temp_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(
            temp_frame, text="🌡️ Temperatura:", font=self.fonts['body'],
            fg=self.colors['text_primary'], bg=self.colors['bg_secondary']
        ).pack(side=tk.LEFT)
        
        self.temp_label = tk.Label(
            temp_frame, text="20°C", font=self.fonts['body'],
            fg=self.colors['text_secondary'], bg=self.colors['bg_secondary']
        )
        self.temp_label.pack(side=tk.LEFT, padx=(10, 0))
        
        cup_frame = tk.Frame(info_row, bg=self.colors['bg_secondary'])
        cup_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        tk.Label(
            cup_frame, text="🥤 Tazza:", font=self.fonts['body'],
            fg=self.colors['text_primary'], bg=self.colors['bg_secondary']
        ).pack(side=tk.RIGHT, padx=(0, 10))
        
        self.cup_label = tk.Label(
            cup_frame, text="Assente", font=self.fonts['body'],
            fg=self.colors['danger'], bg=self.colors['bg_secondary']
        )
        self.cup_label.pack(side=tk.RIGHT)
    
    def create_log_section(self, parent):
        """Crea sezione log moderna"""
        section = self.create_section_frame(parent, "📝 Log Eventi")
        
        # Container log
        log_container = tk.Frame(section, bg=self.colors['bg_secondary'])
        log_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Text widget moderno
        self.log_text = tk.Text(
            log_container,
            height=10,
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
            font=self.fonts['mono'],
            wrap=tk.WORD,
            relief='flat',
            bd=0,
            padx=15,
            pady=10
        )
        
        # Scrollbar moderna
        scrollbar = ttk.Scrollbar(log_container, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottone clear moderno
        clear_btn = self.create_modern_button(
            section, "🗑️ Pulisci Log", self.colors['text_secondary'], self.clear_log, small=True
        )
        clear_btn.pack(pady=(10, 0))
    
    def create_modern_footer(self):
        """Crea footer moderno"""
        # Separatore
        separator = tk.Frame(self.root, height=1, bg=self.colors['bg_accent'])
        separator.pack(fill=tk.X)
        
        footer_frame = tk.Frame(
            self.root,
            bg=self.colors['bg_secondary'],
            height=50
        )
        footer_frame.pack(fill=tk.X)
        footer_frame.pack_propagate(False)
        
        footer_content = tk.Frame(footer_frame, bg=self.colors['bg_secondary'])
        footer_content.pack(fill=tk.BOTH, expand=True, padx=30, pady=15)
        
        # Info MQTT
        self.mqtt_info_label = tk.Label(
            footer_content,
            text=f"MQTT Broker: {self.broker}:{self.port}",
            font=self.fonts['small'],
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_secondary']
        )
        self.mqtt_info_label.pack(side=tk.LEFT)
        
        # Timestamp
        self.time_label = tk.Label(
            footer_content,
            text="",
            font=self.fonts['small'],
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_secondary']
        )
        self.time_label.pack(side=tk.RIGHT)
        
        self.update_time()
    
    # === UTILITY FUNCTIONS ===
    
    def create_section_frame(self, parent, title):
        """Crea frame sezione con titolo"""
        container = tk.Frame(parent, bg=self.colors['bg_secondary'])
        container.pack(fill=tk.X, padx=25, pady=(0, 20))
        
        # Titolo sezione
        title_label = tk.Label(
            container,
            text=title,
            font=self.fonts['subheading'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary']
        )
        title_label.pack(anchor='w', pady=(0, 5))
        
        return container
    
    def create_modern_button(self, parent, text, color, command, small=False):
        """Crea bottone moderno"""
        font = self.fonts['small'] if small else self.fonts['body']
        pady = 8 if small else 12
        
        button = tk.Button(
            parent,
            text=text,
            font=font,
            bg=color,
            fg='white',
            relief='flat',
            bd=0,
            command=command,
            cursor='hand2',
            padx=20,
            pady=pady
        )
        
        # Hover effect
        def on_enter(e):
            button.config(bg=self.darken_color(color))
        
        def on_leave(e):
            button.config(bg=color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button
    
    def create_resource_item(self, parent, text, row, col):
        """Crea item risorsa"""
        label = tk.Label(
            parent,
            text=text,
            font=self.fonts['body'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary']
        )
        label.grid(row=row, column=col, sticky='w', padx=(10, 10), pady=5)
        return label
    
    def darken_color(self, color):
        """Scurisce un colore per l'hover effect"""
        color_map = {
            self.colors['success']: '#218838',
            self.colors['danger']: '#c82333',
            self.colors['warning']: '#e0a800',
            self.colors['info']: '#138496',
            self.colors['primary']: '#0056b3',
            self.colors['purple']: '#5a2d91',
            self.colors['text_secondary']: '#5a6268',
            '#8B4513': '#7a3e10'
        }
        return color_map.get(color, color)
    
    # === MQTT E LOGICA (invariata dal codice originale) ===
    
    def setup_mqtt(self):
        """Configura connessione MQTT"""
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        
        threading.Thread(target=self.connect_mqtt, daemon=True).start()
    
    def connect_mqtt(self):
        """Connette al broker MQTT"""
        try:
            self.mqtt_client.connect(self.broker, self.port, 60)
            self.mqtt_client.loop_forever()
        except Exception as e:
            self.log_event(f"❌ Errore MQTT: {e}")
            threading.Timer(5.0, self.connect_mqtt).start()
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback connessione MQTT"""
        if rc == 0:
            self.log_event("✅ Connesso al broker MQTT")
            self.connection_label.config(
                text="🟢 Connesso",
                fg='white',
                bg=self.colors['success']
            )
            self.connection_status.config(bg=self.colors['success'])
            client.subscribe(self.status_topic)
            client.subscribe(self.events_topic)
        else:
            self.log_event(f"❌ Connessione MQTT fallita: {rc}")
            self.connection_label.config(
                text="🔴 Errore",
                fg='white',
                bg=self.colors['danger']
            )
            self.connection_status.config(bg=self.colors['danger'])
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback disconnessione MQTT"""
        self.log_event("🔴 Disconnesso da MQTT")
        self.connection_label.config(
            text="🔴 Disconnesso",
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_accent']
        )
        self.connection_status.config(bg=self.colors['bg_accent'])
    
    def on_mqtt_message(self, client, userdata, msg):
        """Gestisce messaggi MQTT ricevuti"""
        try:
            data = json.loads(msg.payload.decode())
            
            if msg.topic == self.status_topic:
                self.current_state = data.get('state', 'unknown')
                self.selected_beverage = data.get('selected_beverage')
                self.resources = data.get('resources', {})
                self.root.after(0, self.update_status_display)
                
            elif msg.topic == self.events_topic:
                event = data.get('event', 'unknown')
                self.log_event(f"📣 {event}")
                
        except Exception as e:
            self.log_event(f"❌ Errore messaggio: {e}")
    
    def send_command(self, command: str, payload: dict = None):
        """Invia comando via MQTT"""
        message = {
            "source": "modern_gui",
            "timestamp": datetime.now().isoformat(),
            "command": command
        }
        
        if payload:
            message["payload"] = payload
        
        try:
            self.mqtt_client.publish(self.command_topic, json.dumps(message))
            self.log_event(f"📤 {command}")
        except Exception as e:
            self.log_event(f"❌ Errore invio: {e}")
            messagebox.showerror("Errore", f"Impossibile inviare comando: {e}")
    
    # === COMANDI INTERFACCIA ===
    
    def turn_on(self):
        """Accende la macchina"""
        self.send_command("turn_on")
    
    def turn_off(self):
        """Spegne la macchina"""
        self.send_command("turn_off")
    
    def place_cup(self):
        """Posiziona tazza"""
        self.send_command("place_cup")
    
    def remove_cup(self):
        """Rimuove tazza"""
        self.send_command("remove_cup")
    
    def select_beverage(self):
        """Seleziona bevanda"""
        selection = self.beverage_var.get()
        if selection and selection != "Seleziona una bevanda...":
            # Estrai il nome della bevanda dal testo con emoji
            beverage_map = {
                "☕ Espresso": "espresso",
                "🥛 Cappuccino": "cappuccino", 
                "☕ Americano": "americano"
            }
            beverage = beverage_map.get(selection)
            if beverage:
                self.send_command("select_beverage", {"beverage": beverage})
        else:
            messagebox.showwarning("Attenzione", "Seleziona una bevanda prima!")
    
    def confirm_selection(self):
        """Conferma selezione"""
        self.send_command("confirm_selection")
    
    def start_cleaning(self):
        """Avvia pulizia"""
        self.send_command("start_cleaning")
    
    def reset_error(self):
        """Reset errore"""
        self.send_command("reset_error")
    
    def refill_water(self):
        """Riempie acqua"""
        self.send_command("refill_water")
    
    def refill_coffee(self):
        """Riempie caffè"""
        self.send_command("refill_coffee")
    
    # === AGGIORNAMENTO GUI ===
    
    def update_status_display(self):
        """Aggiorna display dello stato con colori moderni"""
        # Stato principale con colori migliorati
        state_text = self.current_state.upper().replace('_', ' ')
        color = self.get_modern_state_color(self.current_state)
        
        self.state_label.config(text=f"STATO: {state_text}", fg=color)
        
        # Bevanda selezionata
        if self.selected_beverage:
            self.beverage_label.config(
                text=f"Bevanda: {self.selected_beverage.capitalize()}",
                fg=self.colors['text_primary']
            )
        else:
            self.beverage_label.config(
                text="Bevanda: Nessuna",
                fg=self.colors['text_secondary']
            )
        
        # Aggiorna risorse se disponibili
        if self.resources:
            # Livello acqua
            water_level = self.resources.get('water_level', 0)
            self.water_progress['value'] = water_level
            self.water_label.config(
                text=f"{water_level:.0f}%",
                fg=self.colors['success'] if water_level > 20 else self.colors['danger']
            )
            
            # Livello caffè
            coffee_level = self.resources.get('coffee_level', 0)
            self.coffee_progress['value'] = coffee_level
            self.coffee_label.config(
                text=f"{coffee_level:.0f}%",
                fg=self.colors['success'] if coffee_level > 20 else self.colors['danger']
            )
            
            # Temperatura
            temp = self.resources.get('temperature', 20)
            temp_color = self.colors['success'] if temp >= 85 else self.colors['warning']
            self.temp_label.config(text=f"{temp}°C", fg=temp_color)
            
            # Presenza tazza
            cup_present = self.resources.get('cup_present', False)
            if cup_present:
                self.cup_label.config(text="Presente", fg=self.colors['success'])
            else:
                self.cup_label.config(text="Assente", fg=self.colors['danger'])
    
    def get_modern_state_color(self, state):
        """Restituisce colori moderni per gli stati"""
        colors = {
            "off": self.colors['text_secondary'],
            "self_check": self.colors['warning'],
            "ready": self.colors['success'],
            "ask_beverage": self.colors['primary'],
            "produce_beverage": self.colors['purple'],
            "self_clean": self.colors['info'],
            "error": self.colors['danger']
        }
        return colors.get(state, self.colors['text_primary'])
    
    def log_event(self, message):
        """Aggiunge evento al log con timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        def update_log():
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            
            # Limita log a 100 righe
            lines = self.log_text.get("1.0", tk.END).split('\n')
            if len(lines) > 100:
                self.log_text.delete("1.0", "2.0")
        
        if hasattr(self, 'root'):
            self.root.after(0, update_log)
    
    def clear_log(self):
        """Pulisce log eventi"""
        self.log_text.delete("1.0", tk.END)
        self.log_event("🗑️ Log pulito")
    
    def update_time(self):
        """Aggiorna timestamp footer"""
        current_time = datetime.now().strftime("%d/%m/%Y • %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
    
    def run(self):
        """Avvia GUI moderna"""
        # Centra la finestra sullo schermo
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.root.mainloop()
    
    def cleanup(self):
        """Pulizia risorse"""
        try:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        except:
            pass

def main():
    """Funzione principale"""
    try:
        print("🚀 Avvio GUI moderna...")
        app = ModernCoffeeGUI()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 GUI chiusa")
    finally:
        if 'app' in locals():
            app.cleanup()

if __name__ == "__main__":
    main()