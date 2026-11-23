import requests
import json
import base64
import io
from PIL import Image

BASE = 'http://127.0.0.1:8000'

results = {}
details = {}

# Create a small dummy JPEG image in memory for testing multipart endpoints
img = Image.new('RGB', (400, 300), color=(200, 180, 160))
buf = io.BytesIO()
img.save(buf, format='JPEG')
image_bytes = buf.getvalue()

# 1. Health
try:
    r = requests.get(f'{BASE}/health')
    results['health'] = (r.status_code == 200)
    details['health'] = r.json()
except Exception as e:
    results['health'] = False
    details['health'] = str(e)

# 2. Rooms Analyse
try:
    r = requests.post(f'{BASE}/rooms/analyse', files={'file': ('room.jpg', image_bytes, 'image/jpeg')})
    results['rooms_analyse'] = (r.status_code == 200)
    details['rooms_analyse'] = {'status': r.status_code, 'room_type': r.json().get('room_analysis', {}).get('detected_room_type') if r.status_code == 200 else r.text}
    room_analysis_res = r.json() if r.status_code == 200 else {}
except Exception as e:
    results['rooms_analyse'] = False
    details['rooms_analyse'] = str(e)

# 3. Wall Segment & Recolour
try:
    r_seg = requests.post(f'{BASE}/rooms/segment', files={'file': ('room.jpg', image_bytes, 'image/jpeg')}, data={'sensitivity': 0.55})
    results['rooms_segment'] = (r_seg.status_code == 200)
    details['rooms_segment'] = {'status': r_seg.status_code, 'has_mask': 'mask_preview' in r_seg.json() or 'mask_overlay' in r_seg.json() if r_seg.status_code == 200 else False}

    r_rec = requests.post(f'{BASE}/rooms/recolour', files={'file': ('room.jpg', image_bytes, 'image/jpeg')}, data={'target_hex': '#3B82F6', 'intensity': 0.85})
    results['rooms_recolour'] = (r_rec.status_code == 200)
    details['rooms_recolour'] = {'status': r_rec.status_code, 'has_preview': 'image_preview' in r_rec.json() if r_rec.status_code == 200 else False}
except Exception as e:
    results['rooms_segment'] = False
    results['rooms_recolour'] = False
    details['rooms_segment'] = str(e)

# 4. Palettes Generate & Swap
try:
    r_pal = requests.post(f'{BASE}/palettes/generate', json={'primary_hex': '#B85C38', 'room_type': 'Living Room', 'interior_style': 'Modern'})
    results['palettes_generate'] = (r_pal.status_code == 200)
    pal_list = r_pal.json() if r_pal.status_code == 200 else []
    details['palettes_generate'] = {'status': r_pal.status_code, 'concepts_count': len(pal_list)}

    if pal_list:
        sample_pal = pal_list[0]
        r_swap = requests.post(f'{BASE}/palettes/swap', json={'palette': sample_pal, 'from_role': 'primary_wall', 'to_role': 'secondary_wall'})
        results['palettes_swap'] = (r_swap.status_code == 200)
        details['palettes_swap'] = {'status': r_swap.status_code}
    else:
        results['palettes_swap'] = False
        details['palettes_swap'] = 'No palette to swap'
except Exception as e:
    results['palettes_generate'] = False
    results['palettes_swap'] = False
    details['palettes_generate'] = str(e)

# 5. Daylight Simulate
try:
    r_day = requests.post(f'{BASE}/daylight/simulate', files={'file': ('room.jpg', image_bytes, 'image/jpeg')}, data={'preset': 'noon_5500k'})
    results['daylight'] = (r_day.status_code == 200)
    details['daylight'] = {'status': r_day.status_code, 'kelvin': r_day.json().get('kelvin_target') if r_day.status_code == 200 else r.text}
except Exception as e:
    results['daylight'] = False
    details['daylight'] = str(e)

# 6. Materials Score
try:
    r_mat = requests.post(f'{BASE}/materials/score', json={'primary_hex': '#B85C38', 'materials': ['natural_oak', 'brushed_brass']})
    results['materials'] = (r_mat.status_code == 200)
    details['materials'] = {'status': r_mat.status_code, 'compatibility': r_mat.json().get('overall_score') if r_mat.status_code == 200 else r.text}
except Exception as e:
    results['materials'] = False
    details['materials'] = str(e)

# 7. Estimator
try:
    r_est = requests.post(f'{BASE}/estimator/calculate', json={
        'room_length_meters': 5.0,
        'room_width_meters': 4.0,
        'wall_height_meters': 2.8,
        'num_doors': 1,
        'num_windows': 2,
        'coats': 2,
        'cost_per_liter_inr': 450
    })
    results['estimator'] = (r_est.status_code == 200)
    details['estimator'] = {'status': r_est.status_code, 'liters': r_est.json().get('liters_required') if r_est.status_code == 200 else None}
except Exception as e:
    results['estimator'] = False
    details['estimator'] = str(e)

