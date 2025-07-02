import datetime
import time
import os

FILE_NAME = "reminder.txt"

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_reminders():
    reminders = []
    if not os.path.exists(FILE_NAME):
        return reminders
    with open(FILE_NAME, 'r') as file:
        for line in file:
            parts = line.strip().split('|')
            if len(parts) == 3:
                try:
                    date_time = datetime.datetime.strptime(parts[0], '%Y-%m-%d %H:%M')
                    description = parts[1]
                    done = parts[2] == '1'
                    reminders.append({
                        'datetime': date_time,
                        'description': description,
                        'done': done
                    })
                except:
                    continue
    return reminders

def save_reminders(reminders):
    with open(FILE_NAME, 'w') as file:
        for r in reminders:
            dt_str = r['datetime'].strftime('%Y-%m-%d %H:%M')
            line = f"{dt_str}|{r['description']}|{'1' if r['done'] else '0'}\n"
            file.write(line)

def add_reminder(reminders):
    try:
        date_input = input("Tanggal (YYYY-MM-DD): ")
        time_input = input("Jam (HH:MM): ")
        desc = input("Deskripsi: ")

        reminder_time = datetime.datetime.strptime(f"{date_input} {time_input}", '%Y-%m-%d %H:%M')
        reminders.append({
            'datetime': reminder_time,
            'description': desc,
            'done': False
        })
        save_reminders(reminders)
        print("✅ Pengingat berhasil ditambahkan!\n")
    except:
        print("❌ Format tanggal/jam salah. Ulangi.\n")

def list_reminders(reminders):
    if not reminders:
        print("📭 Tidak ada pengingat.\n")
        return
    print("📅 Daftar Pengingat:\n")
    for i, r in enumerate(reminders):
        status = "✅" if r['done'] else "⏰"
        print(f"{i+1}. [{status}] {r['datetime'].strftime('%Y-%m-%d %H:%M')} - {r['description']}")
    print()

def delete_reminder(reminders):
    list_reminders(reminders)
    if not reminders:
        return
    try:
        idx = int(input("Nomor yang ingin dihapus: ")) - 1
        if 0 <= idx < len(reminders):
            removed = reminders.pop(idx)
            save_reminders(reminders)
            print(f"🗑️ Pengingat '{removed['description']}' dihapus.\n")
        else:
            print("❌ Nomor tidak valid.\n")
    except:
        print("❌ Masukan tidak valid.\n")

def mark_done(reminders):
    list_reminders(reminders)
    if not reminders:
        return
    try:
        idx = int(input("Nomor yang sudah selesai: ")) - 1
        if 0 <= idx < len(reminders):
            reminders[idx]['done'] = True
            save_reminders(reminders)
            print("✅ Pengingat ditandai selesai.\n")
        else:
            print("❌ Nomor tidak valid.\n")
    except:
        print("❌ Masukan tidak valid.\n")

def check_reminders(reminders):
    now = datetime.datetime.now().replace(second=0, microsecond=0)
    for r in reminders:
        if not r['done'] and r['datetime'] == now:
            print(f"\n🔔 PENGINGAT: {r['description']} ({r['datetime'].strftime('%H:%M')})")
            r['done'] = True
            save_reminders(reminders)

def main_menu():
    print("=== APLIKASI PENGINGAT HARIAN ===")
    print("1. Tambah Pengingat")
    print("2. Lihat Pengingat")
    print("3. Hapus Pengingat")
    print("4. Tandai Selesai")
    print("5. Keluar")
    print("===============================\n")

def main():
    reminders = load_reminders()
    while True:
        cls()
        check_reminders(reminders)
        main_menu()
        choice = input("Pilihan: ").strip()
        if choice == '1':
            add_reminder(reminders)
            input("Tekan Enter untuk kembali...")
        elif choice == '2':
            list_reminders(reminders)
            input("Tekan Enter untuk kembali...")
        elif choice == '3':
            delete_reminder(reminders)
            input("Tekan Enter untuk kembali...")
        elif choice == '4':
            mark_done(reminders)
            input("Tekan Enter untuk kembali...")
        elif choice == '5':
            print("👋 Sampai jumpa!")
            break
        else:
            print("❌ Pilihan tidak valid.")
            time.sleep(1)

if __name__ == "__main__":
    main()
