# api/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import time
import random
import os

app = Flask(__name__)
CORS(app)

# Para evitar logging extensivo no Vercel
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class BlazeAPIProxy:
    def __init__(self):
        self.base_url = "https://www.bestblaze.com.br"
        self.token = "H0k7r6rTS6Nl12OhDkf8ABaTHwm6ZUiyEZEnkDCC"  # Token estático do site
        self.session = requests.Session()
        self.setup_session()
        
    def setup_session(self):
        """Configura sessão com headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRF-TOKEN': self.token,
        })
    
    def get_double(self, ini=1):
        """Obtém dados do Double"""
        try:
            data = {'ini': ini, '_token': self.token}
            
            response = self.session.post(
                f'{self.base_url}/jogadasDouble',
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    # Tenta extrair manualmente
                    text = response.text.strip()
                    if text.startswith('{') or text.startswith('['):
                        import json
                        return json.loads(text)
                    return {"data": text[:200]}
            else:
                return {
                    "error": f"HTTP {response.status_code}",
                    "response": response.text[:200] if response.text else ""
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    def get_crash(self, ini=1):
        """Obtém dados do Crash"""
        try:
            data = {'ini': ini, '_token': self.token}
            
            response = self.session.post(
                f'{self.base_url}/jogadasCrash',
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    text = response.text.strip()
                    if text.startswith('{') or text.startswith('['):
                        import json
                        return json.loads(text)
                    return {"data": text[:200]}
            else:
                return {
                    "error": f"HTTP {response.status_code}",
                    "response": response.text[:200] if response.text else ""
                }
                
        except Exception as e:
            return {"error": str(e)}

# Instância global
proxy = BlazeAPIProxy()

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Blaze API Proxy</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { background: #4CAF50; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }
        </style>
    </head>
    <body>
        <h1>🔮 Blaze API Proxy</h1>
        <p>Proxy para acessar dados do Blaze Double e Crash</p>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/api/double?ini=1</code><br>
            <span class="method">POST</span> <code>/api/double</code> (body: {"ini": 1})
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/api/crash?ini=1</code><br>
            <span class="method">POST</span> <code>/api/crash</code> (body: {"ini": 1})
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/api/status</code> - Status do serviço
        </div>
        
        <h3>Testar agora:</h3>
        <button onclick="testAPI()">Testar Double</button>
        <button onclick="testCrash()">Testar Crash</button>
        
        <pre id="result" style="background: #eee; padding: 10px; margin-top: 20px;"></pre>
        
        <script>
            async function testAPI() {
                const response = await fetch('/api/double?ini=1');
                const data = await response.json();
                document.getElementById('result').textContent = JSON.stringify(data, null, 2);
            }
            
            async function testCrash() {
                const response = await fetch('/api/crash?ini=1');
                const data = await response.json();
                document.getElementById('result').textContent = JSON.stringify(data, null, 2);
            }
        </script>
    </body>
    </html>
    '''

@app.route('/api/double', methods=['GET', 'POST'])
def double():
    """Endpoint para Double"""
    try:
        if request.method == 'POST':
            if request.is_json:
                ini = request.json.get('ini', 1)
            else:
                ini = request.form.get('ini', 1, type=int)
        else:
            ini = request.args.get('ini', 1, type=int)
        
        result = proxy.get_double(ini)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/crash', methods=['GET', 'POST'])
def crash():
    """Endpoint para Crash"""
    try:
        if request.method == 'POST':
            if request.is_json:
                ini = request.json.get('ini', 1)
            else:
                ini = request.form.get('ini', 1, type=int)
        else:
            ini = request.args.get('ini', 1, type=int)
        
        result = proxy.get_crash(ini)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def status():
    """Status da API"""
    return jsonify({
        "status": "online",
        "service": "Blaze API Proxy",
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "endpoints": [
            "/api/double",
            "/api/crash",
            "/api/status"
        ]
    })

@app.route('/api/health', methods=['GET'])
def health():
    """Health check para Vercel"""
    return jsonify({"status": "healthy"}), 200

# Handler para Vercel
def handler(request):
    from flask import make_response
    with app.app_context():
        response = app.full_dispatch_request()
        return make_response((response.get_data(), response.status_code, response.headers))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # Para execução no Vercel
    application = app        self.cookies = None
        
    def get_csrf_token(self, force_refresh=False):
        """
        Obtém um token CSRF válido da página inicial
        """
        # Cache por 10 minutos
        current_time = time.time()
        if not force_refresh and self.csrf_token and (current_time - self.last_token_time) < 600:
            return self.csrf_token
            
        try:
            print("Obtendo novo token CSRF...")
            
            # Primeiro acessa a página principal
            response = self.session.get(
                self.base_url,
                timeout=15,
                allow_redirects=True
            )
            
            if response.status_code != 200:
                print(f"Erro ao acessar página: {response.status_code}")
                return self.get_fallback_token()
            
            # Verifica se tem cookies de sessão
            if 'laravel_session' in self.session.cookies:
                print("Sessão Laravel encontrada")
            
            # Procura o token em várias localizações possíveis
            token = self.extract_token_from_response(response.text)
            
            if token:
                self.csrf_token = token
                self.last_token_time = current_time
                self.cookies = self.session.cookies.get_dict()
                print(f"Token obtido com sucesso: {token[:30]}...")
                return token
            else:
                print("Token não encontrado, usando fallback")
                return self.get_fallback_token()
                
        except Exception as e:
            print(f"Erro ao obter token: {e}")
            return self.get_fallback_token()
    
    def extract_token_from_response(self, html_content):
        """
        Extrai token CSRF do HTML usando múltiplas estratégias
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Estratégia 1: Meta tag CSRF
        meta_token = soup.find('meta', {'name': 'csrf-token'})
        if meta_token and meta_token.get('content'):
            print("Token encontrado em meta tag")
            return meta_token.get('content')
        
        # Estratégia 2: Input hidden
        input_token = soup.find('input', {'name': '_token'})
        if input_token and input_token.get('value'):
            print("Token encontrado em input hidden")
            return input_token.get('value')
        
        # Estratégia 3: Procura em JavaScript
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Padrões comuns de Laravel
                patterns = [
                    r'window\.Laravel\s*=\s*{[^}]*csrfToken["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'csrf-token["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'_token["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'"X-CSRF-TOKEN"\s*:\s*"([^"]+)"',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, script.string)
                    if match:
                        print(f"Token encontrado em JS com padrão: {pattern[:30]}...")
                        return match.group(1)
        
        # Estratégia 4: Procura em qualquer lugar no HTML
        token_pattern = r'([a-f0-9]{40})'  # Tokens geralmente são hash de 40 caracteres
        matches = re.findall(token_pattern, html_content)
        if matches:
            print(f"Token encontrado por regex no HTML: {matches[0][:20]}...")
            return matches[0]
        
        return None
    
    def get_fallback_token(self):
        """Token de fallback do código original"""
        fallback = "H0k7r6rTS6Nl12OhDkf8ABaTHwm6ZUiyEZEnkDCC"
        print(f"Usando token fallback: {fallback[:20]}...")
        return fallback
    
    def get_double_data(self, ini=1):
        """
        Obtém dados do Double
        """
        try:
            token = self.get_csrf_token()
            
            # Configura headers específicos para API
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': self.base_url,
                'Referer': f'{self.base_url}/',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-TOKEN': token,
            }
            
            # Dados da requisição
            data = {
                'ini': ini,
                '_token': token
            }
            
            # Usa a sessão com cookies
            response = self.session.post(
                f'{self.base_url}/jogadasDouble',
                data=data,
                headers=headers,
                timeout=15,
                allow_redirects=False
            )
            
            print(f"Status Double: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    # Tenta extrair JSON mesmo com problemas
                    text = response.text.strip()
                    if text.startswith('{') or text.startswith('['):
                        return json.loads(text)
                    else:
                        return {"error": "Resposta não é JSON válido", "data": text[:200]}
            else:
                return {
                    "error": f"Erro HTTP {response.status_code}",
                    "status": response.status_code,
                    "text": response.text[:500] if response.text else ""
                }
                
        except Exception as e:
            print(f"Erro em get_double_data: {e}")
            return {"error": str(e)}
    
    def get_crash_data(self, ini=1):
        """
        Obtém dados do Crash
        """
        try:
            token = self.get_csrf_token()
            
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': self.base_url,
                'Referer': f'{self.base_url}/',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-TOKEN': token,
            }
            
            data = {
                'ini': ini,
                '_token': token
            }
            
            response = self.session.post(
                f'{self.base_url}/jogadasCrash',
                data=data,
                headers=headers,
                timeout=15
            )
            
            print(f"Status Crash: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    text = response.text.strip()
                    if text.startswith('{') or text.startswith('['):
                        return json.loads(text)
                    else:
                        return {"error": "Resposta não é JSON válido", "data": text[:200]}
            else:
                return {
                    "error": f"Erro HTTP {response.status_code}",
                    "status": response.status_code,
                    "text": response.text[:500] if response.text else ""
                }
                
        except Exception as e:
            print(f"Erro em get_crash_data: {e}")
            return {"error": str(e)}

# Instância global do scraper
scraper = BestBlazeScraper()

@app.route('/jogadasDouble', methods=['POST', 'GET', 'OPTIONS'])
def proxy_double():
    """
    Endpoint para dados do Double
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Obtém parâmetro ini
        if request.method == 'POST':
            if request.is_json:
                ini = request.json.get('ini', 1)
            else:
                ini = request.form.get('ini', 1, type=int)
        else:  # GET
            ini = request.args.get('ini', 1, type=int)
        
        # Obtém dados
        result = scraper.get_double_data(ini)
        
        # Se der erro 419, tenta renovar token
        if isinstance(result, dict) and result.get('status') == 419:
            print("Erro 419 detectado, renovando token...")
            scraper.get_csrf_token(force_refresh=True)
            result = scraper.get_double_data(ini)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "error": "Erro interno",
            "message": str(e),
            "exception": True
        }), 500

@app.route('/jogadasCrash', methods=['POST', 'GET', 'OPTIONS'])
def proxy_crash():
    """
    Endpoint para dados do Crash
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        if request.method == 'POST':
            if request.is_json:
                ini = request.json.get('ini', 1)
            else:
                ini = request.form.get('ini', 1, type=int)
        else:
            ini = request.args.get('ini', 1, type=int)
        
        result = scraper.get_crash_data(ini)
        
        if isinstance(result, dict) and result.get('status') == 419:
            print("Erro 419 no Crash, renovando token...")
            scraper.get_csrf_token(force_refresh=True)
            result = scraper.get_crash_data(ini)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "error": "Erro interno",
            "message": str(e)
        }), 500

