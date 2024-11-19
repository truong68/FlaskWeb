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
app.secret_key = "your-secret-key"  # Dùng để hiển thị thông báo (flash)

# Cấu hình proxy
proxy_host = "160.22.173.91"
proxy_port = 39546
proxy_user = "best6395"
proxy_pass = "xedaba89n03"

# Tạo tệp extension proxy
def create_proxy_auth_extension():
    proxy_auth_extension = f"""
        var config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "http",
                    host: "{proxy_host}",
                    port: parseInt({proxy_port})
                }},
                bypassList: []
            }}
        }};
        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{proxy_user}",
                    password: "{proxy_pass}"
                }}
            }};
        }}
        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {{urls: ["<all_urls>"]}},
            ['blocking']
        );
    """

    proxy_auth_plugin_path = "proxy_auth_plugin.zip"
    with zipfile.ZipFile(proxy_auth_plugin_path, "w") as zp:
        zp.writestr("manifest.json", """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version": "22.0.0"
        }
        """)
        zp.writestr("background.js", proxy_auth_extension)
    return proxy_auth_plugin_path

# Selenium logic
def search_keywords(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]

        # Cấu hình Selenium
        chrome_options = Options()
        chrome_options.add_argument(f'--proxy-server=http://{proxy_host}:{proxy_port}')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_extension(create_proxy_auth_extension())
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        for keyword in keywords:
            print(f"Tìm kiếm từ khóa: {keyword}")
            driver.get("https://www.google.com")
            time.sleep(2)
            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys(keyword)
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)

            # Lặp qua các trang kết quả
            found = False
            for _ in range(5):  # Giới hạn 5 trang tìm kiếm
                cites = driver.find_elements(By.XPATH, "//cite")
                for cite in cites:
                    url = cite.text
                    if "duhocvietphuong.edu.vn" in url:
                        print(f"Đã tìm thấy URL: {url}")
                        found = True
                        break
                if found:
                    break

            time.sleep(2)

        driver.quit()
        return "Tìm kiếm hoàn tất!"
    except Exception as e:
        return f"Lỗi: {e}"

# Routes
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

        if file:
            file_path = os.path.join(os.getcwd(), "keywords.txt")
            file.save(file_path)
            result = search_keywords(file_path)
            flash(result)
            return redirect(request.url)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
