# Spotify AIO - Account Creator with Live Screen Viewer
from flask import Blueprint, render_template, request, jsonify
import threading
import json
import os
import random
import string
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from PIL import Image
import io
import base64

spotify_bp = Blueprint('spotify', __name__, url_prefix='/spotify')

# Global state
spotify_accounts = []
account_file = os.path.expanduser('~/spotify_accounts.txt')
spotify_job_status = {}
spotify_lock = threading.Lock()
spotify_bot_drivers = {}  # Store driver refs for live video capture
spotify_bots_status = {}  # Real-time bot status
captcha_submissions = {}  # Track which bots have user-submitted CAPTCHAs

def load_accounts():
    """Load saved accounts from file"""
    global spotify_accounts
    if os.path.exists(account_file):
        try:
            with open(account_file, 'r') as f:
                spotify_accounts = [line.strip() for line in f.readlines() if line.strip()]
        except:
            spotify_accounts = []

def save_accounts():
    """Save accounts to file"""
    with open(account_file, 'w') as f:
        for account in spotify_accounts:
            f.write(account + '\n')

def generate_email():
    """Generate random email"""
    return f"spotify_{random.randint(100000, 999999)}@tempmail.com"

def generate_password():
    """Generate secure password"""
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choice(chars) for _ in range(12))

def generate_username():
    """Generate random username"""
    return f"user_{random.randint(100000, 999999)}"

def random_birthday():
    """Generate random birthday"""
    day = str(random.randint(1, 28))
    month = str(random.randint(1, 12)).zfill(2)
    year = str(random.randint(1990, 2005))
    return day, month, year

def random_gender():
    """Generate random gender - male or female"""
    return random.choice(["male", "female"])

