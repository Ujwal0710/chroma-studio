import requests
import json
import time

BASE = 'http://127.0.0.1:8000'
results = {}
details = {}

try:
    # 1. Health & Sample
    r = requests.get(f'{BASE}/health')
    results['health'] = r.status_code == 200
    details['health'] = {'status': r.status_code}

    r_sample = requests.get(f'{BASE}/rooms/sample')
    results['sample'] = r_sample.status_code == 200
    details['sample'] = {'status': r_sample.status_code}
    img_b64 = r_sample.json().get('image_data', '')

    # 2. Rooms Analyse
    r_analyse = requests.post(f'{BASE}/rooms/analyse', json={'image_data': img_b64, 'room_type': 'Living Room'})
    results['analyse'] = r_analyse.status_code == 200
    details['analyse'] = {'status': r_analyse.status_code}
    analysis_data = r_analyse.json()

    # 3. Wall Segment & Recolour
    r_seg = requests.post(f'{BASE}/rooms/segment', json={'image_data': img_b64, 'sensitivity': 0.5})
    results['wall_segment'] = r_seg.status_code == 200
    details['wall_segment'] = {'status': r_seg.status_code}

    r_recolour = requests.post(f'{BASE}/rooms/recolour', json={'image_data': img_b64, 'target_hex': '#3B82F6', 'intensity': 0.8})
    results['wall_recolour'] = r_recolour.status_code == 200
    details['wall_recolour'] = {'status': r_recolour.status_code}

    # 4. Palettes Generate & Swap
    r_pal = requests.post(f'{BASE}/palettes/generate', json={
        'extracted': analysis_data.get('extracted', {'dominant_tones': [{'hex': '#CCCCCC', 'percentage': 50, 'name': 'Grey'}]}),
        'preferences': {'style': 'Modern Minimalist', 'primary_emotion': 'Calm'}
    })
    results['palettes_generate'] = r_pal.status_code == 200
    details['palettes_generate'] = {'status': r_pal.status_code}

    r_swap = requests.post(f'{BASE}/palettes/swap', json={
        'original_hex': '#FFFFFF',
        'replacement_hex': '#10B981',
        'surface': 'walls',
        'image_data': img_b64
    })
    results['palettes_swap'] = r_swap.status_code == 200
    details['palettes_swap'] = {'status': r_swap.status_code}

    # 5. Daylight Simulate
    r_day = requests.post(f'{BASE}/daylight/simulate', json={'image_data': img_b64, 'condition': 'noon_5500k'})
    results['daylight'] = r_day.status_code == 200
    details['daylight'] = {'status': r_day.status_code}

    # 6. Materials Score
    r_mat = requests.post(f'{BASE}/materials/score', json={'palette_hexes': ['#3B82F6', '#E2E8F0'], 'material_types': ['oak_wood', 'matte_metal']})
    results['materials'] = r_mat.status_code == 200
    details['materials'] = {'status': r_mat.status_code}

    # 7. Estimator
    r_est = requests.post(f'{BASE}/estimator/calculate', json={'room_dimensions': {'length_ft': 14, 'width_ft': 12, 'height_ft': 9}, 'selected_paint_tier': 'premium_emulsion'})
    results['estimator'] = r_est.status_code == 200
    details['estimator'] = {'status': r_est.status_code}

    # 8. Timeline & Rollback
    r_time_post = requests.post(f'{BASE}/timeline', json={'project_id': 'proj_test', 'label': 'Test Version', 'state_data': {'hex': '#3B82F6'}})
    results['timeline_post'] = r_time_post.status_code == 200
    details['timeline_post'] = {'status': r_time_post.status_code}
    version_id = r_time_post.json().get('version_id') if r_time_post.status_code == 200 else '1'
    r_time_get = requests.get(f'{BASE}/timeline?project_id=proj_test')
    results['timeline_get'] = r_time_get.status_code == 200
    details['timeline_get'] = {'status': r_time_get.status_code}
    r_time_roll = requests.post(f'{BASE}/timeline/rollback', json={'project_id': 'proj_test', 'version_id': version_id})
    results['timeline_rollback'] = r_time_roll.status_code == 200
    details['timeline_rollback'] = {'status': r_time_roll.status_code}

    # 9. Memory & DNA
    r_mem = requests.post(f'{BASE}/memory/action', json={'action': 'favourite', 'hex_code': '#3B82F6', 'palette_id': 'p1'})
    results['memory_action'] = r_mem.status_code == 200
    details['memory_action'] = {'status': r_mem.status_code}
    r_dna = requests.get(f'{BASE}/dna')
    results['dna'] = r_dna.status_code == 200
    details['dna'] = {'status': r_dna.status_code}

    # 10. Auth
    test_user = f'audit_{int(time.time())}@test.com'
    r_reg = requests.post(f'{BASE}/auth/register', json={'email': test_user, 'password': 'SecurePassword123!', 'full_name': 'Audit User'})
    results['auth_register'] = r_reg.status_code == 200
    details['auth_register'] = {'status': r_reg.status_code}
    r_log = requests.post(f'{BASE}/auth/login', json={'email': test_user, 'password': 'SecurePassword123!'})
    results['auth_login'] = r_log.status_code == 200
    details['auth_login'] = {'status': r_log.status_code}
    token = r_log.json().get('token')
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    r_me = requests.get(f'{BASE}/auth/me', headers=headers)
    results['auth_me'] = r_me.status_code == 200
    details['auth_me'] = {'status': r_me.status_code}

    # 11. Billing
    r_plans = requests.get(f'{BASE}/plans')
    results['plans'] = r_plans.status_code == 200
    details['plans'] = {'status': r_plans.status_code}
    r_order = requests.post(f'{BASE}/billing/order', json={'plan_id': 'pro'})
    results['billing_order'] = r_order.status_code == 200
    details['billing_order'] = {'status': r_order.status_code}

    # 12. Exports
    r_exp_json = requests.get(f'{BASE}/export/json?project_id=proj_test')
    results['export_json'] = r_exp_json.status_code == 200
    details['export_json'] = {'status': r_exp_json.status_code}
    r_exp_csv = requests.get(f'{BASE}/export/csv?project_id=proj_test')
    results['export_csv'] = r_exp_csv.status_code == 200
    details['export_csv'] = {'status': r_exp_csv.status_code}
    r_exp_png = requests.get(f'{BASE}/export/png?project_id=proj_test')
    results['export_png'] = r_exp_png.status_code == 200
    details['export_png'] = {'status': r_exp_png.status_code}

except Exception as e:
    results['error'] = str(e)

print(json.dumps({'results': results, 'details': details}, indent=2))
