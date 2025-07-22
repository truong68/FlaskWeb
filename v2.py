from flask import Flask, render_template, request, redirect, url_for, flash
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import zipfile
import os

app = Flask(__name__)
app.secret_key = "your-secret-key"

# Thông tin proxy
proxy_host = "103.163.25.103"
proxy_port = 43782
proxy_user = "WEyRduUf"
proxy_pass = "7tMDv4bU"

# Tạo extension Proxy dùng Manifest V3
def create_proxy_auth_extension():
    manifest_json = """
    {
        "name": "Chrome Proxy",
        "version": "1.0.0",
        "manifest_version": 3,
        "permissions": [
            "proxy",
            "storage",
            "webRequest",
            "webRequestAuthProvider",
            "scripting"
        ],
        "background": {
            "service_worker": "background.js"
        },
        "host_permissions": [
            "<all_urls>"
        ]
    }
    """

    background_js = f"""
    chrome.runtime.onInstalled.addListener(() => {{
        chrome.proxy.settings.set({{
            value: {{
                mode: "fixed_servers",
                rules: {{
                    singleProxy: {{
                        scheme: "http",
                        host: "{proxy_host}",
                        port: {proxy_port}
                    }},
                    bypassList: []
                }}
            }},
            scope: "regular"
        }}, function() {{}});

        chrome.webRequest.onAuthRequired.addListener(
            function(details) {{
                return {{
                    authCredentials: {{
                        username: "{proxy_user}",
                        password: "{proxy_pass}"
                    }}
                }};
            }},
            {{urls: ["<all_urls>"]}},
            ["blocking"]
        );
    }});
    """

    pluginfile = "proxy_auth_plugin.zip"
    with zipfile.ZipFile(pluginfile, "w") as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return pluginfile

# Hàm tìm kiếm từ khóa
def search_keywords(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]

        chrome_options = Options()
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_extension(create_proxy_auth_extension())
        # chrome_options.add_argument("--headless")  # Bỏ để debug

        service = Service(ChromeDriverManager().install())

        for keyword in keywords:
            print(f"Tìm kiếm từ khóa: {keyword}")

            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get("https://www.google.com")
            time.sleep(2)

            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys(keyword)
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)

            found = False
            for _ in range(5):
                cites = driver.find_elements(By.XPATH, "//cite")
                for cite in cites:
                    url = cite.text
                    if "duhocvietphuong.edu.vn" in url:
                        print(f"Đã tìm thấy URL: {url}")
                        cite.find_element(By.XPATH, "..").click()
                        time.sleep(5)

                        print("Bắt đầu cuộn trang trong 120 giây...")
                        start_time = time.time()
                        scroll_direction = "down"
                        while time.time() - start_time < 180:
                            if scroll_direction == "down":
                                driver.execute_script("window.scrollBy(0, 300);")
                                if driver.execute_script("return window.innerHeight + window.scrollY") >= driver.execute_script("return document.body.scrollHeight"):
                                    scroll_direction = "up"
                            else:
                                driver.execute_script("window.scrollBy(0, -300);")
                                if driver.execute_script("return window.scrollY") == 0:
                                    scroll_direction = "down"
                            time.sleep(0.5)

                        print("Đợi thêm 120 giây trước khi thoát...")
                        time.sleep(180)

                        found = True
                        break

                if found:
                    break

                try:
                    next_button = driver.find_element(By.ID, "pnnext")
                    next_button.click()
                    time.sleep(3)
                except Exception:
                    print("Không tìm thấy nút 'Tiếp'.")
                    break

            driver.quit()

        return "Tìm kiếm hoàn tất!"
    except Exception as e:
        return f"Lỗi: {e}"

# Giao diện upload file từ Flask
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            flash("Không tìm thấy tệp!")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("Chưa chọn tệp!")
            return redirect(request.url)

        file_path = os.path.join(os.getcwd(), "keywords.txt")
        file.save(file_path)
        result = search_keywords(file_path)
        flash(result)
        return redirect(request.url)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