def click_span_button_with_text(driver, wait, text):
    """Helper to click button containing text in span - multiple strategies"""
    strategies = [
        # Strategy 1: Button with span containing text
        (By.XPATH, f"//button//span[contains(text(), '{text}')]/..", "span wrapper"),
        # Strategy 2: Direct button with text
        (By.XPATH, f"//button[contains(normalize-space(), '{text}')]", "direct button"),
        # Strategy 3: Case-insensitive span
        (By.XPATH, f"//button//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]/..", "case-insensitive"),
        # Strategy 4: Any button with partial text match
        (By.XPATH, f"//button[contains(., '{text}')]", "partial match"),
    ]
    
    for locator, by_type, strategy_name in strategies:
        try:
            button = wait.until(EC.presence_of_element_located((by_type, locator)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(0.1)
            
            # Try clickability wait
            try:
                button = wait.until(EC.element_to_be_clickable((by_type, locator)))
            except:
                pass
            
            # Normal click
            try:
                button.click()
                time.sleep(0.2)
                return True
            except:
                # JavaScript click as fallback
                driver.execute_script("arguments[0].click();", button)
                time.sleep(0.2)
                return True
        except Exception as e:
            continue
    
    return False

def get_proxy_for_bot(bot_id):
    """Get proxy from list for a specific bot (rotation)"""
    proxies_env = os.getenv('PROXIES_LIST', '')
    if not proxies_env or proxies_env.strip() == '':
        return None
    
    proxies = [p.strip() for p in proxies_env.split('\n') if p.strip()]
    if not proxies:
        return None
    
    # Rotate proxy based on bot_id
    proxy = proxies[bot_id % len(proxies)]
    print(f"[PROXY] Using proxy {bot_id % len(proxies) + 1}/{len(proxies)}: {proxy[:30]}...")
    return proxy

def launch_spotify_browser(bot_id=None):
    """Launch headless Chrome for Spotify with optional proxy"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # Add proxy if configured
    if bot_id is not None:
        proxy = get_proxy_for_bot(bot_id)
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
    
    return webdriver.Chrome(options=options)

def capture_screenshot(driver, crop_to_captcha=False):
    """Capture screenshot from driver - optionally crops to CAPTCHA area"""
    try:
        screenshot = driver.get_screenshot_as_png()
        img = Image.open(io.BytesIO(screenshot))
        
        # Try to find and crop CAPTCHA area using JavaScript if requested
        if crop_to_captcha:
            try:
                captcha_bounds = driver.execute_script("""
                    // Find reCAPTCHA/hCAPTCHA iframe
                    var iframes = document.querySelectorAll('iframe[src*="recaptcha"], iframe[src*="hcaptcha"]');
                    if (iframes.length > 0) {
                        var rect = iframes[0].getBoundingClientRect();
                        // For expanded CAPTCHA, look for the challenge container
                        var parent = iframes[0].parentElement;
                        while (parent && parent.offsetHeight < 500) {
                            parent = parent.parentElement;
                        }
                        if (parent && parent.offsetHeight >= 200) {
                            rect = parent.getBoundingClientRect();
                        }
                        return {x: Math.max(0, rect.left - 50), y: Math.max(0, rect.top - 50), 
                                w: Math.min(1920, rect.width + 100), h: Math.min(1080, rect.height + 100)};
                    }
                    return null;
                """)
                
                if captcha_bounds and captcha_bounds['w'] > 150 and captcha_bounds['h'] > 150:
                    # Crop to CAPTCHA area with generous padding
                    x1 = int(captcha_bounds['x'])
                    y1 = int(captcha_bounds['y'])
                    x2 = int(min(1920, captcha_bounds['x'] + captcha_bounds['w']))
                    y2 = int(min(1080, captcha_bounds['y'] + captcha_bounds['h']))
                    img = img.crop((x1, y1, x2, y2))
            except:
                pass
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except:
        return None

def attempt_auto_solve_captcha(driver, bot_id=None):
    """Try to automatically solve CAPTCHA with multiple strategies - returns True if solved"""
    try:
        tag = f"[BOT {bot_id}]" if bot_id else "[AUTO-SOLVE]"
        
        # Strategy 1: Click I'm not a robot checkbox
        print(f"{tag} 🤖 Attempting auto-solve (Strategy 1: Checkbox click)")
        checkbox_strategies = [
            (By.CSS_SELECTOR, "div.g-recaptcha input[type='checkbox']"),
            (By.CSS_SELECTOR, "div.rc-checkbox-border"),
            (By.XPATH, "//div[@class='g-recaptcha']//input[@type='checkbox']"),
            (By.CSS_SELECTOR, "label > input[type='checkbox'][aria-label*='robot']"),
        ]
        
        for locator_type, locator in checkbox_strategies:
            try:
                checkbox = driver.find_element(locator_type, locator)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", checkbox)
                print(f"{tag} ✓ Clicked checkbox - waiting for auto-solve")
                time.sleep(2)
                
                # Check if challenge page appears (challenge = needs manual solve)
                try:
                    challenge_iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='api2/bframe']")
                    if not challenge_iframes:
                        print(f"{tag} ✓ CAPTCHA verified without challenge!")
                        return True
                except:
                    pass
                
                time.sleep(3)
                
                # Check if CAPTCHA is gone
                iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha'], iframe[src*='hcaptcha']")
                if not iframes:
                    print(f"{tag} ✓ CAPTCHA auto-solved!")
                    return True
            except Exception as e:
                continue
        
        # Strategy 2: Try clicking into iframe context
        print(f"{tag} 🤖 Attempting Strategy 2: Iframe navigation")
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    src = iframe.get_attribute("src").lower()
                    if "recaptcha" in src or "hcaptcha" in src:
                        driver.switch_to.frame(iframe)
                        try:
                            # Try to find and click checkbox in frame
                            checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                            checkbox.click()
                            print(f"{tag} ✓ Clicked checkbox in iframe")
                            driver.switch_to.default_content()
                            time.sleep(4)
                            
                            # Check if solved
                            iframes_check = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha'], iframe[src*='hcaptcha']")
                            if not iframes_check:
                                print(f"{tag} ✓ CAPTCHA auto-solved via iframe!")
                                return True
                        except:
                            driver.switch_to.default_content()
                except:
                    try:
                        driver.switch_to.default_content()
                    except:
                        pass
        except Exception as e:
            try:
                driver.switch_to.default_content()
            except:
                pass
        
        # Strategy 3: Wait for natural verification (browser fingerprint)
        print(f"{tag} 🤖 Attempting Strategy 3: Waiting for background verification")
        for attempt in range(3):
            time.sleep(3)
            iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha'], iframe[src*='hcaptcha']")
            if not iframes:
                print(f"{tag} ✓ CAPTCHA passed on attempt {attempt + 1}!")
                return True
        
        print(f"{tag} ✗ Auto-solve failed - manual solve needed")
        return False
        
    except Exception as e:
        print(f"{tag} ✗ Auto-solve error: {str(e)[:50]}")
        return False

@spotify_bp.route('/')
def spotify_dashboard():
    """Spotify AIO Dashboard"""
    return render_template('spotify_dashboard.html')

@spotify_bp.route('/api/create-accounts', methods=['POST'])
def create_accounts():
    """Create multiple Spotify accounts"""
    data = request.json
    count = int(data.get('count', 5))
    
    job_id = f"spotify_{datetime.now().timestamp()}"
    
    with spotify_lock:
        spotify_job_status[job_id] = {
            'total': count,
            'created': 0,
            'status': 'running',
            'current_account': '',
            'current_bot_id': None,
            'accounts': []
        }
    
    def create_worker():
        for bot_id in range(count):
            driver = None
            try:
                # Initialize bot status
                if bot_id not in spotify_bots_status:
                    spotify_bots_status[bot_id] = {}
                
                spotify_bots_status[bot_id] = "🔄 Launching browser..."
                driver = launch_spotify_browser(bot_id)
                spotify_bot_drivers[bot_id] = driver
                wait = WebDriverWait(driver, 15)
                
                email = generate_email()
                password = generate_password()
                username = generate_username()
                day, month, year = random_birthday()
                gender = random_gender()
                
                # Navigate to signup
                spotify_bots_status[bot_id] = "📍 Loading Spotify..."
                driver.get("https://www.spotify.com/signup")
                time.sleep(3)
                
                # Accept cookies
                spotify_bots_status[bot_id] = "🍪 Accepting cookies..."
                try:
                    cookie_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='accept-cookies']")))
                    cookie_btn.click()
                except:
                    pass
                time.sleep(0.8)
                
                # Email
                spotify_bots_status[bot_id] = f"✉️  Email: {email[:15]}..."
                email_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
                email_field.send_keys(email)
                time.sleep(0.5)
                
                spotify_bots_status[bot_id] = "👆 Clicking Next..."
                if not click_span_button_with_text(driver, wait, "Next"):
                    email_field.send_keys(Keys.ENTER)
                time.sleep(2)
                
                # Password
                spotify_bots_status[bot_id] = "🔐 Password..."
                password_field = wait.until(EC.presence_of_element_located((By.NAME, "new-password")))
                password_field.send_keys(password)
                time.sleep(0.5)
                
                spotify_bots_status[bot_id] = "👆 Next..."
                if not click_span_button_with_text(driver, wait, "Next"):
                    password_field.send_keys(Keys.ENTER)
                time.sleep(2)
                
                # Display name
                spotify_bots_status[bot_id] = "👤 Display name..."
                name_field = wait.until(EC.presence_of_element_located((By.ID, "displayName")))
                name_field.send_keys(username)
                time.sleep(0.5)
                
                spotify_bots_status[bot_id] = "👆 Next..."
                if not click_span_button_with_text(driver, wait, "Next"):
                    name_field.send_keys(Keys.ENTER)
                time.sleep(2)
                
                # Birthday
                spotify_bots_status[bot_id] = "📅 Birthday..."
                try:
                    # Try day field
                    day_field = wait.until(EC.presence_of_element_located((By.ID, "day")))
                    day_field.clear()
                    day_field.send_keys(day)
                    
                    # Try month - multiple selectors
                    try:
                        month_select = Select(driver.find_element(By.ID, "month"))
                        month_select.select_by_value(month)
                    except:
                        try:
                            month_select = Select(driver.find_element(By.NAME, "month"))
                            month_select.select_by_value(month)
                        except:
                            # Try by visible text
                            month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                            month_idx = int(month) - 1
                            month_select = Select(driver.find_element(By.ID, "month"))
                            month_select.select_by_visible_text(month_names[month_idx])
                    
                    # Try year field
                    year_field = driver.find_element(By.ID, "year")
                    year_field.clear()
                    year_field.send_keys(year)
                    
                    time.sleep(2)
                    if not click_span_button_with_text(driver, wait, "Next"):
                        year_field.send_keys(Keys.ENTER)
                    time.sleep(5)
                except Exception as e:
                    print(f"[BOT {bot_id}] ⚠️ Birthday issue: {str(e)[:50]}")
                    try:
                        click_span_button_with_text(driver, wait, "Next")
                        time.sleep(3)
                    except:
                        pass
                
                # Gender
                spotify_bots_status[bot_id] = "⚙️  Gender..."
                try:
                    # Try finding all radio inputs and click by value
                    gender_element = None
                    
                    # Strategy 1: Find radio with value matching gender
                    gender_short = "m" if gender == "male" else "f"
                    try:
                        radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                        for radio in radios:
                            radio_val = radio.get_attribute("value")
                            if radio_val == gender_short or radio_val == gender or gender.lower() in (radio_val or "").lower():
                                gender_element = radio
                                break
                    except:
                        pass
                    
                    # Strategy 2: Try gender labels with short form
                    if not gender_element:
                        try:
                            gender_element = driver.find_element(By.CSS_SELECTOR, f"label[for='gender_option_{gender_short}']")
                        except:
                            pass
                    
                    # Strategy 3: Try full gender name in labels
                    if not gender_element:
                        try:
                            gender_element = driver.find_element(By.CSS_SELECTOR, f"label[for*='{gender}']")
                        except:
                            pass
                    
                    # Strategy 4: Search all labels for male/female text
                    if not gender_element:
                        try:
                            labels = driver.find_elements(By.TAG_NAME, "label")
                            for label in labels:
                                label_html = label.get_attribute("outerHTML").lower()
                                if gender.lower() in label_html:
                                    gender_element = label
                                    break
                        except:
                            pass
                    
                    if gender_element:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", gender_element)
                        time.sleep(0.5)
                        try:
                            gender_element.click()
                        except:
                            driver.execute_script("arguments[0].click();", gender_element)
                    
                    time.sleep(1.5)
                    # Try clicking Next button first (like username/password)
                    if not click_span_button_with_text(driver, wait, "Next"):
                        # If Next button click fails, try pressing Enter on the gender element
                        try:
                            if gender_element:
                                gender_element.send_keys(Keys.ENTER)
                        except:
                            pass
                    time.sleep(3)
                except Exception as e:
                    print(f"[BOT {bot_id}] ⚠️ Gender issue: {str(e)[:50]}")
                    try:
                        click_span_button_with_text(driver, wait, "Next")
                        time.sleep(3)
                    except:
                        pass
                
                # Accept terms
                try:
                    terms_checkbox = driver.find_element(By.CSS_SELECTOR, "input[name='terms']")
                    if not terms_checkbox.is_selected():
                        terms_checkbox.click()
                    time.sleep(1)
                except:
                    pass
                
                # Final submit - Sign up button
                spotify_bots_status[bot_id] = "📤 Creating account..."
                try:
                    # Find Sign up button and make sure it's visible
                    signup_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Sign up')]/..")))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", signup_button)
                    time.sleep(1)
                    signup_button.click()
                except:
                    # Fallback to helper function
                    click_span_button_with_text(driver, wait, "Sign up")
                time.sleep(8)
                
                # Enhanced CAPTCHA detection
                captcha_detected = False
                captcha_type = None
                
                # Check for reCAPTCHA iframe
                try:
                    recaptcha_frames = driver.find_elements(By.TAG_NAME, "iframe")
                    for frame in recaptcha_frames:
                        try:
                            src = frame.get_attribute("src").lower()
                            if "recaptcha" in src or "challenge" in src:
                                captcha_detected = True
                                captcha_type = "reCAPTCHA"
                                print(f"[BOT {bot_id}] 🔐 reCAPTCHA iframe detected")
                                time.sleep(2)
                                
                                # Try to click the reCAPTCHA checkbox
                                try:
                                    driver.switch_to.frame(frame)
                                    recaptcha_checkbox = driver.find_element(By.CLASS_NAME, "recaptcha-checkbox-border")
                                    recaptcha_checkbox.click()
                                    print(f"[BOT {bot_id}] ✓ Clicked reCAPTCHA checkbox")
                                    time.sleep(3)
                                    driver.switch_to.default_content()
                                except Exception as rc_err:
                                    driver.switch_to.default_content()
                                    print(f"[BOT {bot_id}] Failed to click checkbox: {str(rc_err)[:30]}")
                                break
                        except:
                            pass
                except:
                    pass
                
                # Check for generic CAPTCHA input field
                if not captcha_detected:
                    try:
                        driver.find_element(By.CSS_SELECTOR, "input[name='captcha']")
                        captcha_detected = True
                        captcha_type = "Generic"
                        print(f"[BOT {bot_id}] 🔐 Generic CAPTCHA field detected")
                    except:
                        pass
                
                # Try to click "Continue" button
                try:
                    continue_btn = driver.find_element(By.XPATH, "//span[contains(text(), 'Continue')]/..")
                    continue_btn.click()
                    print(f"[BOT {bot_id}] ✓ Clicked Continue button")
                    time.sleep(3)
                except:
                    pass
                
                if captcha_detected:
                    spotify_bots_status[bot_id] = f"🤖 Attempting auto-solve..."
                    print(f"[BOT {bot_id}] 🔐 {captcha_type or 'CAPTCHA'} detected! Attempting auto-solve...")
                    
                    # Try automatic solution first
                    auto_solved = attempt_auto_solve_captcha(driver, bot_id)
                    
                    if auto_solved:
                        spotify_bots_status[bot_id] = "✓ CAPTCHA auto-solved!"
                        print(f"[BOT {bot_id}] ✓ Auto-solve successful!")
                        time.sleep(3)
                        # Continue with account creation
                        account = {'email': email, 'password': password, 'username': username, 'created': datetime.now().isoformat()}
                        spotify_accounts.append(json.dumps(account))
                        save_accounts()
                        spotify_bots_status[bot_id] = f"✓ Success: {email[:15]}..."
                        
                        with spotify_lock:
                            spotify_job_status[job_id]['accounts'].append(account)
                    else:
                        # Fall back to manual solving
                        spotify_bots_status[bot_id] = f"⏸️ {captcha_type or 'CAPTCHA'} - Waiting for manual solve"
                        print(f"[BOT {bot_id}] 🔐 Auto-solve failed. Waiting for user to solve manually...")
                        
                        # Clear previous submission flag
                        captcha_submissions[bot_id] = False
                        
                        # Mark bot as waiting for CAPTCHA solution
                        with spotify_lock:
                            if job_id not in spotify_job_status:
                                spotify_job_status[job_id] = {'status': 'captcha', 'bot_id': bot_id}
                            else:
                                spotify_job_status[job_id]['waiting_captcha_bot'] = bot_id
                        
                        # Wait for CAPTCHA to be solved - wait for USER SUBMISSION (max 5 minutes)
                        captcha_solved = False
                        wait_time = 0
                        while wait_time < 300:  # 5 minutes timeout
                            time.sleep(1)
                            wait_time += 1
                            
                            # Check if user submitted the CAPTCHA via API
                            if captcha_submissions.get(bot_id, False):
                                print(f"[BOT {bot_id}] ✓ User submitted CAPTCHA solution!")
                                captcha_solved = True
                                break
                        
                        if captcha_solved:
                            spotify_bots_status[bot_id] = "✓ CAPTCHA solved! Verifying account..."
                            time.sleep(2)
                            account = {'email': email, 'password': password, 'username': username, 'created': datetime.now().isoformat()}
                            spotify_accounts.append(json.dumps(account))
                            save_accounts()
                            spotify_bots_status[bot_id] = f"✓ Success: {email[:15]}..."
                            
                            with spotify_lock:
                                spotify_job_status[job_id]['accounts'].append(account)
                            
                            # Clean up
                            if bot_id in captcha_submissions:
                                del captcha_submissions[bot_id]
                        else:
                            spotify_bots_status[bot_id] = "✗ CAPTCHA timeout (5 minutes exceeded)"
                            print(f"[BOT {bot_id}] ✗ CAPTCHA not solved within 5 minutes")
                            if bot_id in captcha_submissions:
                                del captcha_submissions[bot_id]
                else:
                    # No CAPTCHA - success!
                    account = {'email': email, 'password': password, 'username': username, 'created': datetime.now().isoformat()}
                    spotify_accounts.append(json.dumps(account))
                    save_accounts()
                    spotify_bots_status[bot_id] = f"✓ Success: {email[:15]}..."
                    
                    with spotify_lock:
                        spotify_job_status[job_id]['accounts'].append(account)
                
                with spotify_lock:
                    spotify_job_status[job_id]['created'] += 1
                    spotify_job_status[job_id]['current_account'] = email
                    spotify_job_status[job_id]['current_bot_id'] = bot_id
                
            except Exception as e:
                err_msg = str(e)[:35]
                spotify_bots_status[bot_id] = f"✗ {err_msg}"
                with spotify_lock:
                    if job_id in spotify_job_status:
                        spotify_job_status[job_id]['created'] += 1
            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                if bot_id in spotify_bot_drivers:
                    del spotify_bot_drivers[bot_id]
        
        with spotify_lock:
            if job_id in spotify_job_status:
                spotify_job_status[job_id]['status'] = 'complete'
    
    thread = threading.Thread(target=create_worker, daemon=True)
    thread.start()
    
    return jsonify({'job_id': job_id, 'message': 'Account creation started'})

@spotify_bp.route('/api/captcha-solved', methods=['POST'])
def captcha_solved():
    """Notify that CAPTCHA was manually solved by user"""
    data = request.json or {}
    bot_id = data.get('bot_id')
    
    if not bot_id:
        return jsonify({'error': 'No bot_id provided'}), 400
    
    # Mark this bot's CAPTCHA as submitted by user
    captcha_submissions[bot_id] = True
    print(f"[API] ✓ CAPTCHA submitted for Bot #{bot_id} - Waiting 1.5s before continue")
    
    return jsonify({'success': True, 'message': f'CAPTCHA submitted for Bot #{bot_id}'})

@spotify_bp.route('/api/captcha-press-continue', methods=['POST'])
def captcha_press_continue():
    """Auto-press continue button after manual CAPTCHA solve"""
    try:
        data = request.json or {}
        bot_id = int(data.get('bot_id', -1))
        
        if bot_id < 0 or bot_id not in spotify_bot_drivers:
            return jsonify({'success': False, 'error': 'Bot not found'}), 404
        
        driver = spotify_bot_drivers[bot_id]
        
        try:
            # Find and click the continue/submit button
            continue_strategies = [
                (By.XPATH, "//button[contains(text(), 'Continue')]", "text=Continue"),
                (By.XPATH, "//button[contains(text(), 'Next')]", "text=Next"),
                (By.XPATH, "//button[@type='submit']", "type=submit"),
                (By.XPATH, "//span[contains(text(), 'Continue')]/..", "span=Continue"),
                (By.CLASS_NAME, "submit-button", "class=submit"),
            ]
            
            for locator, xpath, desc in continue_strategies:
                try:
                    if locator == By.XPATH:
                        button = driver.find_element(locator, xpath)
                    else:
                        button = driver.find_element(locator, xpath)
                    
                    driver.execute_script("arguments[0].click();", button)
                    print(f"[API] ✓ Pressed continue button ({desc}) for Bot #{bot_id}")
                    return jsonify({'success': True, 'message': f'Continue button pressed for Bot #{bot_id}'})
                except:
                    pass
            
            print(f"[API] Could not find continue button for Bot #{bot_id}")
            return jsonify({'success': False, 'error': 'Continue button not found'})
        except Exception as e:
            print(f"[API] Error pressing continue: {str(e)[:50]}")
            return jsonify({'success': False, 'error': str(e)[:30]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)[:50]})

@spotify_bp.route('/api/captcha-click', methods=['POST'])
def captcha_click():
    """Handle CAPTCHA click from user"""
    try:
        data = request.get_json() or {}
        bot_id = int(data.get('bot_id', -1))
        x = int(data.get('x', 0))
        y = int(data.get('y', 0))
        
        if bot_id < 0:
            return jsonify({'success': False, 'error': 'No bot_id provided'}), 400
        
        if bot_id not in spotify_bot_drivers:
            return jsonify({'success': False, 'error': f'Bot {bot_id} not found'}), 404
        
        driver = spotify_bot_drivers[bot_id]
        
        try:
            # Click using JavaScript - dispatch actual mouse events
            driver.execute_script(f"""
                var element = document.elementFromPoint({x}, {y});
                if (element) {{
                    // Dispatch mouse events for better CAPTCHA detection
                    var mouseEvent = new MouseEvent('mousedown', {{
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        clientX: {x},
                        clientY: {y}
                    }});
                    element.dispatchEvent(mouseEvent);
                    
                    var clickEvent = new MouseEvent('click', {{
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        clientX: {x},
                        clientY: {y}
                    }});
                    element.dispatchEvent(clickEvent);
                    
                    var mouseUpEvent = new MouseEvent('mouseup', {{
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        clientX: {x},
                        clientY: {y}
                    }});
                    element.dispatchEvent(mouseUpEvent);
                }} else {{
                    console.log('No element at coordinates');
                }}
            """)
            print(f"[API] ✓ Clicked at ({x}, {y}) for Bot #{bot_id}")
            
            time.sleep(0.2)
            return jsonify({'success': True, 'clicked': True, 'message': f'CAPTCHA clicked'})
        except Exception as e:
            print(f"[API] Click failed: {str(e)[:50]}")
            return jsonify({'success': False, 'error': f'Click failed: {str(e)[:30]}'})
    except Exception as e:
        print(f"[API] Error in captcha_click: {str(e)}")
        return jsonify({'success': False, 'error': str(e)[:50]})

@spotify_bp.route('/api/account-progress', methods=['GET'])
def account_progress():
    """Get account creation progress"""
    job_id = request.args.get('job_id')
    
    with spotify_lock:
        if job_id not in spotify_job_status:
            return jsonify({'error': 'Job not found'}), 404
        
        job = spotify_job_status[job_id]
        progress = int((job['created'] / job['total']) * 100) if job['total'] > 0 else 0
        
        return jsonify({
            'job_id': job_id,
            'total': job['total'],
            'created': job['created'],
            'status': job['status'],
            'progress': progress,
            'current_account': job['current_account'],
            'current_bot_id': job['current_bot_id'],
            'accounts': job['accounts']
        })

@spotify_bp.route('/api/accounts', methods=['GET'])
def get_accounts():
    """Get all created accounts"""
    load_accounts()
    accounts = []
    for account_str in spotify_accounts:
        try:
            accounts.append(json.loads(account_str))
        except:
            pass
    return jsonify({'accounts': accounts, 'total': len(accounts)})

@spotify_bp.route('/api/bot-screenshot/<int:bot_id>', methods=['GET'])
def get_bot_screenshot(bot_id):
    """Get live bot screenshot - full screen"""
    try:
        if bot_id in spotify_bot_drivers:
            driver = spotify_bot_drivers[bot_id]
            screenshot = capture_screenshot(driver, crop_to_captcha=False)
            status = spotify_bots_status.get(bot_id, "Processing...")
            return jsonify({'screenshot': screenshot, 'status': status})
        else:
            status = spotify_bots_status.get(bot_id, "Inactive")
            return jsonify({'screenshot': None, 'status': status})
    except:
        return jsonify({'screenshot': None, 'status': 'Error'}), 500

@spotify_bp.route('/api/captcha-screenshot/<int:bot_id>', methods=['GET'])
def get_captcha_screenshot(bot_id):
    """Get cropped CAPTCHA screenshot only"""
    try:
        if bot_id in spotify_bot_drivers:
            driver = spotify_bot_drivers[bot_id]
            screenshot = capture_screenshot(driver, crop_to_captcha=True)
            status = spotify_bots_status.get(bot_id, "Processing...")
            return jsonify({'screenshot': screenshot, 'status': status})
        else:
            status = spotify_bots_status.get(bot_id, "Inactive")
            return jsonify({'screenshot': None, 'status': status})
    except:
        return jsonify({'screenshot': None, 'status': 'Error'}), 500

@spotify_bp.route('/api/bot-status', methods=['GET'])
def bot_status():
    """Get all active bots status"""
    return jsonify(spotify_bots_status)

@spotify_bp.route('/api/download-accounts', methods=['GET'])
def download_accounts():
    """Download accounts as text file"""
    content = '\n'.join(spotify_accounts)
    return jsonify({'content': content})

@spotify_bp.route('/api/clear-accounts', methods=['POST'])
def clear_accounts():
    """Clear all accounts"""
    global spotify_accounts
    spotify_accounts = []
    if os.path.exists(account_file):
        os.remove(account_file)
    return jsonify({'message': 'All accounts cleared'})