# 8. Timeline & Rollback
try:
    r_time_post = requests.post(f'{BASE}/timeline', json={
        'project_id': 'proj_matrix_test',
        'label': 'Test Version 1',
        'palette_data': {'selected_tone': '#B85C38'}
    })
    results['timeline_post'] = (r_time_post.status_code == 200)
    v_id = r_time_post.json().get('version_id') if r_time_post.status_code == 200 else None
    
    r_time_get = requests.get(f'{BASE}/timeline?project_id=proj_matrix_test')
    results['timeline_get'] = (r_time_get.status_code == 200)
    
    if v_id:
        r_roll = requests.post(f'{BASE}/timeline/rollback', json={'project_id': 'proj_matrix_test', 'version_id': v_id})
        results['timeline_rollback'] = (r_roll.status_code == 200)
        details['timeline_rollback'] = {'status': r_roll.status_code}
    else:
        results['timeline_rollback'] = False
except Exception as e:
    results['timeline_post'] = False
    results['timeline_get'] = False
    results['timeline_rollback'] = False
    details['timeline_error'] = str(e)

# 9. Memory & DNA
try:
    if pal_list:
        r_fav = requests.post(f'{BASE}/memory/favourite', json={'palette': pal_list[0], 'style': 'Modern'})
        results['memory_favourite'] = (r_fav.status_code == 200)
        r_rej = requests.post(f'{BASE}/memory/reject', json={'palette': pal_list[0]})
        results['memory_reject'] = (r_rej.status_code == 200)
    else:
        results['memory_favourite'] = False
        results['memory_reject'] = False
    
    r_dna = requests.get(f'{BASE}/dna')
    results['dna'] = (r_dna.status_code == 200)
    details['dna'] = {'status': r_dna.status_code, 'signature': r_dna.json().get('signature_name') if r_dna.status_code == 200 else None}
except Exception as e:
    results['dna'] = False
    details['dna_error'] = str(e)

# 10. Auth
try:
    import time
    u_email = f'matrix_user_{int(time.time())}@matrix.com'
    r_reg = requests.post(f'{BASE}/auth/register', json={'email': u_email, 'password': 'MatrixPassword123!', 'full_name': 'Matrix Tester'})
    results['auth_register'] = (r_reg.status_code == 201)
    
    r_login = requests.post(f'{BASE}/auth/login', json={'email': u_email, 'password': 'MatrixPassword123!'})
    results['auth_login'] = (r_login.status_code == 200)
    token = r_login.json().get('token')
    
    r_me = requests.get(f'{BASE}/auth/me', headers={'Authorization': f'Bearer {token}'})
    results['auth_me'] = (r_me.status_code == 200 and r_me.json().get('authenticated') is True)
    
    r_logout = requests.post(f'{BASE}/auth/logout')
    results['auth_logout'] = (r_logout.status_code == 200)
except Exception as e:
    results['auth'] = False
    details['auth_error'] = str(e)

# 11. Billing
try:
    r_pl = requests.get(f'{BASE}/plans')
    results['plans'] = (r_pl.status_code == 200)
    
    r_ord = requests.post(f'{BASE}/billing/order', json={'plan_id': 'pro', 'billing_cycle': 'monthly'})
    results['billing_order'] = (r_ord.status_code == 200)
    ord_id = r_ord.json().get('order_id') if r_ord.status_code == 200 else None
    
    r_ver = requests.post(f'{BASE}/billing/verify', json={
        'razorpay_order_id': ord_id or 'order_mock',
        'razorpay_payment_id': 'pay_mock_123',
        'razorpay_signature': 'valid_sig_sandbox',
        'plan_id': 'pro'
    })
    results['billing_verify'] = (r_ver.status_code == 200)
except Exception as e:
    results['billing'] = False
    details['billing_error'] = str(e)

# 12. Exports
try:
    if pal_list:
        r_exp_j = requests.post(f'{BASE}/export/json', json=pal_list[0])
        results['export_json'] = (r_exp_j.status_code == 200 and 'application/json' in r_exp_j.headers.get('content-type', ''))
        
        r_exp_c = requests.post(f'{BASE}/export/csv', json=pal_list[0])
        results['export_csv'] = (r_exp_c.status_code == 200 and 'text/csv' in r_exp_c.headers.get('content-type', ''))
        
        r_exp_p = requests.post(f'{BASE}/export/pdf', json=pal_list[0])
        results['export_pdf'] = (r_exp_p.status_code == 200 and 'application/pdf' in r_exp_p.headers.get('content-type', ''))
        
        r_exp_png = requests.post(f'{BASE}/export/png', json=pal_list[0])
        results['export_png'] = (r_exp_png.status_code == 200 and 'image/png' in r_exp_png.headers.get('content-type', ''))
except Exception as e:
    results['exports'] = False
    details['export_error'] = str(e)

print(json.dumps({'results': results, 'details': details}, indent=2))
