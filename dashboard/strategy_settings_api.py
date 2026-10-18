"""Shared HTTP routing for Malaysian SNR preferences and existing dashboard reloads."""
import json
from http import HTTPStatus
from urllib.parse import urlparse
from strategy.malaysian_snr.runtime_settings import validate_msnr_patch


PATH = '/api/strategies/malaysian-snr/settings'
SETTING = 'enable_synthetic_daily_storyline_filter'
BODY_SETTING = 'fractal_min_body_ratio'
DISTANCE_SETTING = 'fractal_max_entry_distance_atr'


def handle_strategy_settings_request(handler, service, method):
    path = urlparse(handler.path).path
    if path == '/api/strategies/malaysian-snr/candidates' and method == 'GET':
        try:
            result = {'ok':True,'funnel':service.repository.msnr_candidate_funnel(source='DEMO')}
            status = HTTPStatus.OK
        except Exception:
            result, status = {'ok':False,'error':'Auditoria de candidatos no disponible'}, HTTPStatus.SERVICE_UNAVAILABLE
        handler._send(json.dumps(result,ensure_ascii=False).encode('utf-8'),
                      'application/json; charset=utf-8',status)
        return True
    if path != PATH:
        return False
    if method == 'GET':
        result = service.get_msnr_runtime_settings()
        status = HTTPStatus.OK if result.get('ok') else HTTPStatus.SERVICE_UNAVAILABLE
    else:
        try:
            length = int(handler.headers.get('Content-Length', '0'))
            if not 0 < length <= 16384:
                raise ValueError('Tamaño de solicitud inválido')
            body = json.loads(handler.rfile.read(length).decode('utf-8'))
            body = validate_msnr_patch(body)
            result = service.update_msnr_runtime_settings(body.pop(SETTING, None), **body)
            status = HTTPStatus.OK if result.get('ok') else HTTPStatus.SERVICE_UNAVAILABLE
        except (ValueError, UnicodeDecodeError) as exc:
            result = {'ok': False, 'error': str(exc)}
            status = HTTPStatus.BAD_REQUEST
    handler._send(json.dumps(result, ensure_ascii=False).encode('utf-8'),
                  'application/json; charset=utf-8', status)
    return True


def install_strategy_settings_routes(service):
    """Add just the new endpoint to a running dashboard without replacing its server."""
    server = getattr(service, '_server', None)
    if server is None:
        return
    cls = server.RequestHandlerClass
    if getattr(cls, '_msnr_settings_routes_installed', False):
        return
    original_get, original_post = cls.do_GET, cls.do_POST

    def do_GET(handler):
        if not handle_strategy_settings_request(handler, service, 'GET'):
            return original_get(handler)

    def do_POST(handler):
        if not handle_strategy_settings_request(handler, service, 'POST'):
            return original_post(handler)

    cls.do_GET, cls.do_POST = do_GET, do_POST
    cls._msnr_settings_routes_installed = True
