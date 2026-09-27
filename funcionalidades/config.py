USER_AGENTS = [
    # Windows - Chrome / Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.184 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/121.0.2277.128 Safari/537.36",
    # macOS - Safari / Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.184 Safari/537.36",
    # Linux - Chrome / Firefox
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.224 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Android - Chrome
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
    # iPhone - Safari / Chrome
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.71 Mobile/15E148 Safari/604.1",
    # iPad
    "Mozilla/5.0 (iPad; CPU OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.7 Mobile/15E148 Safari/604.1",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Edge moderno
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36 Edg/122.0.2365.66",
]

DEFAULT_USER_AGENT = "webCrawler/Tool"

ACCEPT_PADRAO = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
ACCEPT_LANGUAGE_PADRAO = "en-US,en;q=0.9"
ACCEPT_ENCODING_PADRAO = "gzip, deflate"

PROXIES_TOR = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050",
}

# Heurísticas de bloqueio / captcha
CAPTCHA_KEYWORDS = [
    "captcha",
    "recaptcha",
    "g-recaptcha",
    "hcaptcha",
    "i am not a robot",
    "verify you are human",
]

PROTECTION_KEYWORDS = [
    "checking your browser",
    "attention required",
    "cf-browser-verification",
    "ray id",
    "just a moment...",
]

BLOCK_KEYWORDS = [
    "access denied",
    "forbidden",
    "too many requests",
    "rate limit",
    "unusual traffic",
    "automated queries",
]

STATUS_CODES_BLOQUEIO = (401, 403, 429)

# Extensões que não valem a pena seguir/coletar como página
EXTENSOES_INUTEIS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico", ".bmp", ".tiff", ".heic",
    ".mp4", ".mkv", ".mov", ".avi", ".webm", ".mp3", ".wav", ".ogg", ".flac",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".rar", ".7z", ".tar", ".gz", ".iso",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".exe", ".bin", ".apk", ".dmg", ".msi", ".dll", ".css", ".xml",
)

# Regexs de detecção de segredos/tokens
SECRET_PATTERNS = {
    "token_json": r'"token"\s*:\s*"[^"]+"',
    "access_token": r'"access_token"\s*:\s*"[^"]+"',
    "twitter_token": r'\b[1-9][0-9]+-[0-9a-zA-Z]{40}\b',
    "facebook_token": r'\bEAA[0-9A-Za-z]{20,}\b',
    "google_api": r'AIza[0-9A-Za-z\-_]{35}',
    "jwt_token": r'\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b',
    "github_token": r'\bghp_[a-zA-Z0-9]{36}\b',
    "github_oauth": r'\bgho_[a-zA-Z0-9]{36}\b',
    "github_server_access_token": r'\bghu_[a-zA-Z0-9]{36}\b',
    "stripe_key_standard": r'\bsk_live_[0-9a-zA-Z]{24}\b',
    "stripe_key_private": r'\brk_live_[0-9a-zA-Z]{99}\b',
    "openai_api_key": r'\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b',
    "aws_access_key": r'\bAKIA[0-9A-Z]{16}\b',
    "slack_token": r'\bxox[baprs]-[0-9A-Za-z-]{10,}\b',
}

# Regexs de identificação de chamadas de rede em código JS
class codigo_regexs:
    ajax = r"\$\.ajax\(\{.*?\}\s*\)"
    ajax_get_post = r"\$\.(?:get|post)\(.*?\)"
    fetch = r"fetch\s*\(.*?\)"
    axios = r"axios\.\w+\(.*?\)"
    web_socket = r"new\s*WebSocket\(.*?\)"
    xml_http_request = r"\.open\(['\"`](?:GET|POST|PUT|DELETE|PATCH)['\"`]\s*,.*?\)"
    http_request = r"this\.\w+\.\w+\(.*?\)"

    pattern = [ajax, fetch, http_request, ajax_get_post, axios, web_socket, xml_http_request]

    padroes_requisicao = {
        "fetch": fetch,
        "axios": axios,
        "jQuery.ajax": ajax,
        "jQuery.get/post": ajax_get_post,
        "WebSocket": web_socket,
        "XMLHttpRequest": xml_http_request,
        "this.*() genérico": http_request,
    }

    variaveis = r"\b[\w$]+\s*=\s*['\"`]?[^;,\n]{1,120}"

    palavras_chaves_vetores = r"\b(admin|role|Cookies\.set|Cookies\.get|Cookies\.remove|userRole)\b"
    palavras_chaves_baixo = r"\b(userId)\b"


# Regexs para extrair valores de strings literais em código JS.
STRING_LITERAL_PATTERNS = [
    r'"(?:[^"\\\n]|\\.)*"',
    r"'(?:[^'\\\n]|\\.)*'",
    r'`(?:[^`\\]|\\.)*`',
]

