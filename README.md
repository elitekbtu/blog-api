## Verification

Use the following commands to verify the system:

---

### 1. Admin endpoint (nginx → Django)

```bash
curl -I http://localhost/admin/login/
Expected:
HTTP/1.1 200 OK

Server: nginx/...

2. Static files (nginx caching)
curl -I http://localhost/static/admin/css/base.css

Expected:
HTTP/1.1 200 OK
Cache-Control: max-age=... (long cache header)

3. Posts API
curl http://localhost/api/posts/
Expected:
JSON response with list of posts

4. nginx fallback when backend is down

docker compose stop web
curl -I http://localhost/api/posts/

Expected:
502 Bad Gateway (from nginx, NOT connection refused)

5. Direct backend port check
curl -I http://localhost:8000/
Expected:
Connection refused

6. WebSocket connection
wscat -c "ws://localhost/ws/posts/<slug>/comments/?token=<jwt>"

Expected:
101 Switching Protocols
Then:
Send a comment via REST API
Verify message is received in WebSocket client