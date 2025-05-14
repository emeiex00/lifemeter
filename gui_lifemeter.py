import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import winsound # Per l'audio su Windows
import math # Per la frequenza del suono

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

        self.audio_enabled = True
        self.btn_mute = tk.Button(master, text="Mute Audio", command=self.toggle_audio)
        self.btn_mute.pack(pady=5)

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

    def play_green_sound(self, percentuale):
        if not self.audio_enabled or percentuale <= 0:
            return
        try:
            # Frequenza più alta per percentuali maggiori, durata breve
            # Esempio: da 500 Hz (bassa % verde) a 2500 Hz (alta % verde)
            # Evitiamo frequenze troppo basse o troppo alte che potrebbero non essere udibili o fastidiose
            min_freq = 500
            max_freq = 2500
            # Mappiamo la percentuale (0-100) alla gamma di frequenze
            # Qui usiamo una semplice mappatura lineare per iniziare, poi si può affinare
            freq = int(min_freq + (percentuale / 100) * (max_freq - min_freq))
            
            # Assicuriamoci che la frequenza sia nel range valido per winsound.Beep (37 through 32,767 hertz)
            freq = max(37, min(freq, 32767))
            
            duration_ms = 1000 # Durata del suono in millisecondi
            winsound.Beep(freq, duration_ms)
        except Exception as e:
            print(f"Errore durante la riproduzione del suono: {e}")

    def toggle_audio(self):
        self.audio_enabled = not self.audio_enabled
        if self.audio_enabled:
            self.btn_mute.config(text="Mute Audio")
        else:
            self.btn_mute.config(text="Unmute Audio")

if __name__ == "__main__":
    # Controlla se Pillow è installato
    try:
        from PIL import Image, ImageTk
    except ImportError:
        messagebox.showerror("Dipendenza Mancante", "Pillow (PIL) non è installato. Per favore, installalo eseguendo: pip install Pillow")
        exit()

    root = tk.Tk()
    app = GreenDetectorApp(root)
    root.mainloop()