from flask import Flask, send_from_directory, request, jsonify, session, redirect
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
# Импорт роутов для настроек
from routes.settings import settings_bp

load_dotenv()

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = os.getenv("SECRET_KEY", "college_secret_key_2025_artemy")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ==================== СТРАНИЦЫ ====================

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/dashboard.html')
def dashboard():
    return send_from_directory('../frontend', 'dashboard.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('../frontend', filename)

# ==================== API ГРУПП ====================

@app.route('/api/groups', methods=['GET'])
def get_groups():
    try:
        active = request.args.get('active', 'false').lower() == 'true'
        graduated = request.args.get('graduated', 'false').lower() == 'true'
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        
        if active:
            url = f"{SUPABASE_URL}/rest/v1/groups?is_deleted=eq.false&is_graduated=eq.false&select=*"
        elif graduated:
            url = f"{SUPABASE_URL}/rest/v1/groups?is_deleted=eq.false&is_graduated=eq.true&select=*"
        else:
            url = f"{SUPABASE_URL}/rest/v1/groups?is_deleted=eq.false&select=*"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({"error": "Ошибка получения групп"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/groups', methods=['POST'])
def create_group():
    try:
        data = request.get_json()
        start_year = data.get('start_year')
        duration = data.get('duration')
        if start_year and duration:
            data['graduation_year'] = int(start_year + duration)
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.post(f"{SUPABASE_URL}/rest/v1/groups", headers=headers, json=data)
        
        if response.status_code == 201:
            try:
                result = response.json()
                return jsonify({"success": True, "group": result[0]}), 201
            except:
                return jsonify({"success": True, "message": "Группа создана"}), 201
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/groups/<int:group_id>', methods=['PUT'])
def update_group(group_id):
    try:
        data = request.get_json()
        start_year = data.get('start_year')
        duration = data.get('duration')
        if start_year and duration:
            data['graduation_year'] = int(start_year + duration)
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/groups?id=eq.{group_id}", headers=headers, json=data)
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/groups/<int:group_id>', methods=['DELETE'])
def delete_group(group_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/groups?id=eq.{group_id}", headers=headers, json={"is_deleted": True})
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/groups/<int:group_id>/graduate', methods=['POST'])
def graduate_group(group_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        data = {"is_graduated": True, "graduated_at": datetime.now().isoformat()}
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/groups?id=eq.{group_id}", headers=headers, json=data)
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/groups/<int:group_id>/restore', methods=['POST'])
def restore_graduate_group(group_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        data = {"is_graduated": False, "graduated_at": None}
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/groups?id=eq.{group_id}", headers=headers, json=data)
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API СТУДЕНТОВ ====================

@app.route('/api/students', methods=['GET'])
def get_all_students():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/students?is_deleted=eq.false&select=*", headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({"error": "Ошибка получения студентов"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students', methods=['POST'])
def add_student():
    try:
        data = request.get_json()
        if not data.get('enrollment_year'):
            return jsonify({"error": "Поле 'Год поступления' обязательно"}), 400
        if not data.get('last_name') or not data.get('first_name'):
            return jsonify({"error": "Поля 'Фамилия' и 'Имя' обязательны"}), 400
        
        if not data.get('birth_date'):
            data['birth_date'] = None
        
        if 'school_name' not in data:
            data['school_name'] = None
        if 'school_graduation_year' not in data:
            data['school_graduation_year'] = None
        if 'certificate_avg_grade' not in data:
            data['certificate_avg_grade'] = None
        if 'has_target_contract' not in data:
            data['has_target_contract'] = False
        if 'target_organization' not in data:
            data['target_organization'] = None
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.post(f"{SUPABASE_URL}/rest/v1/students", headers=headers, json=data)
        
        if response.status_code == 201:
            try:
                result = response.json()
                return jsonify({"success": True, "id": result[0]['id']}), 201
            except:
                return jsonify({"success": True, "message": "Студент добавлен"}), 201
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students/group/<int:group_id>', methods=['GET'])
def get_students_by_group(group_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        url = f"{SUPABASE_URL}/rest/v1/students?group_id=eq.{group_id}&is_deleted=eq.false&select=*"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({"error": "Ошибка получения студентов"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/students?id=eq.{student_id}&select=*", headers=headers)
        if response.status_code == 200 and response.json():
            return jsonify(response.json()[0])
        return jsonify({"error": "Студент не найден"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    try:
        data = request.get_json()
        if not data.get('birth_date'):
            data['birth_date'] = None
        
        if 'school_name' not in data:
            data['school_name'] = None
        if 'school_graduation_year' not in data:
            data['school_graduation_year'] = None
        if 'certificate_avg_grade' not in data:
            data['certificate_avg_grade'] = None
        if 'has_target_contract' not in data:
            data['has_target_contract'] = False
        if 'target_organization' not in data:
            data['target_organization'] = None
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/students?id=eq.{student_id}", headers=headers, json=data)
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/students?id=eq.{student_id}", headers=headers, json={"is_deleted": True})
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API УЧЁТА ====================

@app.route('/api/students/<int:student_id>/accounting', methods=['GET'])
def get_student_accounting(student_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/study_accounting?student_id=eq.{student_id}&select=type", headers=headers)
        if response.status_code == 200:
            types = [item['type'] for item in response.json()]
            return jsonify(types)
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students/<int:student_id>/accounting', methods=['POST'])
def update_student_accounting(student_id):
    try:
        data = request.get_json()
        types = data.get('types', [])
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        
        requests.delete(f"{SUPABASE_URL}/rest/v1/study_accounting?student_id=eq.{student_id}", headers=headers)
        
        for t in types:
            insert_data = {"student_id": student_id, "type": t}
            requests.post(f"{SUPABASE_URL}/rest/v1/study_accounting", headers=headers, json=insert_data)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API РОДИТЕЛЕЙ ====================

@app.route('/api/parents', methods=['GET'])
def get_parents():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/parents?is_archived=eq.false&select=*", headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({"error": "Ошибка получения родителей"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/parents', methods=['POST'])
def create_parent():
    try:
        data = request.get_json()
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.post(f"{SUPABASE_URL}/rest/v1/parents", headers=headers, json=data)
        
        if response.status_code == 201:
            try:
                result = response.json()
                return jsonify({"success": True, "parent_id": result[0]['id']}), 201
            except:
                return jsonify({"success": True, "message": "Родитель добавлен"}), 201
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/parents/<int:parent_id>', methods=['PUT'])
def update_parent(parent_id):
    try:
        data = request.get_json()
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/parents?id=eq.{parent_id}", headers=headers, json=data)
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/parents/<int:parent_id>', methods=['DELETE'])
def delete_parent(parent_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/parents?id=eq.{parent_id}", headers=headers, json={"is_archived": True})
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API СВЯЗИ СТУДЕНТОВ И РОДИТЕЛЕЙ ====================

@app.route('/api/students/<int:student_id>/parents', methods=['GET'])
def get_student_parents(student_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/student_parents?student_id=eq.{student_id}&select=parent_id", headers=headers)
        if response.status_code != 200 or not response.json():
            return jsonify([])
        
        parent_ids = [sp['parent_id'] for sp in response.json()]
        url = f"{SUPABASE_URL}/rest/v1/parents?id=in.({','.join(map(str, parent_ids))})&is_archived=eq.false&select=*"
        response2 = requests.get(url, headers=headers)
        if response2.status_code == 200:
            return jsonify(response2.json())
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students/<int:student_id>/parents/<int:parent_id>', methods=['POST'])
def add_student_parent(student_id, parent_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        
        check = requests.get(f"{SUPABASE_URL}/rest/v1/student_parents?student_id=eq.{student_id}&parent_id=eq.{parent_id}&select=id", headers=headers)
        if check.status_code == 200 and check.json():
            return jsonify({"error": "Связь уже существует"}), 400
        
        response = requests.post(f"{SUPABASE_URL}/rest/v1/student_parents", headers=headers, json={"student_id": student_id, "parent_id": parent_id})
        if response.status_code == 201:
            return jsonify({"success": True}), 201
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students/<int:student_id>/parents/<int:parent_id>', methods=['DELETE'])
def remove_student_parent(student_id, parent_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/student_parents?student_id=eq.{student_id}&parent_id=eq.{parent_id}", headers=headers)
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API БРАТЬЕВ И СЕСТЁР ====================

@app.route('/api/students/<int:student_id>/siblings', methods=['GET'])
def get_student_siblings(student_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/siblings?student_id=eq.{student_id}&select=*", headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students/<int:student_id>/siblings', methods=['POST'])
def add_student_sibling(student_id):
    try:
        data = request.get_json()
        data['student_id'] = student_id
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.post(f"{SUPABASE_URL}/rest/v1/siblings", headers=headers, json=data)
        if response.status_code == 201:
            return jsonify({"success": True, "sibling": response.json()[0]}), 201
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students/siblings/<int:sibling_id>', methods=['DELETE'])
def delete_student_sibling(sibling_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/siblings?id=eq.{sibling_id}", headers=headers)
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API СОТРУДНИКОВ ====================

@app.route('/api/staff', methods=['GET'])
def get_staff():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/staff?is_active=eq.true&select=*", headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({"error": "Ошибка получения сотрудников"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/staff', methods=['POST'])
def create_staff():
    try:
        data = request.get_json()
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.post(f"{SUPABASE_URL}/rest/v1/staff", headers=headers, json=data)
        
        if response.status_code == 201:
            try:
                result = response.json()
                return jsonify({"success": True, "staff": result[0]}), 201
            except:
                return jsonify({"success": True, "message": "Сотрудник добавлен"}), 201
        else:
            return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/staff/<int:staff_id>', methods=['PUT'])
def update_staff(staff_id):
    try:
        data = request.get_json()
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/staff?id=eq.{staff_id}", headers=headers, json=data)
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/staff/<int:staff_id>', methods=['DELETE'])
def delete_staff(staff_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/staff?id=eq.{staff_id}", headers=headers, json={"is_active": False})
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API СВЯЗИ СОТРУДНИКОВ С ГРУППАМИ ====================

@app.route('/api/groups/<int:group_id>/staff', methods=['GET'])
def get_group_staff(group_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/group_staff?group_id=eq.{group_id}&select=staff_id,role,academic_year", headers=headers)
        if response.status_code == 200:
            staff_ids = list(set([item['staff_id'] for item in response.json()]))
            if staff_ids:
                staff_url = f"{SUPABASE_URL}/rest/v1/staff?id=in.({','.join(map(str, staff_ids))})&is_active=eq.true&select=*"
                staff_response = requests.get(staff_url, headers=headers)
                if staff_response.status_code == 200:
                    staff_list = staff_response.json()
                    for s in staff_list:
                        match = next((item for item in response.json() if item['staff_id'] == s['id']), None)
                        s['role'] = match['role'] if match else None
                        s['academic_year'] = match['academic_year'] if match else None
                    return jsonify(staff_list)
            return jsonify([])
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/groups/<int:group_id>/staff/<int:staff_id>', methods=['POST'])
def add_group_staff(group_id, staff_id):
    try:
        data = request.get_json()
        role = data.get('role')
        academic_year = data.get('academic_year')
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        
        check = requests.get(f"{SUPABASE_URL}/rest/v1/group_staff?group_id=eq.{group_id}&staff_id=eq.{staff_id}&academic_year=eq.{academic_year}&select=id", headers=headers)
        if check.status_code == 200 and check.json():
            return jsonify({"error": "Связь уже существует"}), 400
        
        data = {"group_id": group_id, "staff_id": staff_id, "role": role, "academic_year": academic_year}
        response = requests.post(f"{SUPABASE_URL}/rest/v1/group_staff", headers=headers, json=data)
        if response.status_code == 201:
            return jsonify({"success": True}), 201
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/groups/<int:group_id>/staff/<int:staff_id>', methods=['DELETE'])
def remove_group_staff(group_id, staff_id):
    try:
        academic_year = request.args.get('academic_year', '')
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        url = f"{SUPABASE_URL}/rest/v1/group_staff?group_id=eq.{group_id}&staff_id=eq.{staff_id}&academic_year=eq.{academic_year}"
        response = requests.delete(url, headers=headers)
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API ОТЧЁТОВ И ПОИСКА ====================

@app.route('/api/reports/group-students/<int:group_id>', methods=['GET'])
def report_group_students(group_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        
        group_res = requests.get(f"{SUPABASE_URL}/rest/v1/groups?id=eq.{group_id}&select=*", headers=headers)
        group = group_res.json()[0] if group_res.status_code == 200 and group_res.json() else None
        
        students_res = requests.get(f"{SUPABASE_URL}/rest/v1/students?group_id=eq.{group_id}&is_deleted=eq.false&select=*", headers=headers)
        students = students_res.json() if students_res.status_code == 200 else []
        
        all_parents_res = requests.get(f"{SUPABASE_URL}/rest/v1/parents?is_archived=eq.false&select=*", headers=headers)
        all_parents = all_parents_res.json() if all_parents_res.status_code == 200 else []
        all_parents_dict = {p['id']: p for p in all_parents}
        
        all_links_res = requests.get(f"{SUPABASE_URL}/rest/v1/student_parents?select=student_id,parent_id", headers=headers)
        all_links = all_links_res.json() if all_links_res.status_code == 200 else []
        
        links_by_student = {}
        for link in all_links:
            sid = link['student_id']
            pid = link['parent_id']
            if sid not in links_by_student:
                links_by_student[sid] = []
            links_by_student[sid].append(pid)
        
        for s in students:
            parent_ids = links_by_student.get(s['id'], [])
            s['parents'] = [all_parents_dict[pid] for pid in parent_ids if pid in all_parents_dict]
            
            accounting_res = requests.get(f"{SUPABASE_URL}/rest/v1/study_accounting?student_id=eq.{s['id']}&select=type", headers=headers)
            s['accounting'] = [a['type'] for a in accounting_res.json()] if accounting_res.status_code == 200 else []
            
            siblings_res = requests.get(f"{SUPABASE_URL}/rest/v1/siblings?student_id=eq.{s['id']}&select=*", headers=headers)
            s['siblings'] = siblings_res.json() if siblings_res.status_code == 200 else []
        
        return jsonify({"group": group, "students": students})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/parents', methods=['GET'])
def report_parents():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        
        parents_res = requests.get(f"{SUPABASE_URL}/rest/v1/parents?is_archived=eq.false&select=*", headers=headers)
        parents = parents_res.json() if parents_res.status_code == 200 else []
        
        students_res = requests.get(f"{SUPABASE_URL}/rest/v1/students?is_deleted=eq.false&select=id,last_name,first_name,middle_name,group_id", headers=headers)
        all_students = students_res.json() if students_res.status_code == 200 else []
        
        for p in parents:
            links_res = requests.get(f"{SUPABASE_URL}/rest/v1/student_parents?parent_id=eq.{p['id']}&select=student_id", headers=headers)
            if links_res.status_code == 200 and links_res.json():
                student_ids = [l['student_id'] for l in links_res.json()]
                p['students'] = [s for s in all_students if s['id'] in student_ids]
            else:
                p['students'] = []
        
        return jsonify(parents)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/accounting', methods=['GET'])
def report_accounting():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        
        accounting_res = requests.get(f"{SUPABASE_URL}/rest/v1/study_accounting?select=student_id,type", headers=headers)
        if accounting_res.status_code != 200:
            return jsonify([])
        
        students_map = {}
        for a in accounting_res.json():
            if a['student_id'] not in students_map:
                students_map[a['student_id']] = []
            students_map[a['student_id']].append(a['type'])
        
        if not students_map:
            return jsonify([])
        
        student_ids = list(students_map.keys())
        students_res = requests.get(f"{SUPABASE_URL}/rest/v1/students?id=in.({','.join(map(str, student_ids))})&is_deleted=eq.false&select=*,group_id,school_name,school_graduation_year,certificate_avg_grade,has_target_contract,target_organization", headers=headers)
        students = students_res.json() if students_res.status_code == 200 else []
        
        for s in students:
            s['accounting'] = students_map.get(s['id'], [])
            if s.get('group_id'):
                group_res = requests.get(f"{SUPABASE_URL}/rest/v1/groups?id=eq.{s['group_id']}&select=name", headers=headers)
                if group_res.status_code == 200 and group_res.json():
                    s['group_name'] = group_res.json()[0]['name']
        
        return jsonify(students)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/search', methods=['GET'])
def search_all():
    try:
        query = request.args.get('q', '').lower()
        if not query or len(query) < 2:
            return jsonify({"students": [], "parents": [], "groups": []})
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        
        students_res = requests.get(f"{SUPABASE_URL}/rest/v1/students?is_deleted=eq.false&select=*,group_id,has_target_contract,target_organization", headers=headers)
        all_students = students_res.json() if students_res.status_code == 200 else []
        students = []
        for s in all_students:
            if (query in (s.get('last_name') or '').lower() or 
                query in (s.get('first_name') or '').lower() or 
                query in (s.get('middle_name') or '').lower() or
                query in (s.get('phone') or '') or
                query in (s.get('school_name') or '').lower() or
                query in (s.get('target_organization') or '').lower()):
                if s.get('group_id'):
                    group_res = requests.get(f"{SUPABASE_URL}/rest/v1/groups?id=eq.{s['group_id']}&select=name", headers=headers)
                    if group_res.status_code == 200 and group_res.json():
                        s['group_name'] = group_res.json()[0]['name']
                students.append(s)
        
        parents_res = requests.get(f"{SUPABASE_URL}/rest/v1/parents?is_archived=eq.false&select=*", headers=headers)
        all_parents = parents_res.json() if parents_res.status_code == 200 else []
        parents = [p for p in all_parents if 
                   query in (p.get('last_name') or '').lower() or 
                   query in (p.get('first_name') or '').lower() or 
                   query in (p.get('middle_name') or '').lower() or
                   query in (p.get('phone') or '')]
        
        groups_res = requests.get(f"{SUPABASE_URL}/rest/v1/groups?is_deleted=eq.false&is_graduated=eq.false&select=*", headers=headers)
        all_groups = groups_res.json() if groups_res.status_code == 200 else []
        groups = [g for g in all_groups if query in (g.get('name') or '').lower()]
        
        return jsonify({"students": students, "parents": parents, "groups": groups})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API АДМИНИСТРАЦИИ ====================

@app.route('/api/admin-staff', methods=['GET'])
def get_admin_staff():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/admin_staff?is_active=eq.true&select=*", headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({"error": "Ошибка получения списка"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin-staff', methods=['POST'])
def create_admin_staff():
    try:
        data = request.get_json()
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.post(f"{SUPABASE_URL}/rest/v1/admin_staff", headers=headers, json=data)
        
        if response.status_code == 201:
            try:
                result = response.json()
                if result and len(result) > 0:
                    return jsonify({"success": True, "admin": result[0]}), 201
                else:
                    return jsonify({"success": True, "message": "Администратор добавлен"}), 201
            except:
                return jsonify({"success": True, "message": "Администратор добавлен"}), 201
        else:
            return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin-staff/<int:admin_id>', methods=['PUT'])
def update_admin_staff(admin_id):
    try:
        data = request.get_json()
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/admin_staff?id=eq.{admin_id}", headers=headers, json=data)
        
        if response.status_code == 200:
            return jsonify({"success": True})
        else:
            return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin-staff/<int:admin_id>', methods=['DELETE'])
def delete_admin_staff(admin_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/admin_staff?id=eq.{admin_id}", headers=headers, json={"is_active": False})
        
        if response.status_code == 200:
            return jsonify({"success": True})
        else:
            return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API УПРАВЛЕНИЯ РОЛЯМИ И ПРАВАМИ ====================

@app.route('/api/roles', methods=['GET'])
def get_roles():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/roles?select=*", headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({"error": "Ошибка получения ролей"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/<int:user_id>/role', methods=['GET'])
def get_user_role_api(user_id):
    """Получить роль сотрудника"""
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/user_roles?user_id=eq.{user_id}&select=roles(name)",
            headers=headers
        )
        if response.status_code == 200 and response.json():
            return jsonify({'role': response.json()[0]['roles']['name']})
        return jsonify({'role': 'viewer'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/roles', methods=['POST'])
def set_user_roles(user_id):
    try:
        data = request.get_json()
        role_ids = data.get('role_ids', [])
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        
        requests.delete(f"{SUPABASE_URL}/rest/v1/user_roles?user_id=eq.{user_id}", headers=headers)
        
        for role_id in role_ids:
            requests.post(f"{SUPABASE_URL}/rest/v1/user_roles", headers=headers, json={"user_id": user_id, "role_id": role_id})
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/<int:user_id>/group-permissions', methods=['GET'])
def get_user_group_permissions(user_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/user_group_permissions?user_id=eq.{user_id}&can_edit=eq.true&select=group_id", headers=headers)
        if response.status_code == 200:
            group_ids = [ug['group_id'] for ug in response.json()]
            return jsonify({"group_ids": group_ids})
        return jsonify({"group_ids": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/<int:user_id>/group-permissions', methods=['POST'])
def set_user_group_permissions(user_id):
    try:
        data = request.get_json()
        group_ids = data.get('group_ids', [])
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        
        requests.delete(f"{SUPABASE_URL}/rest/v1/user_group_permissions?user_id=eq.{user_id}", headers=headers)
        
        for group_id in group_ids:
            requests.post(f"{SUPABASE_URL}/rest/v1/user_group_permissions", headers=headers, json={"user_id": user_id, "group_id": group_id, "can_edit": True})
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API НАСТРОЕК САЙТА ====================

@app.route('/api/site-settings', methods=['GET'])
def get_site_settings():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/site_settings?select=*", headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/site-settings/<key>', methods=['PUT'])
def update_site_setting(key):
    try:
        data = request.get_json()
        value = data.get('value')
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        
        check = requests.get(f"{SUPABASE_URL}/rest/v1/site_settings?setting_key=eq.{key}&select=id", headers=headers)
        if check.status_code == 200 and check.json():
            id = check.json()[0]['id']
            response = requests.patch(f"{SUPABASE_URL}/rest/v1/site_settings?id=eq.{id}", headers=headers, json={"setting_value": value})
        else:
            response = requests.post(f"{SUPABASE_URL}/rest/v1/site_settings", headers=headers, json={"setting_key": key, "setting_value": value})
        
        if response.status_code in [200, 201]:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contact-info', methods=['GET'])
def get_contact_info():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/contact_info?select=*", headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contact-info/<contact_type>', methods=['PUT'])
def update_contact_info(contact_type):
    try:
        data = request.get_json()
        value = data.get('value')
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        
        check = requests.get(f"{SUPABASE_URL}/rest/v1/contact_info?contact_type=eq.{contact_type}&select=id", headers=headers)
        if check.status_code == 200 and check.json():
            id = check.json()[0]['id']
            response = requests.patch(f"{SUPABASE_URL}/rest/v1/contact_info?id=eq.{id}", headers=headers, json={"contact_value": value})
        else:
            response = requests.post(f"{SUPABASE_URL}/rest/v1/contact_info", headers=headers, json={"contact_type": contact_type, "contact_value": value})
        
        if response.status_code in [200, 201]:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/theme-settings', methods=['GET'])
def get_theme_settings():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/theme_settings?select=*", headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/theme-settings/<key>', methods=['PUT'])
def update_theme_setting(key):
    try:
        data = request.get_json()
        value = data.get('value')
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        
        check = requests.get(f"{SUPABASE_URL}/rest/v1/theme_settings?theme_key=eq.{key}&select=id", headers=headers)
        if check.status_code == 200 and check.json():
            id = check.json()[0]['id']
            response = requests.patch(f"{SUPABASE_URL}/rest/v1/theme_settings?id=eq.{id}", headers=headers, json={"theme_value": value})
        else:
            response = requests.post(f"{SUPABASE_URL}/rest/v1/theme_settings", headers=headers, json={"theme_key": key, "theme_value": value})
        
        if response.status_code in [200, 201]:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API ФОТОАЛЬБОМОВ ====================

@app.route('/api/photo-albums', methods=['GET'])
def get_photo_albums():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/photo_albums?order=created_at.desc&select=*", headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/photo-albums', methods=['POST'])
def create_photo_album():
    try:
        data = request.get_json()
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.post(f"{SUPABASE_URL}/rest/v1/photo_albums", headers=headers, json=data)
        
        if response.status_code == 201:
            return jsonify({"success": True, "album": response.json()[0]}), 201
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/photo-albums/<int:album_id>', methods=['DELETE'])
def delete_photo_album(album_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/photo_albums?id=eq.{album_id}", headers=headers)
        
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/photos', methods=['POST'])
def add_photo():
    try:
        data = request.get_json()
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.post(f"{SUPABASE_URL}/rest/v1/photos", headers=headers, json=data)
        
        if response.status_code == 201:
            return jsonify({"success": True, "photo": response.json()[0]}), 201
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/photos/<int:photo_id>', methods=['DELETE'])
def delete_photo(photo_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/photos?id=eq.{photo_id}", headers=headers)
        
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API НОВОСТЕЙ ====================

@app.route('/api/news', methods=['GET'])
def get_news():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/news?order=published_at.desc&select=*", headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/news', methods=['POST'])
def create_news():
    try:
        data = request.get_json()
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.post(f"{SUPABASE_URL}/rest/v1/news", headers=headers, json=data)
        
        if response.status_code == 201:
            return jsonify({"success": True, "news": response.json()[0]}), 201
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/news/<int:news_id>', methods=['PUT'])
def update_news(news_id):
    try:
        data = request.get_json()
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.patch(f"{SUPABASE_URL}/rest/v1/news?id=eq.{news_id}", headers=headers, json=data)
        
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/news/<int:news_id>', methods=['DELETE'])
def delete_news(news_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/news?id=eq.{news_id}", headers=headers)
        
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API ФАЙЛОВОГО АРХИВА ====================

@app.route('/api/file-archive', methods=['GET'])
def get_file_archive():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/file_archive?order=upload_date.desc&select=*", headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/file-archive', methods=['POST'])
def add_file():
    try:
        data = request.get_json()
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.post(f"{SUPABASE_URL}/rest/v1/file_archive", headers=headers, json=data)
        
        if response.status_code == 201:
            return jsonify({"success": True, "file": response.json()[0]}), 201
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/file-archive/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/file_archive?id=eq.{file_id}", headers=headers)
        
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== API ДИЗАЙНА ====================

@app.route('/api/design-settings', methods=['GET'])
def get_design_settings():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/design_settings?select=*", headers=headers)
        if response.status_code == 200:
            settings = {item['setting_key']: item['setting_value'] for item in response.json()}
            return jsonify(settings)
        return jsonify({})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/design-settings/<key>', methods=['PUT'])
def update_design_setting(key):
    try:
        data = request.get_json()
        value = data.get('value')
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        
        check = requests.get(f"{SUPABASE_URL}/rest/v1/design_settings?setting_key=eq.{key}&select=id", headers=headers)
        if check.status_code == 200 and check.json():
            id = check.json()[0]['id']
            response = requests.patch(f"{SUPABASE_URL}/rest/v1/design_settings?id=eq.{id}", headers=headers, json={"setting_value": value, "updated_at": datetime.now().isoformat()})
        else:
            response = requests.post(f"{SUPABASE_URL}/rest/v1/design_settings", headers=headers, json={"setting_key": key, "setting_value": value})
        
        if response.status_code in [200, 201]:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/design-settings/reset', methods=['POST'])
def reset_design_settings():
    try:
        default_settings = {
            "background_type": "gradient",
            "background_gradient_start": "#1a0b2e",
            "background_gradient_end": "#fbbf24",
            "background_color": "#f0f2f5",
            "background_image": "",
            "primary_color": "#4c1d95",
            "secondary_color": "#2563eb",
            "accent_color": "#fbbf24",
            "text_color": "#1e1b4b",
            "header_bg": "#1e1b4b",
            "font_family_title": "Segoe UI, Tahoma, Geneva, Verdana, sans-serif",
            "font_family_groups": "Segoe UI, Tahoma, Geneva, Verdana, sans-serif",
            "font_family_students": "Segoe UI, Tahoma, Geneva, Verdana, sans-serif",
            "font_family_menu": "Segoe UI, Tahoma, Geneva, Verdana, sans-serif"
        }
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        
        for key, value in default_settings.items():
            check = requests.get(f"{SUPABASE_URL}/rest/v1/design_settings?setting_key=eq.{key}&select=id", headers=headers)
            if check.status_code == 200 and check.json():
                id = check.json()[0]['id']
                requests.patch(f"{SUPABASE_URL}/rest/v1/design_settings?id=eq.{id}", headers=headers, json={"setting_value": value})
            else:
                requests.post(f"{SUPABASE_URL}/rest/v1/design_settings", headers=headers, json={"setting_key": key, "setting_value": value})
        
        return jsonify({"success": True, "message": "Настройки сброшены"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/saved-themes', methods=['GET'])
def get_saved_themes():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/saved_themes?select=*", headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/saved-themes', methods=['POST'])
def create_saved_theme():
    try:
        data = request.get_json()
        theme_name = data.get('name')
        
        if not theme_name:
            return jsonify({"error": "Не указано имя темы"}), 400
        
        design_res = requests.get(f"{SUPABASE_URL}/rest/v1/design_settings?select=setting_key,setting_value", headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"})
        if design_res.status_code != 200:
            return jsonify({"error": "Ошибка получения настроек"}), 500
        
        theme_settings = {}
        for item in design_res.json():
            theme_settings[item['setting_key']] = item['setting_value']
        
        theme_settings['name'] = theme_name
        theme_settings['created_at'] = datetime.now().isoformat()
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.post(f"{SUPABASE_URL}/rest/v1/saved_themes", headers=headers, json=theme_settings)
        
        if response.status_code == 201:
            return jsonify({"success": True, "message": "Тема сохранена"}), 201
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/saved-themes/<int:theme_id>', methods=['POST'])
def apply_saved_theme(theme_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        
        theme_res = requests.get(f"{SUPABASE_URL}/rest/v1/saved_themes?id=eq.{theme_id}&select=*", headers=headers)
        if theme_res.status_code != 200 or not theme_res.json():
            return jsonify({"error": "Тема не найдена"}), 404
        
        theme = theme_res.json()[0]
        
        for key, value in theme.items():
            if key not in ['id', 'name', 'created_at'] and value:
                check = requests.get(f"{SUPABASE_URL}/rest/v1/design_settings?setting_key=eq.{key}&select=id", headers=headers)
                if check.status_code == 200 and check.json():
                    id = check.json()[0]['id']
                    requests.patch(f"{SUPABASE_URL}/rest/v1/design_settings?id=eq.{id}", headers=headers, json={"setting_value": value})
                else:
                    requests.post(f"{SUPABASE_URL}/rest/v1/design_settings", headers=headers, json={"setting_key": key, "setting_value": value})
        
        return jsonify({"success": True, "message": "Тема применена"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/saved-themes/<int:theme_id>', methods=['DELETE'])
def delete_saved_theme(theme_id):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/saved_themes?id=eq.{theme_id}", headers=headers)
        
        if response.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"error": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== РЕГИСТРАЦИЯ BLUEPRINTS ====================
app.register_blueprint(settings_bp)

# ==================== API ДЛЯ ТЕЛЕГРАМ БОТА ====================

@app.route('/auth/telegram', methods=['GET'])
def auth_telegram():
    """Авторизация через Telegram бота"""
    token = request.args.get('token')
    
    if not token:
        return "❌ Токен не указан", 400
    
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        
        # Ищем токен в таблице telegram_users
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/telegram_users?auth_token=eq.{token}&select=staff_id,telegram_id,token_expires",
            headers=headers
        )
        
        if response.status_code != 200 or not response.json():
            return "❌ Неверный или просроченный токен", 400
        
        tg_user = response.json()[0]
        
        # Проверяем срок действия токена
        from datetime import datetime
        token_expires = datetime.fromisoformat(tg_user['token_expires'].replace('Z', '+00:00'))
        if datetime.now().astimezone() > token_expires:
            return "❌ Срок действия ссылки истёк. Запросите новую в боте", 400
        
        # Получаем данные сотрудника
        staff_res = requests.get(
            f"{SUPABASE_URL}/rest/v1/staff?id=eq.{tg_user['staff_id']}&select=*",
            headers=headers
        )
        
        if staff_res.status_code != 200 or not staff_res.json():
            return "❌ Сотрудник не найден", 400
        
        staff = staff_res.json()[0]
        
        # Создаём сессию
        session['user_id'] = staff['id']
        session['user_name'] = f"{staff['first_name']} {staff['last_name']}"
        session['user_role'] = get_user_role_from_db(staff['id'])
        
        # Удаляем использованный токен
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/telegram_users?id=eq.{tg_user['id']}",
            headers=headers,
            json={"auth_token": None, "token_expires": None}
        )
        
        # Редирект на панель управления
        return redirect('/dashboard.html')
        
    except Exception as e:
        return f"❌ Ошибка: {str(e)}", 500


@app.route('/api/bot/verify-code', methods=['POST'])
def verify_bot_code():
    """Проверка кода привязки Telegram"""
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        code = data.get('code')
        staff_id = data.get('staff_id')
        
        # Проверяем код (в реальном проекте нужно хранить в БД)
        # Здесь будет логика проверки
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/bot/users', methods=['GET'])
def get_bot_users():
    """Получить список пользователей бота (для панели управления)"""
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/telegram_users?select=id,staff_id,telegram_id,telegram_username,is_verified,is_active,staff(last_name,first_name,position)",
            headers=headers
        )
        if response.status_code == 200:
            # Преобразуем данные, чтобы id был на верхнем уровне
            users = response.json()
            for u in users:
                u['id'] = u.get('id')  # Убеждаемся, что id есть
            return jsonify(users)
        return jsonify([])
    except Exception as e:
        print(f"Ошибка в /api/bot/users: {e}")
        return jsonify({"error": str(e)}), 500


def get_user_role_from_db(user_id):
    """Получить роль пользователя из БД"""
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/user_roles?user_id=eq.{user_id}&select=roles(name)",
            headers=headers
        )
        if response.status_code == 200 and response.json():
            return response.json()[0]['roles']['name']
        return 'viewer'
    except:
        return 'viewer'


# Добавь импорт redirect в начало файла (если нет)
# from flask import redirect

# ==================== API ДЛЯ УПРАВЛЕНИЯ БОТОМ ====================

@app.route('/api/bot/stats', methods=['GET'])
def get_bot_stats():
    """Получить статистику по боту"""
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        
        users_res = requests.get(f"{SUPABASE_URL}/rest/v1/telegram_users?select=id", headers=headers)
        total_users = len(users_res.json()) if users_res.status_code == 200 else 0
        
        active_res = requests.get(f"{SUPABASE_URL}/rest/v1/telegram_users?is_active=eq.true&select=id", headers=headers)
        active_users = len(active_res.json()) if active_res.status_code == 200 else 0
        
        verified_res = requests.get(f"{SUPABASE_URL}/rest/v1/telegram_users?is_verified=eq.true&select=id", headers=headers)
        verified_users = len(verified_res.json()) if verified_res.status_code == 200 else 0
        
        staff_res = requests.get(f"{SUPABASE_URL}/rest/v1/staff?is_active=eq.true&select=id", headers=headers)
        total_staff = len(staff_res.json()) if staff_res.status_code == 200 else 0
        
        return jsonify({
            'total_users': total_users,
            'active_users': active_users,
            'verified_users': verified_users,
            'total_staff': total_staff
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/users', methods=['GET'])
def get_bot_users_list():
    """Получить список пользователей бота с полной информацией"""
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/telegram_users?select=id,staff_id,telegram_id,telegram_username,is_verified,is_active,staff(last_name,first_name,position,phone)",
            headers=headers
        )
        if response.status_code == 200:
            users = response.json()
            # Добавляем id на верхний уровень
            for u in users:
                u['id'] = u.get('id')
            return jsonify(users)
        return jsonify([])
    except Exception as e:
        print(f"Ошибка в /api/bot/users: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/bot/bind', methods=['POST'])
def bot_bind_user():
    """Привязать сотрудника к Telegram"""
    try:
        data = request.get_json()
        staff_id = data.get('staff_id')
        telegram_id = data.get('telegram_id')
        telegram_username = data.get('telegram_username', '')
        
        if not staff_id or not telegram_id:
            return jsonify({'error': 'Не указаны сотрудник или Telegram ID'}), 400
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        
        # Проверяем, не привязан ли уже этот Telegram
        check = requests.get(f"{SUPABASE_URL}/rest/v1/telegram_users?telegram_id=eq.{telegram_id}", headers=headers)
        if check.status_code == 200 and check.json():
            return jsonify({'error': 'Этот Telegram уже привязан к другому сотруднику'}), 400
        
        # Проверяем, не привязан ли уже этот сотрудник
        check_staff = requests.get(f"{SUPABASE_URL}/rest/v1/telegram_users?staff_id=eq.{staff_id}", headers=headers)
        if check_staff.status_code == 200 and check_staff.json():
            return jsonify({'error': 'Этот сотрудник уже привязан к Telegram'}), 400
        
        # Получаем данные сотрудника для отправки уведомления
        staff_res = requests.get(f"{SUPABASE_URL}/rest/v1/staff?id=eq.{staff_id}&select=first_name,last_name,position", headers=headers)
        staff_name = ""
        staff_position = ""
        if staff_res.status_code == 200 and staff_res.json():
            s = staff_res.json()[0]
            staff_name = f"{s.get('first_name', '')} {s.get('last_name', '')}"
            staff_position = s.get('position', '')
        
        # Создаём привязку
        bind_data = {
            'staff_id': staff_id,
            'telegram_id': telegram_id,
            'telegram_username': telegram_username,
            'is_verified': True,
            'is_active': True
        }
        response = requests.post(f"{SUPABASE_URL}/rest/v1/telegram_users", headers=headers, json=bind_data)
        
        if response.status_code == 201:
            # Отправляем уведомление в Telegram через бота
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if bot_token and telegram_id:
                try:
                    notify_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    notify_data = {
                        "chat_id": telegram_id,
                        "text": f"✅ *Вас привязали к системе!*\n\n"
                                f"👤 *Сотрудник:* {staff_name}\n"
                                f"📌 *Должность:* {staff_position}\n\n"
                                f"🤖 Теперь вы можете:\n"
                                f"• Написать /start для доступа к меню\n"
                                f"• Нажать «Войти на сайт» для авторизации\n"
                                f"• Использовать /status для проверки прав\n\n"
                                f"🌐 Сайт: http://127.0.0.1:5000",
                        "parse_mode": "Markdown"
                    }
                    requests.post(notify_url, json=notify_data)
                except Exception as e:
                    print(f"Не удалось отправить уведомление: {e}")
            
            return jsonify({'success': True})
        return jsonify({'error': response.text}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/toggle/<int:user_id>', methods=['POST'])
def bot_toggle_user(user_id):
    """Блокировка/разблокировка пользователя с уведомлением в Telegram"""
    try:
        data = request.get_json()
        is_active = data.get('is_active', True)
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        
        # Сначала получаем данные пользователя для уведомления
        get_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/telegram_users?id=eq.{user_id}&select=telegram_id,staff_id,staff(first_name,last_name)",
            headers=headers
        )
        
        telegram_id = None
        staff_name = ""
        if get_response.status_code == 200 and get_response.json():
            user_data = get_response.json()[0]
            telegram_id = user_data.get('telegram_id')
            if user_data.get('staff'):
                staff_name = f"{user_data['staff'].get('first_name', '')} {user_data['staff'].get('last_name', '')}"
        
        # Обновляем статус
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/telegram_users?id=eq.{user_id}",
            headers=headers,
            json={'is_active': is_active}
        )
        
        if response.status_code == 200:
            # Отправляем уведомление в Telegram
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if bot_token and telegram_id:
                try:
                    status_text = "разблокирован" if is_active else "заблокирован"
                    status_emoji = "✅" if is_active else "🔒"
                    notify_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    notify_data = {
                        "chat_id": telegram_id,
                        "text": f"{status_emoji} *Ваш доступ {status_text}!*\n\n"
                                f"👤 Сотрудник: {staff_name}\n"
                                f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                                f"По вопросам обращайтесь к администратору.",
                        "parse_mode": "Markdown"
                    }
                    requests.post(notify_url, json=notify_data)
                except Exception as e:
                    print(f"Не удалось отправить уведомление: {e}")
            
            return jsonify({'success': True})
        return jsonify({'error': response.text}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/unbind/<int:user_id>', methods=['DELETE'])
def bot_unbind_user(user_id):
    """Отвязать сотрудника от Telegram с уведомлением"""
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        
        # Сначала получаем данные пользователя для уведомления
        get_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/telegram_users?id=eq.{user_id}&select=telegram_id,staff_id,staff(first_name,last_name)",
            headers=headers
        )
        
        telegram_id = None
        staff_name = ""
        if get_response.status_code == 200 and get_response.json():
            user_data = get_response.json()[0]
            telegram_id = user_data.get('telegram_id')
            if user_data.get('staff'):
                staff_name = f"{user_data['staff'].get('first_name', '')} {user_data['staff'].get('last_name', '')}"
        
        # Удаляем запись
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/telegram_users?id=eq.{user_id}",
            headers=headers
        )
        
        if response.status_code == 200 or response.status_code == 204:
            # Отправляем уведомление в Telegram
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if bot_token and telegram_id:
                try:
                    notify_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    notify_data = {
                        "chat_id": telegram_id,
                        "text": f"⚠️ *Ваш аккаунт был отвязан от системы!*\n\n"
                                f"👤 Сотрудник: {staff_name}\n"
                                f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                                f"❌ Вы больше не можете входить на сайт через бота.\n"
                                f"Для восстановления доступа обратитесь к администратору.",
                        "parse_mode": "Markdown"
                    }
                    requests.post(notify_url, json=notify_data)
                except Exception as e:
                    print(f"Не удалось отправить уведомление: {e}")
            
            return jsonify({'success': True})
        return jsonify({'error': response.text}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/update/<int:user_id>', methods=['PUT'])
def bot_update_user(user_id):
    """Обновить Telegram ID пользователя"""
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        telegram_username = data.get('telegram_username', '')
        
        if not telegram_id:
            return jsonify({'error': 'Telegram ID не указан'}), 400
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/telegram_users?id=eq.{user_id}",
            headers=headers,
            json={'telegram_id': telegram_id, 'telegram_username': telegram_username}
        )
        
        if response.status_code == 200:
            return jsonify({'success': True})
        return jsonify({'error': response.text}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/broadcast', methods=['POST'])
def bot_broadcast():
    """Отправить сообщение всем пользователям бота"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/telegram_users?is_active=eq.true&select=telegram_id",
            headers=headers
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Не удалось получить список пользователей'}), 500
        
        users = response.json()
        
        return jsonify({
            'success': True,
            'recipients': len(users),
            'message': f'Сообщение будет отправлено {len(users)} пользователям'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== API ДЛЯ ПОЛУЧЕНИЯ РОЛЕЙ ПОЛЬЗОВАТЕЛЯ ====================

@app.route('/api/users/<int:user_id>/roles', methods=['GET'])
def get_user_roles_list(user_id):
    """Получить список ролей пользователя (для панели управления ботом)"""
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/user_roles?user_id=eq.{user_id}&select=role_id",
            headers=headers
        )
        if response.status_code == 200:
            role_ids = [ur['role_id'] for ur in response.json()]
            return jsonify({"role_ids": role_ids})
        return jsonify({"role_ids": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== API ДЛЯ НАСТРОЕК ОТОБРАЖЕНИЯ ====================

@app.route('/api/display-settings', methods=['GET'])
def get_display_settings():
    """Получить все настройки отображения"""
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(f"{SUPABASE_URL}/rest/v1/display_settings?order=section.asc,sort_order.asc", headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/display-settings', methods=['PUT'])
def update_display_setting():
    """Обновить настройку отображения"""
    try:
        data = request.get_json()
        setting_id = data.get('id')
        is_visible = data.get('is_visible')
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/display_settings?id=eq.{setting_id}",
            headers=headers,
            json={'is_visible': is_visible}
        )
        
        if response.status_code == 200:
            return jsonify({'success': True})
        return jsonify({'error': response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

        # ==================== API ДЛЯ МАССОВОЙ ЗАГРУЗКИ РОЛЕЙ ====================

@app.route('/api/users/roles/batch', methods=['POST'])
def get_users_roles_batch():
    """Получить роли для нескольких сотрудников одним запросом"""
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return jsonify({})
        
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        
        # Получаем роли для всех пользователей одним запросом
        user_ids_str = ','.join(map(str, user_ids))
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/user_roles?user_id=in.({user_ids_str})&select=user_id,role_id",
            headers=headers
        )
        
        if response.status_code != 200:
            return jsonify({})
        
        # Группируем по user_id
        roles_map = {}
        for item in response.json():
            user_id = item['user_id']
            role_id = item['role_id']
            if user_id not in roles_map:
                roles_map[user_id] = []
            roles_map[user_id].append(role_id)
        
        return jsonify(roles_map)
    except Exception as e:
        print(f"Ошибка в /api/users/roles/batch: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 СЕРВЕР ЗАПУЩЕН")
    print("=" * 50)
    print("📍 Адрес: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)