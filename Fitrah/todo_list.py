import os

FILE_NAME = "tugas.txt"

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_tasks():
    tasks = []
    if not os.path.exists(FILE_NAME):
        return tasks
    with open(FILE_NAME, 'r') as file:
        for line in file:
            parts = line.strip().split('|')
            if len(parts) == 2:
                task = {'desc': parts[0], 'done': parts[1] == '1'}
                tasks.append(task)
    return tasks

def save_tasks(tasks):
    with open(FILE_NAME, 'w') as file:
        for t in tasks:
            status = '1' if t['done'] else '0'
            file.write(f"{t['desc']}|{status}\n")

def show_tasks(tasks):
    if not tasks:
        print("📭 Tidak ada tugas.\n")
        return
    print("📋 Daftar Tugas:\n")
    for i, t in enumerate(tasks):
        status = "✅" if t['done'] else "⏳"
        print(f"{i+1}. [{status}] {t['desc']}")
    print()

def add_task(tasks):
    desc = input("📝 Masukkan deskripsi tugas: ").strip()
    if desc:
        tasks.append({'desc': desc, 'done': False})
        save_tasks(tasks)
        print("✅ Tugas ditambahkan.\n")
    else:
        print("❌ Deskripsi tidak boleh kosong.\n")

def delete_task(tasks):
    show_tasks(tasks)
    if not tasks:
        return
    try:
        idx = int(input("Masukkan nomor tugas yang akan dihapus: ")) - 1
        if 0 <= idx < len(tasks):
            removed = tasks.pop(idx)
            save_tasks(tasks)
            print(f"🗑️ Tugas '{removed['desc']}' dihapus.\n")
        else:
            print("❌ Nomor tidak valid.\n")
    except:
        print("❌ Input tidak valid.\n")

def mark_done(tasks):
    show_tasks(tasks)
    if not tasks:
        return
    try:
        idx = int(input("Tandai tugas selesai nomor: ")) - 1
        if 0 <= idx < len(tasks):
            tasks[idx]['done'] = True
            save_tasks(tasks)
            print("✅ Tugas ditandai selesai.\n")
        else:
            print("❌ Nomor tidak valid.\n")
    except:
        print("❌ Input tidak valid.\n")

def menu():
    print("==== APLIKASI TO-DO LIST ====")
    print("1. Lihat semua tugas")
    print("2. Tambah tugas")
    print("3. Tandai tugas selesai")
    print("4. Hapus tugas")
    print("5. Keluar")
    print("=============================\n")

def main():
    tasks = load_tasks()
    while True:
        clear()
        menu()
        choice = input("Pilih menu (1-5): ").strip()
        if choice == '1':
            clear()
            show_tasks(tasks)
            input("Tekan Enter untuk kembali...")
        elif choice == '2':
            clear()
            add_task(tasks)
            input("Tekan Enter untuk kembali...")
        elif choice == '3':
            clear()
            mark_done(tasks)
            input("Tekan Enter untuk kembali...")
        elif choice == '4':
            clear()
            delete_task(tasks)
            input("Tekan Enter untuk kembali...")
        elif choice == '5':
            print("👋 Sampai jumpa!")
            break
        else:
            print("❌ Pilihan tidak valid.")
            input("Tekan Enter untuk kembali...")

if __name__ == "__main__":
    main()
