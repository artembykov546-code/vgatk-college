from flask import Blueprint, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

settings_bp = Blueprint('settings', __name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

# ==================== ПОЛУЧИТЬ ВСЕ НАСТРОЙКИ ====================
@settings_bp.route('/api/settings/all', methods=['GET'])
def get_all_settings():
    try:
        headers = get_headers()
        
        # Получаем настройки сайта
        site_response = requests.get(f"{SUPABASE_URL}/rest/v1/site_settings?select=*", headers=headers)
        site_settings = site_response.json() if site_response.status_code == 200 else []
        
        # Получаем контакты
        contacts_response = requests.get(f"{SUPABASE_URL}/rest/v1/contact_info?select=*", headers=headers)
        contact_info = contacts_response.json() if contacts_response.status_code == 200 else []
        
        # Получаем настройки дизайна
        design_response = requests.get(f"{SUPABASE_URL}/rest/v1/design_settings?select=*", headers=headers)
        design_settings = design_response.json() if design_response.status_code == 200 else []
        
        return jsonify({
            'site_settings': site_settings,
            'contact_info': contact_info,
            'design_settings': design_settings
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ОБНОВИТЬ НАСТРОЙКУ ====================
@settings_bp.route('/api/settings/update', methods=['POST'])
def update_setting():
    try:
        data = request.get_json()
        table = data.get('table')
        key = data.get('key')
        value = data.get('value')
        
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        
        if table == 'site_settings':
            check = requests.get(f"{SUPABASE_URL}/rest/v1/site_settings?setting_key=eq.{key}&select=id", headers=headers)
            if check.status_code == 200 and check.json():
                id = check.json()[0]['id']
                requests.patch(f"{SUPABASE_URL}/rest/v1/site_settings?id=eq.{id}", headers=headers, json={"setting_value": value})
            else:
                requests.post(f"{SUPABASE_URL}/rest/v1/site_settings", headers=headers, json={"setting_key": key, "setting_value": value})
                
        elif table == 'contact_info':
            check = requests.get(f"{SUPABASE_URL}/rest/v1/contact_info?contact_type=eq.{key}&select=id", headers=headers)
            if check.status_code == 200 and check.json():
                id = check.json()[0]['id']
                requests.patch(f"{SUPABASE_URL}/rest/v1/contact_info?id=eq.{id}", headers=headers, json={"contact_value": value})
            else:
                requests.post(f"{SUPABASE_URL}/rest/v1/contact_info", headers=headers, json={"contact_type": key, "contact_value": value})
                
        elif table == 'design_settings':
            check = requests.get(f"{SUPABASE_URL}/rest/v1/design_settings?setting_key=eq.{key}&select=id", headers=headers)
            if check.status_code == 200 and check.json():
                id = check.json()[0]['id']
                requests.patch(f"{SUPABASE_URL}/rest/v1/design_settings?id=eq.{id}", headers=headers, json={"setting_value": value})
            else:
                requests.post(f"{SUPABASE_URL}/rest/v1/design_settings", headers=headers, json={"setting_key": key, "setting_value": value})
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ЗАГРУЗИТЬ ЛОГОТИП ====================
@settings_bp.route('/api/upload/logo', methods=['POST'])
def upload_logo():
    try:
        # Пока заглушка, позже добавим загрузку файлов
        return jsonify({'success': True, 'message': 'Функция загрузки будет добавлена позже'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

print("✅ Настройки (settings_bp) загружены")