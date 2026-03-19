import yaml
import os
import subprocess
import sys
import argparse

# ---------------------------------------------------------
# ฟังก์ชันช่วยค้นหา Odoo Module (สำหรับ Repo ที่ไม่มี includes)
# ---------------------------------------------------------
def get_odoo_modules(base_path):
    modules = []
    try:
        for item in os.listdir(base_path):
            full_path = os.path.join(base_path, item)
            # ถ้าเป็นโฟลเดอร์ และมีไฟล์ __manifest__.py แสดงว่าเป็น Odoo Module
            if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, '__manifest__.py')):
                modules.append(item)
    except Exception:
        pass
    return modules

def get_git_hash():
    """ดึงค่า Git Commit Hash ปัจจุบัน"""
    try:
        result = subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError:
        return None

# ---------------------------------------------------------
# 1. จัดการ Command-line Arguments
# ---------------------------------------------------------
parser = argparse.ArgumentParser(description='เครื่องมือจัดการ Odoo Addons พร้อม Auto-generate Command')
parser.add_argument('-p', '--pull', action='store_true', help='อัปเดต (git pull) โฟลเดอร์ที่มีอยู่แล้ว')
parser.add_argument('-g', '--git', nargs='+', help='ระบุชื่อ Repository ที่ต้องการทำงานด้วย')
args = parser.parse_args()

config_file = 'repos.yaml'
if not os.path.exists(config_file):
    print(f"❌ Error: ไม่พบไฟล์ {config_file}")
    sys.exit(1)

with open(config_file, 'r') as f:
    all_repos = yaml.safe_load(f)

repos_to_process = {}
if args.git:
    for path, data in all_repos.items():
        if path.replace('./', '') in args.git:
            repos_to_process[path] = data
    if not repos_to_process:
        print(f"❌ ไม่พบ Repository ชื่อ {', '.join(args.git)}")
        sys.exit(1)
else:
    repos_to_process = all_repos

print(f"🚀 เริ่มตรวจสอบและดาวน์โหลด {len(repos_to_process)} Repositories...\n")

# *** ตัวแปรเก็บรายชื่อ Module ที่มีการเปลี่ยนแปลง ***
changed_modules = set()

# ---------------------------------------------------------
# 2. วนลูปทำงานทีละโฟลเดอร์
# ---------------------------------------------------------
for path, data in repos_to_process.items():
    target_dir = path.replace('./', '')
    remote_url = data.get('remotes', {}).get('origin')
    merges = data.get('merges', [])
    includes = data.get('includes', [])
    
    if not remote_url or not merges:
        continue

    branch = merges[0].split()[1]

    # --- กรณี A: โฟลเดอร์มีอยู่แล้ว (อัปเดต) ---
    if os.path.exists(target_dir):
        if args.pull:
            print(f"🔄 ตรวจสอบอัปเดต {target_dir}...")
            curr_dir = os.getcwd()
            os.chdir(target_dir)
            
            old_hash = get_git_hash()
            
            try:
                subprocess.run(['git', 'pull'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                new_hash = get_git_hash()
                
                # ถ้า Hash เปลี่ยน = มีการอัปเดตโค้ดจริงๆ
                if old_hash != new_hash:
                    if includes:
                        sparse_cmd = ['git', 'sparse-checkout', 'set', '--no-cone'] + includes
                        subprocess.run(sparse_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        changed_modules.update(includes)
                    else:
                        # สแกนหา Module เองเพราะไม่มี includes
                        changed_modules.update(get_odoo_modules('.'))
                    print(f"   ✨ มีโค้ดใหม่เข้ามา! (อัปเดตสำเร็จ)")
                else:
                    print(f"   ➖ ไม่มีอัปเดตใหม่ (Up to date)")
                    
            except subprocess.CalledProcessError:
                print(f"   ❌ อัปเดตล้มเหลว")
            finally:
                os.chdir(curr_dir)
        else:
            print(f"⏭️ ข้าม {target_dir}: มีอยู่แล้ว (ใช้ -p เพื่ออัปเดต)")
        continue

    # --- กรณี B: โหลดโฟลเดอร์ใหม่ (โคลนใหม่ถือว่ามีการเปลี่ยนแปลงเสมอ) ---
    print(f"📦 โคลนใหม่ {target_dir} (Branch: {branch})...")
    try:
        if includes:
            clone_cmd = ['git', 'clone', '--filter=blob:none', '--sparse', '--depth', '1', '--branch', branch, remote_url, target_dir]
            subprocess.run(clone_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            os.chdir(target_dir)
            sparse_cmd = ['git', 'sparse-checkout', 'set', '--no-cone'] + includes
            subprocess.run(sparse_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.chdir('..')
            
            changed_modules.update(includes)
            
        else:
            clone_cmd = ['git', 'clone', '--depth', '1', '--branch', branch, remote_url, target_dir]
            subprocess.run(clone_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            changed_modules.update(get_odoo_modules(target_dir))

        print(f"   ✅ โคลนสำเร็จ\n")
    except subprocess.CalledProcessError:
        print(f"   ❌ โคลนล้มเหลว\n")

# ---------------------------------------------------------
# 3. สรุปผลและสร้างคำสั่ง Odoo (Odoo Command Generator)
# ---------------------------------------------------------
print("-" * 50)
if changed_modules:
    modules_str = ",".join(sorted(changed_modules))
    print("🎉 สรุป: พบ Modules ที่ถูกเพิ่มหรืออัปเดตใหม่!")
    print("\n💡 คุณสามารถ Copy คำสั่งด้านล่างไปรันเพื่อ Update Odoo ได้เลย:\n")
    
    # คำสั่งสำหรับรันแบบ Native (odoo-bin)
    print("👉 [รันแบบ Native / Virtual Env]")
    print(f"python odoo-bin -c odoo.conf -d <YOUR_DB_NAME> -u {modules_str}\n")
    
    # คำสั่งสำหรับรันแบบ Docker (ถ้าคุณใช้ Docker Compose)
    print("👉 [รันแบบ Docker Compose (Odoo 18)]")
    print(f"docker compose exec web odoo -c /etc/odoo/odoo.conf -d <YOUR_DB_NAME> -u {modules_str}\n")
else:
    print("🎉 ทำงานเสร็จสมบูรณ์! (ไม่มี Module ไหนที่มีการเปลี่ยนแปลง)")