@app.route('/status', methods=['GET'])
def status():
    """Verifica status do scraper"""
    return jsonify({
        "status": "online",
        "token_obtido": scraper.csrf_token is not None,
        "token_preview": scraper.csrf_token[:30] + "..." if scraper.csrf_token else None,
        "ultimo_token": time.strftime('%H:%M:%S', time.localtime(scraper.last_token_time)),
        "tem_cookies": bool(scraper.cookies)
    })

@app.route('/refresh', methods=['GET'])
def refresh_token():
    """Força atualização do token"""
    token = scraper.get_csrf_token(force_refresh=True)
    return jsonify({
        "success": True,
        "token": token[:50] + "..." if token and len(token) > 50 else token,
        "time": time.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/test', methods=['GET'])
def test_connection():
    """Testa conexão com o site"""
    try:
        response = scraper.session.get(scraper.base_url, timeout=10)
        return jsonify({
            "status": response.status_code,
            "headers": dict(response.headers),
            "cookies": dict(scraper.session.cookies),
            "redirects": len(response.history) if hasattr(response, 'history') else 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return """
    <h1>🚀 API BestBlaze Proxy Avançado</h1>
    <p>Esta API faz scraping do site BestBlaze com gerenciamento de sessão Laravel.</p>
    
    <h3>Endpoints:</h3>
    <ul>
        <li><b>GET/POST /jogadasDouble?ini=1</b> - Dados do Double</li>
        <li><b>GET/POST /jogadasCrash?ini=1</b> - Dados do Crash</li>
        <li><b>GET /status</b> - Status do sistema</li>
        <li><b>GET /refresh</b> - Atualizar token manualmente</li>
        <li><b>GET /test</b> - Testar conexão</li>
    </ul>
    
    <h3>Uso com JavaScript:</h3>
    <pre>
    // Exemplo com fetch
    fetch('/jogadasDouble', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ini: 1})
    })
    .then(r => r.json())
    .then(console.log)
    </pre>
    """

if __name__ == '__main__':
    # Pré-aquecimento: obtém token inicial
    print("Iniciando BestBlaze Scraper...")
    scraper.get_csrf_token()
    app.run(debug=True, port=5000, host='0.0.0.0')
