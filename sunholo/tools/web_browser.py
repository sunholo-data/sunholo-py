import os
import base64
import json
from datetime import datetime
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

class BrowseWebWithImagePromptsBot:
    """
    Examples:

    ```python
    class ProductionBot(BrowseWebWithImagePromptsBot):
        def send_prompt_to_llm(self, prompt, screenshot_base64):
            # Implement the actual logic to send the prompt and screenshot to the LLM and return the response
            api_url = "https://api.example.com/process"  # Replace with the actual LLM API endpoint
            headers = {"Content-Type": "application/json"}
            data = {
                "prompt": prompt,
                "screenshot": screenshot_base64
            }
            response = requests.post(api_url, headers=headers, data=json.dumps(data))
            return response.text  # Assuming the response is in JSON format

    @app.route('/run-bot', methods=['POST'])
    def run_bot():
        data = request.json
        session_id = data.get('session_id')
        website_name = data.get('website_name')
        browser_type = data.get('browser_type', 'chromium')
        current_action_description = data.get('current_action_description', "")
        next_goal = data.get('next_goal', "")
        
        bot = ProductionBot(session_id=session_id, website_name=website_name, browser_type=browser_type, headless=True)
        
        # Check if initial instructions are provided
        initial_instructions = data.get('instructions')
        if initial_instructions:
            bot.execute_instructions(initial_instructions)
        
        # Take initial screenshot and send to LLM if no instructions provided
        if not initial_instructions:
            screenshot_path = bot.take_screenshot()
            new_instructions = bot.send_screenshot_to_llm(screenshot_path, current_action_description, next_goal)
            bot.execute_instructions(new_instructions)
        
        # Take final screenshot
        bot.take_screenshot()
        
        bot.close()
        
        return jsonify({"status": "completed", "new_instructions": new_instructions})

    if __name__ == "__main__":
        app.run(host='0.0.0.0', port=8080)
    ```
    """
    def __init__(self, session_id, website_name, browser_type='chromium', headless=True):
        if not sync_playwright:
            raise ImportError("playright needed for BrowseWebWithImagePromptsBot class - install via `pip install sunholo[tools]`")
        self.session_id = session_id
        self.website_name = website_name
        self.browser_type = browser_type
        self.screenshot_dir = f"{website_name}_{session_id}"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.cookie_file = os.path.join(self.screenshot_dir, "cookies.json")
        self.playwright = sync_playwright().start()
        
        if browser_type == 'chromium':
            self.browser = self.playwright.chromium.launch(headless=headless)
        elif browser_type == 'firefox':
            self.browser = self.playwright.firefox.launch(headless=headless)
        elif browser_type == 'webkit':
            self.browser = self.playwright.webkit.launch(headless=headless)
        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")
        
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.load_cookies()

    def load_cookies(self):
        if os.path.exists(self.cookie_file):
            with open(self.cookie_file, 'r') as f:
                cookies = json.load(f)
                self.context.add_cookies(cookies)

    def save_cookies(self):
        cookies = self.context.cookies()
        with open(self.cookie_file, 'w') as f:
            json.dump(cookies, f)

    def navigate(self, url):
        self.page.goto(url)

    def click(self, selector):
        self.page.click(selector)

    def scroll(self, direction='down', amount=1):
        for _ in range(amount):
            if direction == 'down':
                self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            elif direction == 'up':
                self.page.evaluate("window.scrollBy(0, -window.innerHeight)")
            elif direction == 'left':
                self.page.evaluate("window.scrollBy(-window.innerWidth, 0)")
            elif direction == 'right':
                self.page.evaluate("window.scrollBy(window.innerWidth, 0)")

    def type_text(self, selector, text):
        self.page.fill(selector, text)

    def take_screenshot(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(self.screenshot_dir, f"screenshot_{timestamp}.png")
        self.page.screenshot(path=screenshot_path)
        return screenshot_path

    def get_latest_screenshot_path(self):
        screenshots = sorted(
            [f for f in os.listdir(self.screenshot_dir) if f.startswith('screenshot_')],
            key=lambda x: os.path.getmtime(os.path.join(self.screenshot_dir, x)),
            reverse=True
        )
        if screenshots:
            return os.path.join(self.screenshot_dir, screenshots[0])
        return None

    def create_prompt_vars(self, current_action_description, next_goal):
        prompt = {
            "current_action_description": current_action_description,
            "next_goal": next_goal,
        }
        return prompt

    def send_screenshot_to_llm(self, screenshot_path, current_action_description="", next_goal=""):
        with open(screenshot_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        prompt_vars = self.create_prompt(current_action_description, next_goal)
        response = self.send_prompt_to_llm(prompt_vars, encoded_image)  # Sending prompt and image separately
        return json.loads(response)

    def send_prompt_to_llm(self, prompt_vars, screenshot_base64):
        raise NotImplementedError("This method should be implemented by subclasses: `def send_prompt_to_llm(self, prompt_vars, screenshot_base64)`")

    def close(self):
        self.save_cookies()
        self.browser.close()
        self.playwright.stop()

    def execute_instructions(self, instructions):
        for instruction in instructions:
            action = instruction['action']
            if action == 'navigate':
                self.navigate(instruction['url'])
            elif action == 'click':
                self.click(instruction['selector'])
            elif action == 'scroll':
                self.scroll(instruction.get('direction', 'down'), instruction.get('amount', 1))
            elif action == 'type':
                self.type_text(instruction['selector'], instruction['text'])
            screenshot_path = self.take_screenshot()
            new_instructions = self.send_screenshot_to_llm(screenshot_path, instruction.get('description', ''), instruction.get('next_goal', ''))
            if new_instructions:
                self.execute_instructions(new_instructions)

