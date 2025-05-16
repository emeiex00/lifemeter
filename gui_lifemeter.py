import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import sys
import winsound # Per l'audio su Windows
import math # Per la frequenza del suono
import time # Per le pause durante la riproduzione
import pygame.midi # Per la funzionalità MIDI
import threading # Per eseguire l'audio in background

# Assicurati che green_detector.py sia nello stesso percorso o nel PYTHONPATH
try:
    from green_detector import calcola_percentuale_verde
except ImportError:
    messagebox.showerror("Errore", "Non è stato possibile importare 'green_detector.py'. Assicurati che sia nella stessa cartella.")
    exit()

class GreenDetectorApp:
    def __init__(self, master):
        self.master = master
        master.title("LifeMeter - Rilevatore di Verde")

        self.soglia_default = 2

        self.label_info = tk.Label(master, text="Carica un'immagine per analizzare la percentuale di verde.")
        self.label_info.pack(pady=10)

        self.btn_carica = tk.Button(master, text="Carica Immagine", command=self.carica_immagine)
        self.btn_carica.pack(pady=5)

        self.frame_immagini = tk.Frame(master)
        self.frame_immagini.pack(pady=10)

        self.label_originale_testo = tk.Label(self.frame_immagini, text="Immagine Originale:")
        self.label_originale_testo.grid(row=0, column=0, padx=10)
        self.panel_originale = tk.Label(self.frame_immagini)
        self.panel_originale.grid(row=1, column=0, padx=10)

        self.label_verde_testo = tk.Label(self.frame_immagini, text="Pixel Verdi Rilevati:")
        self.label_verde_testo.grid(row=0, column=1, padx=10)
        self.panel_verde = tk.Label(self.frame_immagini)
        self.panel_verde.grid(row=1, column=1, padx=10)

        self.label_risultato = tk.Label(master, text="Percentuale verde: -")
        self.label_risultato.pack(pady=10)

        self.image_path = None
        self.img_originale_tk = None
        self.img_verde_tk = None

        # Configurazione MIDI
        self.frame_midi = tk.Frame(master)
        self.frame_midi.pack(pady=5)
        
        self.label_midi = tk.Label(self.frame_midi, text="Configurazione MIDI:")
        self.label_midi.grid(row=0, column=0, padx=5)
        
        self.midi_devices = ttk.Combobox(self.frame_midi, width=30)
        self.midi_devices.grid(row=0, column=1, padx=5)
        
        self.btn_refresh_midi = tk.Button(self.frame_midi, text="Aggiorna", command=self.refresh_midi_devices)
        self.btn_refresh_midi.grid(row=0, column=2, padx=5)
        
        # Inizializza pygame.midi
        try:
            # Verifica se pygame.midi è già inizializzato
            if not pygame.midi.get_init():
                pygame.midi.init()
                print("pygame.midi inizializzato con successo")
            else:
                print("pygame.midi era già inizializzato")
                
            # Mostra informazioni sui dispositivi MIDI disponibili
            midi_count = pygame.midi.get_count()
            print(f"Dispositivi MIDI disponibili: {midi_count}")
            for i in range(midi_count):
                info = pygame.midi.get_device_info(i)
                name, is_input, is_output, is_opened = info[1].decode(), info[2], info[3], info[4]
                print(f"  Dispositivo {i}: {name} (input: {is_input}, output: {is_output}, aperto: {is_opened})")
            
            self.refresh_midi_devices()
            self.midi_output = None
            self.midi_enabled = False
        except Exception as e:
            print(f"Errore durante l'inizializzazione MIDI: {e}")
            messagebox.showwarning("MIDI non disponibile", f"Impossibile inizializzare MIDI: {e}\nVerrà utilizzato il beep predefinito.")
        
        # Opzioni audio
        self.audio_enabled = True
        self.audio_type = tk.StringVar(value="beep")  # Opzioni: "beep" o "midi"
        
        self.frame_audio = tk.Frame(master)
        self.frame_audio.pack(pady=5)
        
        self.btn_mute = tk.Button(self.frame_audio, text="Mute Audio", command=self.toggle_audio)
        self.btn_mute.grid(row=0, column=0, padx=5)
        
        self.radio_beep = tk.Radiobutton(self.frame_audio, text="Beep", variable=self.audio_type, value="beep")
        self.radio_beep.grid(row=0, column=1, padx=5)
        
        self.radio_midi = tk.Radiobutton(self.frame_audio, text="MIDI", variable=self.audio_type, value="midi")
        self.radio_midi.grid(row=0, column=2, padx=5)

    def carica_immagine(self):
        self.image_path = filedialog.askopenfilename(
            title="Seleziona un'immagine",
            filetypes=(("Immagini JPEG", "*.jpg *.jpeg"),
                       ("Immagini PNG", "*.png"),
                       ("Tutti i file", "*.*"))
        )
        if not self.image_path:
            return

        try:
            # Calcola percentuale e genera immagine verde
            percentuale, img_verde_pil = calcola_percentuale_verde(self.image_path, self.soglia_default, genera_immagine_output=True)

            self.label_risultato.config(text=f"Percentuale verde (soglia {self.soglia_default}): {percentuale}%")

            # Mostra immagine originale
            img_originale_pil = Image.open(self.image_path)
            img_originale_pil.thumbnail((400, 400)) # Riduci per visualizzazione (dimensione aumentata)
            self.img_originale_tk = ImageTk.PhotoImage(img_originale_pil)
            self.panel_originale.config(image=self.img_originale_tk)
            self.panel_originale.image = self.img_originale_tk # Mantieni riferimento

            # Mostra immagine con pixel verdi
            if img_verde_pil:
                img_verde_pil.thumbnail((400, 400)) # Riduci per visualizzazione (dimensione aumentata)
                self.img_verde_tk = ImageTk.PhotoImage(img_verde_pil)
                self.panel_verde.config(image=self.img_verde_tk)
                self.panel_verde.image = self.img_verde_tk # Mantieni riferimento
            else:
                self.panel_verde.config(image=None)
                self.panel_verde.image = None

            # Riproduci suono in base alla percentuale
            self.play_green_sound(percentuale)

        except FileNotFoundError:
            messagebox.showerror("Errore", f"File non trovato: {self.image_path}")
        except ImportError as e:
             messagebox.showerror("Errore di Importazione", f"Errore durante l'importazione di moduli necessari: {e}. Assicurati che Pillow (PIL) sia installato.")
        except Exception as e:
            messagebox.showerror("Errore", f"Si è verificato un errore durante l'elaborazione dell'immagine: {e}")
            self.label_risultato.config(text="Percentuale verde: Errore")
            self.panel_originale.config(image=None)
            self.panel_originale.image = None
            self.panel_verde.config(image=None)
            self.panel_verde.image = None

    def refresh_midi_devices(self):
        try:
            self.midi_devices.set("")
            devices = []
            for i in range(pygame.midi.get_count()):
                info = pygame.midi.get_device_info(i)
                name, is_input, is_output, is_opened = info[1].decode(), info[2], info[3], info[4]
                if is_output == 1:  # Solo dispositivi di output
                    devices.append((i, name))
            
            if devices:
                self.midi_devices["values"] = [name for _, name in devices]
                self.midi_device_ids = [id for id, _ in devices]
                self.midi_devices.current(0)
                self.connect_midi()
            else:
                self.midi_devices["values"] = ["Nessun dispositivo MIDI trovato"]
                self.midi_device_ids = []
                self.midi_enabled = False
        except Exception as e:
            print(f"Errore durante l'aggiornamento dei dispositivi MIDI: {e}")
            self.midi_enabled = False
    
    def connect_midi(self):
        try:
            if hasattr(self, 'midi_output') and self.midi_output is not None:
                del self.midi_output
            
            selected_index = self.midi_devices.current()
            if selected_index >= 0 and selected_index < len(self.midi_device_ids):
                device_id = self.midi_device_ids[selected_index]
                self.midi_output = pygame.midi.Output(device_id)
                self.midi_enabled = True
                print(f"Connesso al dispositivo MIDI: {self.midi_devices.get()} (ID: {device_id})")
                # Invia una nota di test per verificare la connessione
                try:
                    self.midi_output.note_on(60, 100)  # Nota C4 con velocità 100
                    time.sleep(0.1)
                    self.midi_output.note_off(60, 0)
                    print("Test MIDI inviato con successo")
                except Exception as e:
                    print(f"Errore durante il test MIDI: {e}")
            else:
                self.midi_enabled = False
                print("Nessun dispositivo MIDI selezionato o disponibile")
        except Exception as e:
            print(f"Errore durante la connessione al dispositivo MIDI: {e}")
            self.midi_enabled = False
            messagebox.showerror("Errore MIDI", f"Impossibile connettersi al dispositivo MIDI: {e}")
    
    def play_green_sound(self, percentuale):
        if not self.audio_enabled or percentuale <= 0:
            return
        
        # Esegui l'audio in un thread separato per non bloccare l'interfaccia
        threading.Thread(target=self._play_sound, args=(percentuale,), daemon=True).start()
    
    def _play_sound(self, percentuale):
        try:
            if self.audio_type.get() == "beep":
                # Mappiamo la percentuale di verde alla frequenza del suono
                # Frequenza minima: 500 Hz, massima: 2500 Hz
                # Più verde = suono più acuto
                duration_ms = 1000  # Durata esatta di 1 secondo
                freq = int(500 + (percentuale / 100) * 2000)
                
                # Assicuriamoci che la frequenza sia nel range valido per winsound.Beep
                # (tra 37 e 32767 Hz)
                freq = max(37, min(freq, 32767))
                
                # Riproduci il beep con la frequenza calcolata
                winsound.Beep(freq, duration_ms)
            
            elif self.audio_type.get() == "midi":
                if not self.midi_enabled or self.midi_output is None:
                    print("MIDI non abilitato o dispositivo non connesso. Riconnessione in corso...")
                    self.connect_midi()
                    if not self.midi_enabled or self.midi_output is None:
                        print("Impossibile connettersi al dispositivo MIDI")
                        return
                
                # Mappiamo la percentuale di verde a un accordo maggiore
                # Più verde = accordo più alto
                
                # Calcola la nota base (C3 = 60, C7 = 108)
                base_note = int(60 + (percentuale / 100) * 48)
                base_note = max(36, min(base_note, 96))  # Limita il range delle note
                
                # Crea un accordo maggiore (base, terza maggiore, quinta)
                chord = [base_note, base_note + 4, base_note + 7]
                velocity = 100  # Volume (0-127)
                
                print(f"Invio accordo MIDI: {chord} con velocità {velocity}")
                
                try:
                    # Suona l'accordo
                    for note in chord:
                        self.midi_output.note_on(note, velocity)
                        time.sleep(0.01)  # Piccolo ritardo tra le note
                    
                    # Mantieni l'accordo per 1 secondo
                    time.sleep(1)
                    
                    # Rilascia le note
                    for note in chord:
                        self.midi_output.note_off(note, 0)
                        time.sleep(0.01)  # Piccolo ritardo tra le note
                    
                    print("Accordo MIDI inviato con successo")
                except Exception as e:
                    print(f"Errore durante l'invio dell'accordo MIDI: {e}")
                    # Prova a riconnettersi al dispositivo MIDI
                    self.connect_midi()
                
        except Exception as e:
            print(f"Errore durante la riproduzione audio: {e}")

    
    def toggle_audio(self):
        self.audio_enabled = not self.audio_enabled
        if self.audio_enabled:
            self.btn_mute.config(text="Mute Audio")
        else:
            self.btn_mute.config(text="Unmute Audio")

if __name__ == "__main__":
    # Controlla se le dipendenze sono installate
    try:
        from PIL import Image, ImageTk
    except ImportError:
        messagebox.showerror("Dipendenza Mancante", "Pillow (PIL) non è installato. Per favore, installalo eseguendo: pip install Pillow")
        exit()
    
    try:
        import pygame.midi
    except ImportError:
        messagebox.showwarning("Dipendenza Mancante", "pygame non è installato. La funzionalità MIDI non sarà disponibile.\nPer installarla, esegui: pip install pygame")
    
    root = tk.Tk()
    app = GreenDetectorApp(root)
    
    # Funzione per chiudere correttamente l'applicazione
    def on_closing():
        # Chiudi correttamente le risorse MIDI
        if hasattr(app, 'midi_output') and app.midi_output is not None:
            del app.midi_output
        if 'pygame.midi' in sys.modules and pygame.midi.get_init():
            pygame.midi.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()