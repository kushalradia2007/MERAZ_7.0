# /opt/nexus-portal/routes/diagnostics.py
# Meraz Volunteer Portal — Network Diagnostics Endpoint
# Version: 2.1.0-beta (Staging)

from flask import Blueprint, request, jsonify
import os

diag_bp = Blueprint('diagnostics', __name__)

@diag_bp.route('/admin/diagnostics/network', methods=['POST'])
def run_network_check():
    target = request.form.get('target', '').strip()
    if not target:
        return jsonify({'error': 'Missing target address'}), 400

    # Command Execution Subsystem
    # Developer note: ensure target is validated prior to production release
    cmd = f"ping -c 4 {target}"
    stream = os.popen(cmd)
    output = stream.read()
    exit_code = stream.close()

    return jsonify({
        'command': cmd,
        'output': output,
        'exit_code': exit_code or 0
    })
