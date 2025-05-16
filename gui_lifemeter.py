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
        self.panel_originale = tk.Canvas(self.frame_immagini)
        self.panel_originale.grid(row=1, column=0, padx=10)
        self.panel_originale.bind("<ButtonPress-1>", self.inizio_selezione)
        self.panel_originale.bind("<B1-Motion>", self.disegna_selezione)
        self.panel_originale.bind("<ButtonRelease-1>", self.fine_selezione)

        # Aggiungi pulsante per abilitare/disabilitare la selezione area
        self.btn_selezione = tk.Button(self.frame_immagini, text="Seleziona Area", command=self.toggle_selezione)
        self.btn_selezione.grid(row=2, column=0, pady=5)
        
        self.selezione_attiva = False
        self.area_selezione = None  # (x1, y1, x2, y2)
        self.label_verde_testo = tk.Label(self.frame_immagini, text="Pixel Verdi Rilevati:")
        self.label_verde_testo.grid(row=0, column=1, padx=10)
        self.panel_verde = tk.Label(self.frame_immagini)
        self.panel_verde.grid(row=1, column=1, padx=10)

        self.label_risultato = tk.Label(master, text="Percentuale verde: -")
        self.label_risultato.pack(pady=10)
        
        # Pulsante per riprodurre il suono senza ricaricare l'immagine
        self.btn_riproduci_suono = tk.Button(master, text="Riproduci Suono", command=self.riproduci_suono, state=tk.DISABLED)
        self.btn_riproduci_suono.pack(pady=5)

        self.image_path = None
        self.img_originale_tk = None
        self.img_verde_tk = None
        self.ultima_percentuale = None  # Memorizza l'ultima percentuale calcolata

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

    def _analizza_e_aggiorna_ui(self):
        if not self.image_path:
            # messagebox.showinfo("Info", "Carica prima un'immagine.")
            return

        try:
            # Calcola percentuale solo nell'area selezionata
            percentuale, img_verde_pil = calcola_percentuale_verde(
                self.image_path,
                self.soglia_default,
                genera_immagine_output=True,
                area_di_interesse=self.area_selezione
            )
            self.label_risultato.config(text=f"Percentuale verde (soglia {self.soglia_default}): {percentuale}%")

            # Mostra immagine con pixel verdi
            if img_verde_pil:
                img_verde_pil.thumbnail((400, 400))
                self.img_verde_tk = ImageTk.PhotoImage(img_verde_pil)
                self.panel_verde.config(image=self.img_verde_tk)
                self.panel_verde.image = self.img_verde_tk
            else:
                self.panel_verde.config(image=None)
                self.panel_verde.image = None

            self.ultima_percentuale = percentuale
            self.btn_riproduci_suono.config(state=tk.NORMAL)
            # Non riprodurre il suono automaticamente qui, ma solo su richiesta
            # self.play_green_sound(percentuale) 

        except FileNotFoundError:
            messagebox.showerror("Errore", f"File non trovato: {self.image_path}")
            self.label_risultato.config(text="Percentuale verde: Errore")
            self.panel_verde.config(image=None)
            self.panel_verde.image = None
            self.btn_riproduci_suono.config(state=tk.DISABLED)
            self.ultima_percentuale = None
        except ImportError as e:
            messagebox.showerror("Errore di Importazione", f"Errore durante l'importazione di moduli necessari: {e}. Assicurati che Pillow (PIL) sia installato.")
        except Exception as e:
            messagebox.showerror("Errore", f"Si è verificato un errore durante l'elaborazione dell'immagine: {e}")
            self.label_risultato.config(text="Percentuale verde: Errore")
            self.panel_verde.config(image=None)
            self.panel_verde.image = None
            self.btn_riproduci_suono.config(state=tk.DISABLED)
            self.ultima_percentuale = None

    def carica_immagine(self):
        new_image_path = filedialog.askopenfilename(
            title="Seleziona un'immagine",
            filetypes=(("Immagini JPEG", "*.jpg *.jpeg"),
                       ("Immagini PNG", "*.png"),
                       ("Tutti i file", "*.*"))
        )
        if not new_image_path:
            return
        
        self.image_path = new_image_path
        self.area_selezione = None # Resetta l'area di selezione quando si carica una nuova immagine

        try:
            # Pulisci il canvas prima di caricare una nuova immagine
            self.panel_originale.delete("all")
            
            # Mostra immagine originale
            img_originale_pil = Image.open(self.image_path)
            img_originale_pil.thumbnail((400, 400))
            self.img_originale_tk = ImageTk.PhotoImage(img_originale_pil)
            self.panel_originale.config(width=img_originale_pil.width, height=img_originale_pil.height)
            self.img_id = self.panel_originale.create_image(0, 0, anchor=tk.NW, image=self.img_originale_tk)

            # Ora analizza l'intera immagine
            self._analizza_e_aggiorna_ui()
            if self.ultima_percentuale is not None:
                 self.play_green_sound(self.ultima_percentuale) # Riproduci suono dopo caricamento iniziale

        except FileNotFoundError:
            messagebox.showerror("Errore", f"File non trovato: {self.image_path}")
        except ImportError as e:
            messagebox.showerror("Errore di Importazione", f"Errore durante l'importazione di moduli necessari: {e}. Assicurati che Pillow (PIL) sia installato.")
        except Exception as e:
            messagebox.showerror("Errore", f"Si è verificato un errore durante il caricamento dell'immagine: {e}")
            self.label_risultato.config(text="Percentuale verde: Errore")
            self.panel_originale.config(image=None)
            self.panel_originale.image = None
            self.panel_verde.config(image=None)
            self.panel_verde.image = None
            self.btn_riproduci_suono.config(state=tk.DISABLED)
            self.ultima_percentuale = None

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
    
    def riproduci_suono(self):
        """Riproduce il suono basato sull'ultima percentuale di verde rilevata"""
        if self.ultima_percentuale is not None:
            self.play_green_sound(self.ultima_percentuale)
        else:
            messagebox.showinfo("Nessun dato", "Carica prima un'immagine per analizzare la percentuale di verde.")
            self.btn_riproduci_suono.config(state=tk.DISABLED)

    def toggle_selezione(self):
        self.selezione_attiva = not self.selezione_attiva
        if self.selezione_attiva:
            self.btn_selezione.config(text="Annulla Selezione", bg='lightcoral') # o un altro colore per indicare attività
            messagebox.showinfo("Selezione Area", "Clicca e trascina sull'immagine originale per selezionare l'area di analisi.")
        else:
            self.btn_selezione.config(text="Seleziona Area", bg='SystemButtonFace')
            self.area_selezione = None
            # Rimuovi il rettangolo di selezione se presente
            if hasattr(self, 'rect_id') and self.rect_id:
                self.panel_originale.delete(self.rect_id)
                self.rect_id = None
            if self.image_path:
                self._analizza_e_aggiorna_ui() # Ricalcola sull'intera immagine
    
    def aggiorna_anteprima(self):
        # Metodo per aggiornare l'anteprima dell'immagine
        if self.image_path:
            self._analizza_e_aggiorna_ui()

    def inizio_selezione(self, event):
        if self.selezione_attiva and self.img_originale_tk:
            self.start_x = event.x
            self.start_y = event.y
            self.rect_id = self.panel_originale.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)

    def disegna_selezione(self, event):
        if self.selezione_attiva and self.img_originale_tk and hasattr(self, 'rect_id'):
            self.panel_originale.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def fine_selezione(self, event):
        if self.selezione_attiva and self.img_originale_tk:
            # Converti coordinate relative all'immagine ridimensionata
            img_width = self.panel_originale.winfo_width()
            img_height = self.panel_originale.winfo_height()
            
            # Calcola rapporto dimensionale originale/anteprima
            original_width, original_height = Image.open(self.image_path).size
            x_ratio = original_width / img_width
            y_ratio = original_height / img_height
            
            # Normalizza coordinate
            x1 = min(max(int(self.start_x * x_ratio), 0), original_width)
            y1 = min(max(int(self.start_y * y_ratio), 0), original_height)
            x2 = min(max(int(event.x * x_ratio), 0), original_width)
            y2 = min(max(int(event.y * y_ratio), 0), original_height)
            
            self.area_selezione = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            if self.image_path:
                self._analizza_e_aggiorna_ui() # Analizza l'area appena selezionata
            # Non disattivare la selezione automaticamente qui, l'utente potrebbe volerla modificare
            # self.toggle_selezione() # Opzionale: disattiva la modalità selezione dopo averla completata

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
    
    def riproduci_suono(self):
        """Riproduce il suono basato sull'ultima percentuale di verde rilevata"""
        if self.ultima_percentuale is not None:
            self.play_green_sound(self.ultima_percentuale)
        else:
            messagebox.showinfo("Nessun dato", "Carica prima un'immagine per analizzare la percentuale di verde.")
            self.btn_riproduci_suono.config(state=tk.DISABLED)

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