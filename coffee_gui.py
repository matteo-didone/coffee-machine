#!/usr/bin/env python3
"""
Enhanced Coffee Machine - Streamlit Web GUI COMPLETAMENTE RISCRITTA
Soluzione alternativa senza MQTT callback in thread separati
"""

import streamlit as st
import json
import time
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
import plotly.graph_objects as go
from collections import deque
import queue

# Configurazione pagina
st.set_page_config(
    page_title="☕ Coffee Machine Control",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizzato
st.markdown("""
<style>
    .main { padding-top: 1rem; }
    .stMetric {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem; border-radius: 10px; margin: 0.5rem 0;
    }
    .stMetric > div { color: white !important; }
    .state-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem; border-radius: 15px; text-align: center; color: white;
        margin: 1rem 0; box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    .stButton > button {
        width: 100%; margin: 0.25rem 0; border-radius: 8px; font-weight: 600;
    }
    h1 { color: #2c3e50; font-size: 2.5rem; margin-bottom: 1rem; }
    h2 { color: #34495e; margin-bottom: 1rem; }
    h3 { color: #5a6c7d; margin-bottom: 0.5rem; margin-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# Classe per gestione MQTT semplificata
class SimpleMQTTManager:
    def __init__(self):
        self.broker = "localhost"
        self.port = 1883
        self.base_topic = "enhanced_coffee_machine"
        self.command_topic = f"{self.base_topic}/commands"
        self.status_topic = f"{self.base_topic}/status"
        self.events_topic = f"{self.base_topic}/events"
        
        self.client = None
        self.connected = False
        self.message_queue = queue.Queue()
        
    def connect(self):
        """Connessione MQTT semplificata"""
        try:
            if self.client:
                try:
                    self.client.loop_stop()
                    self.client.disconnect()
                except:
                    pass
            
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            
            result = self.client.connect(self.broker, self.port, 60)
            if result == 0:
                self.client.loop_start()
                return True
            else:
                return False
                
        except Exception as e:
            st.error(f"Errore connessione MQTT: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            client.subscribe(self.status_topic)
            client.subscribe(self.events_topic)
        else:
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
    
    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            self.message_queue.put({
                'topic': msg.topic,
                'data': data,
                'timestamp': time.time()
            })
        except:
            pass
    
    def send_command(self, command, payload=None):
        """Invia comando"""
        if not self.connected or not self.client:
            return False
            
        message = {
            "source": "streamlit_gui",
            "timestamp": datetime.now().isoformat(),
            "command": command
        }
        
        if payload:
            message["payload"] = payload
        
        try:
            self.client.publish(self.command_topic, json.dumps(message))
            return True
        except:
            return False
    
    def get_messages(self):
        """Recupera messaggi dalla coda"""
        messages = []
        try:
            while not self.message_queue.empty():
                messages.append(self.message_queue.get_nowait())
        except:
            pass
        return messages
    
    def disconnect(self):
        """Disconnetti"""
        try:
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
        except:
            pass

# Inizializzazione stato globale
@st.cache_resource
def get_mqtt_manager():
    return SimpleMQTTManager()

def init_session_state():
    """Inizializza stato sessione"""
    defaults = {
        'current_state': 'unknown',
        'selected_beverage': None,
        'error_type': None,
        'resources': {
            'water_level': 100,
            'coffee_level': 100,
            'temperature': 20,
            'cup_present': False,
            'cleaning_cycles': 0
        },
        'events_log': deque(maxlen=50),
        'last_update': time.time(),
        'connection_status': 'disconnected'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def add_log(message):
    """Aggiunge log thread-safe"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.events_log.append(f"[{timestamp}] {message}")

def create_gauge_chart(value, title, color="#007bff"):
    """Crea gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16, 'color': '#2c3e50'}},
        number={'font': {'size': 20, 'color': '#2c3e50'}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#ecf0f1",
            'steps': [
                {'range': [0, 25], 'color': '#ffebee'},
                {'range': [25, 50], 'color': '#fff3e0'},
                {'range': [50, 75], 'color': '#e8f5e8'},
                {'range': [75, 100], 'color': '#e3f2fd'}
            ]
        }
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def main():
    """Funzione principale"""
    
    # Inizializza stato
    init_session_state()
    
    # Ottieni manager MQTT
    mqtt_manager = get_mqtt_manager()
    
    # === HEADER ===
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("# ☕ Enhanced Coffee Machine")
        st.markdown("### Modern Control Panel")
    
    with col2:
        # Gestione connessione
        if mqtt_manager.connected:
            st.markdown("**MQTT:** 🟢 Connesso")
            st.session_state.connection_status = 'connected'
        else:
            st.markdown("**MQTT:** 🔴 Disconnesso")
            st.session_state.connection_status = 'disconnected'
            if st.button("🔄 Connetti", key="connect_btn"):
                with st.spinner("Connessione..."):
                    if mqtt_manager.connect():
                        add_log("✅ Connesso a MQTT")
                        st.success("Connesso!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        add_log("❌ Errore connessione MQTT")
                        st.error("Errore connessione")
    
    # Processa messaggi MQTT ricevuti
    if mqtt_manager.connected:
        messages = mqtt_manager.get_messages()
        for msg in messages:
            if msg['topic'] == mqtt_manager.status_topic:
                data = msg['data']
                st.session_state.current_state = data.get('state', 'unknown')
                st.session_state.selected_beverage = data.get('selected_beverage')
                st.session_state.error_type = data.get('error_type')
                if 'resources' in data:
                    st.session_state.resources.update(data['resources'])
                st.session_state.last_update = time.time()
                
            elif msg['topic'] == mqtt_manager.events_topic:
                event = msg['data'].get('event', 'unknown')
                add_log(f"📣 {event}")
    
    st.markdown("---")
    
    # === LAYOUT PRINCIPALE ===
    col_left, col_right = st.columns([1, 1])
    
    # === CONTROLLI ===
    with col_left:
        st.markdown("## 🎮 Controlli")
        
        # Funzione helper per invio comandi
        def send_cmd(command, payload=None):
            if mqtt_manager.connected:
                if mqtt_manager.send_command(command, payload):
                    add_log(f"📤 {command}")
                    st.success(f"✅ {command}")
                else:
                    st.error("❌ Errore invio")
            else:
                st.error("❌ MQTT disconnesso")
        
        # Alimentazione
        st.markdown("### ⚡ Alimentazione")
        col_on, col_off = st.columns(2)
        
        with col_on:
            if st.button("🔌 Accendi", key="btn_on", use_container_width=True):
                send_cmd("turn_on")
        
        with col_off:
            if st.button("🔌 Spegni", key="btn_off", use_container_width=True):
                send_cmd("turn_off")
        
        # Gestione Tazza
        st.markdown("### 🥤 Gestione Tazza")
        col_place, col_remove = st.columns(2)
        
        with col_place:
            if st.button("🥤 Posiziona", key="btn_place", use_container_width=True):
                send_cmd("place_cup")
        
        with col_remove:
            if st.button("🥤 Rimuovi", key="btn_remove", use_container_width=True):
                send_cmd("remove_cup")
        
        # Selezione Bevande
        st.markdown("### ☕ Bevande")
        
        beverage = st.selectbox(
            "Scegli bevanda:",
            ["", "espresso", "cappuccino", "americano"],
            format_func=lambda x: {
                "": "Seleziona...",
                "espresso": "☕ Espresso",
                "cappuccino": "🥛 Cappuccino", 
                "americano": "☕ Americano"
            }.get(x, x)
        )
        
        col_select, col_confirm = st.columns(2)
        
        with col_select:
            if st.button("☕ Seleziona", key="btn_select", use_container_width=True):
                if beverage:
                    send_cmd("select_beverage", {"beverage": beverage})
                else:
                    st.warning("Seleziona bevanda!")
        
        with col_confirm:
            if st.button("✅ Prepara", key="btn_confirm", use_container_width=True):
                send_cmd("confirm_selection")
        
        # Manutenzione
        st.markdown("### 🔧 Manutenzione")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧽 Pulizia", key="btn_clean", use_container_width=True):
                send_cmd("start_cleaning")
        with col2:
            if st.button("🔄 Reset", key="btn_reset", use_container_width=True):
                send_cmd("reset_error")
        
        col3, col4 = st.columns(2)
        with col3:
            if st.button("💧 Riempi H2O", key="btn_water", use_container_width=True):
                send_cmd("refill_water")
        with col4:
            if st.button("☕ Riempi Caffè", key="btn_coffee", use_container_width=True):
                send_cmd("refill_coffee")
    
    # === STATUS ===
    with col_right:
        st.markdown("## 📊 Status")
        
        # Stato Macchina
        state_text = st.session_state.current_state.upper().replace('_', ' ')
        error_info = ""
        if st.session_state.error_type:
            error_info = f"<br><span style='color: #ffcccb;'>⚠️ {st.session_state.error_type.replace('_', ' ').title()}</span>"
        
        st.markdown(f"""
        <div class="state-card">
            <h2 style="margin: 0; color: white;">🤖 {state_text}</h2>
            <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.8);">
                Bevanda: {st.session_state.selected_beverage or 'Nessuna'}
            </p>
            {error_info}
        </div>
        """, unsafe_allow_html=True)
        
        # Risorse
        st.markdown("### 📦 Risorse")
        
        resources = st.session_state.resources
        
        col_gauge1, col_gauge2 = st.columns(2)
        
        with col_gauge1:
            water_level = resources.get('water_level', 0)
            water_chart = create_gauge_chart(
                water_level, 
                "💧 Acqua (%)", 
                "#007bff" if water_level > 20 else "#dc3545"
            )
            st.plotly_chart(water_chart, use_container_width=True)
        
        with col_gauge2:
            coffee_level = resources.get('coffee_level', 0)
            coffee_chart = create_gauge_chart(
                coffee_level, 
                "☕ Caffè (%)", 
                "#8B4513" if coffee_level > 20 else "#dc3545"
            )
            st.plotly_chart(coffee_chart, use_container_width=True)
        
        # Info aggiuntive
        col_temp, col_cup = st.columns(2)
        
        with col_temp:
            temp = resources.get('temperature', 20)
            st.metric("🌡️ Temperatura", f"{temp}°C")
        
        with col_cup:
            cup_present = resources.get('cup_present', False)
            cup_status = "Presente" if cup_present else "Assente"
            st.metric("🥤 Tazza", cup_status)
        
        # Log Eventi
        st.markdown("### 📝 Log")
        
        if st.button("🗑️ Pulisci Log", key="clear_log"):
            st.session_state.events_log.clear()
            st.rerun()
        
        if st.session_state.events_log:
            recent_logs = list(st.session_state.events_log)[-10:]
            log_text = "\n".join(recent_logs)
            st.text_area(
                "Eventi:",
                value=log_text,
                height=150,
                disabled=True,
                label_visibility="collapsed"
            )
        else:
            st.info("📋 Nessun evento")
    
    # === FOOTER ===
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown(f"**MQTT:** `{mqtt_manager.broker}:{mqtt_manager.port}`")
    
    with col2:
        last_update = datetime.fromtimestamp(st.session_state.last_update).strftime("%H:%M:%S")
        st.markdown(f"**🕒 Ultimo aggiornamento:** {last_update}")
    
    with col3:
        if st.button("🔄 Refresh", key="refresh"):
            st.rerun()
    
    # Auto-refresh ogni 2 secondi se connesso
    if mqtt_manager.connected:
        time.sleep(2)
        st.rerun()

if __name__ == "__main__":
    main()