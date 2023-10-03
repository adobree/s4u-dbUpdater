import tkinter as tk
import time

def update_timer():
    global remaining_time

    remaining_time -= 1
    if remaining_time <= 0:
        remaining_time = 300  # 5 perc újraindítása
        label.config(text="Visszaszámláló: 5:00")
    else:
        minutes = remaining_time // 60
        seconds = remaining_time % 60
        label.config(text="Visszaszámláló: {:02d}:{:02d}".format(minutes, seconds))

    root.after(1000, update_timer)  # Frissítés 1 másodpercenként

# Főalkalmazás
root = tk.Tk()
root.title("5 perces visszaszámláló")

remaining_time = 300  # 5 perc = 300 másodperc

label = tk.Label(root, text="Visszaszámláló: 5:00", font=("Arial", 24))
label.pack(padx=20, pady=20)

update_timer()  # Első frissítés

root.mainloop()
