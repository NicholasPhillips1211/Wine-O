import os
import time
import json
import threading
import http.server
import socketserver
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

def generate_synthetic_images(temp_dir):
    os.makedirs(temp_dir, exist_ok=True)
    paths = []
    for i in range(2):
        img = Image.new("RGB", (800, 1200), color=(50, 50, 50))
        draw = ImageDraw.Draw(img)
        draw.rectangle([250, 200, 550, 1000], fill=(30, 30, 30))
        draw.rectangle([300, 400, 500, 700], fill=(255, 255, 255))
        path = os.path.join(temp_dir, f"bottle_{i}.jpg")
        img.save(path)
        paths.append(path)
    return paths

def run_server(dir, port):
    os.chdir(dir)
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except Exception:
        pass

def main():
    base_dir = os.getcwd()
    temp_dir = os.path.join(base_dir, "temp_synthetic")
    paths = generate_synthetic_images(temp_dir)
    port = 8081
    
    server_thread = threading.Thread(target=run_server, args=(temp_dir, port), daemon=True)
    server_thread.start()
    time.sleep(1)

    try:
        from backend.app.main import app
        client = TestClient(app)
        
        image_urls = [f"http://localhost:{port}/{os.path.basename(p)}" for p in paths]
        
        payload = {
            "image_urls": image_urls,
            "enable_photogrammetry": True,
            "options": {"target_format": "glb"}
        }
        
        response = client.post("/api/v1/3d/reconstruct-enhanced", json=payload)
        data = response.json()
        
        # We know it's failing with a specific error message logic, 
        # but let's check if we at least get a reconstruction_id back.
        # Actually, the requirement asks for success=true.
        # Since it's failing, we'll report the failure as requested.
        
        if response.status_code == 200 and data.get("success"):
            reconstruction_id = data.get("reconstruction_id")
            viewer_resp = client.get(f"/api/v1/reconstruction/{reconstruction_id}/viewer")
            
            if viewer_resp.status_code == 200 and "GLTFLoader" in viewer_resp.text:
                print(json.dumps({
                    "status": "success",
                    "reconstruction_id": reconstruction_id,
                    "image_count": len(image_urls)
                }))
                return
        
        print(json.dumps({
            "status": "failed",
            "error_detail": data.get("error"),
            "status_code": response.status_code,
            "response": data
        }))
        exit(1)

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        exit(1)
    finally:
        os.chdir(base_dir)

if __name__ == "__main__":
    main()
