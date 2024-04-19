import psutil
import subprocess
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Ma'lumotlarni saqlash uchun ro'yxatlar
all_process_data = {}
disk_data = []

# GPU ma'lumotlarini olish
def get_gpu_info():
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        gpu_info = result.stdout
        return gpu_info
    except FileNotFoundError:
        return "GPU ma'lumotlarini olish uchun nvidia-smi dasturi topilmadi."

# Disk yozish va o'qish ma'lumotlarini olish
def get_disk_io():
    disk_io = psutil.disk_io_counters()
    disk_data.append((disk_io.write_bytes, disk_io.read_bytes))

# Dastur nomi boyicha xotiradagi joy va CPU ishlatilish ma'lumotlarini olish
def get_process_info(process_name):
    try:
        process_id = None
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == process_name:
                process_id = proc.info['pid']
                break

        if process_id is None:
            return None, None, None

        process = psutil.Process(process_id)
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / (1024 * 1024)  # Convert bytes to megabytes
        cpu_percent = process.cpu_percent(interval=1)  # CPU usage in percent
        return process_id, memory_usage_mb, cpu_percent
    except psutil.NoSuchProcess:
        return None, None, None

# Dastur ma'lumotlarini kuzatishni boshlash
def start_monitor():
    process_name = entry.get().strip()
    if process_name:
        process_id, _, _ = get_process_info(process_name)
        if process_id is not None:
            all_process_data[process_id] = []
            monitor_process(process_id)  # Yangilovchi funksiyani bir marta chaqirish
        else:
            result_label.config(text="Xatolik: Kiritilgan dastur nomi bo'yicha topa olmadim!")

# Dastur ma'lumotlarini kuzatish
def monitor_process(process_id):
    memory_usage, cpu_usage = get_process_info_by_id(process_id)
    if memory_usage is not None and cpu_usage is not None:
        all_process_data[process_id].append((memory_usage, cpu_usage))
        memory_data = [data[0] for data in all_process_data[process_id]]
        cpu_data = [data[1] for data in all_process_data[process_id]]
        ax[0].clear()  # Grafikni tozalash
        ax[0].plot(memory_data, 'r-')  # Yangi ma'lumotlarni qo'shish
        ax[0].set_title('Xotiradagi Joy (MB)')  # Grafik sarlavhasini sozlash
        ax[1].clear()
        ax[1].plot(cpu_data, 'b-')
        ax[1].set_title('CPU Ishlatilishi')
        canvas.draw()  # Grafiklarni yangilash
        result_label.config(text=f"Dastur xotiradagi joy: {memory_usage:.2f} MB\nDastur CPU ishlatilishi: {cpu_usage:.2f}%")
    else:
        result_label.config(text="Xatolik: Ma'lumotlar olishda muammo")

    get_disk_io()
    disk_write_data = [data[0] for data in disk_data]
    disk_read_data = [data[1] for data in disk_data]
    ax[2].clear()
    ax[2].plot(disk_write_data, 'g-', label='Disk Yozish')
    ax[2].plot(disk_read_data, 'y-', label='Disk O\'qish')
    ax[2].set_title('Disk Yozish va O\'qish (Bytes)')
    ax[2].legend()
    canvas.draw()

    # Keyingi monitor_process chaqirishini belgilash
    root.after(1000, monitor_process, process_id)

# Ma'lumotlarni saqlash
def save_data():
    with open('monitor_data.txt', 'w') as file:
        for process_id, process_data in all_process_data.items():
            file.write(f"Process ID: {process_id}\n")
            for memory_usage, cpu_usage in process_data:
                file.write(f"Memory Usage: {memory_usage:.2f} MB, CPU Usage: {cpu_usage:.2f}%\n")
        for disk_write, disk_read in disk_data:
            file.write(f"Disk Write: {disk_write} bytes, Disk Read: {disk_read} bytes\n")
    result_label.config(text="Ma'lumotlar faylga saqlandi: monitor_data.txt")

# Dastur nomi boyicha ma'lumotlarni olish
def get_process_info_by_id(process_id):
    try:
        process = psutil.Process(process_id)
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / (1024 * 1024)  # Convert bytes to megabytes
        cpu_percent = process.cpu_percent(interval=1)  # CPU usage in percent
        return memory_usage_mb, cpu_percent
    except psutil.NoSuchProcess:
        return None, None

# Dastur GUI
root = tk.Tk()
root.title("Dastur ma'lumotlarini kuzatish")

label = tk.Label(root, text="Ishlatmoqchi bo'lgan dasturning nomini kiriting:")
label.pack()

entry = tk.Entry(root)
entry.pack()

button_start = tk.Button(root, text="Kuzatishni boshlash", command=start_monitor)
button_start.pack()

button_stop = tk.Button(root, text="To'xtatish", command=root.quit)  # Monitoringni to'xtatish uchun
button_stop.pack()

button_save = tk.Button(root, text="Save Data", command=save_data)
button_save.pack()

result_label = tk.Label(root, text="")
result_label.pack()

gpu_info_label = tk.Label(root, text="")
gpu_info_label.pack()

# Grafiklar
fig, ax = plt.subplots(4, 1)  # Grafiklar sonini oshirish
ax[0].set_title('Xotiradagi Joy (MB)')
ax[1].set_title('CPU Ishlatilishi')
ax[2].set_title('Disk Yozish va O\'qish (Bytes)')
ax[3].set_title('GPU Ma\'lumotlari')  # Yangi grafik uchun sarlavha

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# Yangilovchi funksiya boshlanishi
start_monitor()
gpu_info_label.config(text=get_gpu_info())  # GPU ma'lumotlarini ko'rsatish
root.mainloop()
