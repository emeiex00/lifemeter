from PIL import Image
import argparse

def calcola_percentuale_verde(image_path, soglia=5, genera_immagine_output=False):
    img = Image.open(image_path)
    img_rgb = img.convert('RGB')
    width, height = img.size
    data_rgb = list(img_rgb.getdata())

    pixel_verdi_cont = 0
    output_img_data = None

    if genera_immagine_output:
        # Crea una nuova immagine RGBA per supportare la trasparenza
        output_img = Image.new('RGBA', (width, height), (0, 0, 0, 0)) 
        output_pixels = output_img.load()

    new_data = []
    for i, (r, g, b) in enumerate(data_rgb):
        if g > r + soglia and g > b + soglia:
            pixel_verdi_cont += 1
            if genera_immagine_output:
                # Copia il pixel verde sull'immagine di output
                x = i % width
                y = i // width
                output_pixels[x, y] = (r, g, b, 255) # Rendi il pixel opaco
        elif genera_immagine_output:
            # Lascia il pixel trasparente se non è verde
            pass # Già inizializzato trasparente
    
    percentuale = round((pixel_verdi_cont / len(data_rgb)) * 100, 2) if len(data_rgb) > 0 else 0

    if genera_immagine_output:
        return percentuale, output_img
    else:
        return percentuale

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calcola la percentuale di verde in un\'immagine')
    parser.add_argument('--image', type=str, required=True, help='Percorso dell\'immagine da analizzare')
    parser.add_argument('--soglia', type=int, default=2, help='Soglia di rilevamento verde (default: 2)')
    
    args = parser.parse_args()
    
    percentuale, immagine_verde = calcola_percentuale_verde(args.image, args.soglia, genera_immagine_output=True)
    print(f"Percentuale verde: {percentuale}%")

    # Salva l'immagine con i soli pixel verdi
    try:
        output_image_path = "green_pixels_detected.png"
        immagine_verde.save(output_image_path)
        print(f"Immagine con pixel verdi salvata in: {output_image_path}")
    except Exception as e:
        print(f"Errore durante il salvataggio dell'immagine dei pixel verdi: {e}")