# Fontes de "entrada do usuário" em código JS — usado pelo 'js reverse entradas'.
ENTRADAS_USUARIO = {
    "URL / location": [
        r"location\.href\b",
        r"location\.search\b",
        r"location\.hash\b",
        r"location\.pathname\b",
        r"location\.hostname\b",
        r"document\.URL\b",
        r"document\.documentURI\b",
        r"document\.baseURI\b",
        r"window\.name\b",
    ],
    "Parâmetros de query": [
        r"URLSearchParams\s*\([^)]*\)",
        r"\.searchParams\.get\([^)]*\)",
        r"useSearchParams\s*\(\s*\)",
        r"\$route\.query\b",
        r"\$route\.params\b",
        r"useParams\s*\(\s*\)",
    ],
    "LocalStorage / SessionStorage": [
        r"localStorage\.getItem\([^)]*\)",
        r"sessionStorage\.getItem\([^)]*\)",
        r"localStorage\[[^\]]*\]",
        r"sessionStorage\[[^\]]*\]",
    ],
    "Cookies": [
        r"document\.cookie\b",
        r"Cookies\.get\([^)]*\)",
        r"\$\.cookie\([^)]*\)",
    ],
    "Campos de formulário / DOM": [
        r"document\.getElementById\([^)]*\)\.value",
        r"document\.querySelector\([^)]*\)\.value",
        r"document\.getElementsBy(?:Name|ClassName|TagName)\([^)]*\)(?:\[\d+\])?\.value",
        r"\$\([^)]*\)\.val\(\)",
        r"event\.target\.value",
        r"e\.target\.value",
        r"this\.value\b",
        r"new FormData\([^)]*\)",
    ],
    "Upload de arquivos": [
        r"new FileReader\(\s*\)",
        r"\.files\[\d+\]",
        r"\.files\.length\b",
    ],
    "Prompts diretos": [
        r"window\.prompt\([^)]*\)",
        r"\bprompt\([^)]*\)",
        r"window\.confirm\([^)]*\)",
    ],
    "postMessage (cross-frame)": [
        r"addEventListener\(\s*['\"]message['\"][^)]*\)",
        r"\.onmessage\s*=",
    ],
    "Cabeçalhos HTTP": [
        r"getResponseHeader\([^)]*\)",
        r"getAllResponseHeaders\(\s*\)",
        r"headers\.get\([^)]*\)",
        r"request\.headers\[[^\]]*\]",
    ],
    "Referrer": [
        r"document\.referrer\b",
    ],
    "History API": [
        r"history\.state\b",
        r"history\.pushState\([^)]*\)",
        r"history\.replaceState\([^)]*\)",
    ],
    "Clipboard": [
        r"navigator\.clipboard\.readText\(\s*\)",
    ],
    "Eventos de interação do usuário": [
        r"addEventListener\(\s*['\"](?:input|change|keyup|keydown|paste|drop|submit)['\"][^)]*\)",
    ],
}

SINKS_PERIGOSOS = {
    "Execução de código": [
        r"\beval\s*\([^)]*\)",
        r"new\s+Function\s*\([^)]*\)",
        r"setTimeout\s*\(\s*['\"`][^)]*\)",
        r"setInterval\s*\(\s*['\"`][^)]*\)",
        r"\bexecScript\s*\([^)]*\)",
    ],
    "Injeção de HTML/DOM": [
        r"\.innerHTML\s*=\s*[^;]{1,200}",
        r"\.outerHTML\s*=\s*[^;]{1,200}",
        r"document\.write\s*\([^)]*\)",
        r"document\.writeln\s*\([^)]*\)",
        r"\.insertAdjacentHTML\s*\([^)]*\)",
        r"dangerouslySetInnerHTML\s*=\s*\{[^}]*\}",
        r"\$\([^)]*\)\.html\s*\([^)]*\)",
        r"\$\([^)]*\)\.append\s*\([^)]*\)",
        r"\$\([^)]*\)\.prepend\s*\([^)]*\)",
        r"\$\([^)]*\)\.after\s*\([^)]*\)",
        r"\$\([^)]*\)\.before\s*\([^)]*\)",
        r"\$\([^)]*\)\.replaceWith\s*\([^)]*\)",
    ],
    "Redirecionamento / navegação": [
        r"\b(?:window\.)?location\s*=\s*[^;]{1,200}",
        r"location\.href\s*=\s*[^;]{1,200}",
        r"location\.assign\s*\([^)]*\)",
        r"location\.replace\s*\([^)]*\)",
        r"window\.open\s*\([^)]*\)",
    ],
    "Atributos perigosos de elemento": [
        r"\.setAttribute\s*\(\s*['\"`](?:href|src|action|formaction)['\"`]\s*,[^)]*\)",
        r"\.src\s*=\s*[^;]{1,200}",
        r"\.action\s*=\s*[^;]{1,200}",
    ],
    "Escrita de cookies": [
        r"document\.cookie\s*=\s*[^;]{1,200}",
    ],
    "Possível prototype pollution": [
        r"__proto__",
        r"\bObject\.assign\s*\([^)]*\)",
        r"\.constructor\.prototype\b",
        r"\bmerge\s*\([^)]*\)",
        r"\bextend\s*\([^)]*\)",
    ],
    "postMessage (envio)": [
        r"\.postMessage\s*\([^)]*\)",
    ],
}